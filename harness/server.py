"""The web application: a JSON API, a live event stream and one static page.

    uvicorn harness.server:app --host 0.0.0.0 --port 8000

Environment:
    ANTHROPIC_API_KEY        the key the agent sessions use (required when deployed)
    HARNESS_PASSWORD         visitors must enter it before anything that spends tokens
    HARNESS_ALLOW_OPEN=1     allow those actions with no password (local development only)
    HARNESS_RUNS_DIR         where run folders are kept (mount a volume here)
    HARNESS_MODEL            model for every session (default claude-opus-5-5)
    HARNESS_MAX_BUDGET_USD   spend ceiling per agent session (default 25)
"""
from __future__ import annotations

import asyncio
import hmac
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

from . import core, pipeline

PASSWORD = os.environ.get("HARNESS_PASSWORD", "")
ALLOW_OPEN = os.environ.get("HARNESS_ALLOW_OPEN") == "1"
STATIC = Path(__file__).parent / "static"
MAX_VIEW_BYTES = 400_000
MAX_CSV_LINES = 201

# One stage at a time across the whole server: the spend ceiling is per session,
# and this keeps a public URL from running several pipelines in parallel.
active: dict = {"task": None, "run": None, "stage": None}


@asynccontextmanager
async def lifespan(_: FastAPI):
    core.load_runs()
    yield
    if active["task"]:
        active["task"].cancel()


app = FastAPI(title="Procurement Audit Planner", lifespan=lifespan)


def authorise(password: str | None) -> None:
    if PASSWORD:
        if not hmac.compare_digest((password or "").encode(), PASSWORD.encode()):
            raise HTTPException(401, "Wrong or missing password.")
    elif not ALLOW_OPEN:
        raise HTTPException(403, "Running is disabled: the server has no HARNESS_PASSWORD set.")


def get_run(run_id: str) -> core.Run:
    run = core.RUNS.get(run_id)
    if not run:
        raise HTTPException(404, "No such run.")
    return run


def describe(run: core.Run) -> dict:
    stages = []
    for meta in pipeline.STAGES:
        entry = run.state["stages"][meta["id"]]
        stages.append({**meta, **entry, "files": run.files(meta["id"]),
                       "blocked_by": pipeline.can_run(run, meta["id"])})
    return {"id": run.id, "readonly": run.readonly, "created": run.state.get("created"),
            "start_at": run.state.get("start_at"), "stages": stages,
            "running": active["stage"] if active["run"] == run.id else None,
            "server_busy": bool(active["task"]),
            "cost_usd": round(sum(s["cost_usd"] for s in stages), 2)}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/config")
def config() -> dict:
    return {"auth": "password" if PASSWORD else ("open" if ALLOW_OPEN else "disabled"),
            "model": core.MODEL, "max_budget_usd": core.MAX_BUDGET_USD,
            "decisions": pipeline.DECISIONS, "signoff_decisions": pipeline.SIGNOFF_DECISIONS}


@app.get("/api/runs")
def list_runs() -> list[dict]:
    runs = sorted(core.RUNS.values(), key=lambda r: r.state.get("created") or 0, reverse=True)
    return [{"id": r.id, "readonly": r.readonly, "created": r.state.get("created"),
             "start_at": r.state.get("start_at")} for r in runs]


@app.post("/api/runs")
def new_run(body: dict = Body(...), x_harness_password: str | None = Header(None)) -> dict:
    authorise(x_harness_password)
    try:
        return describe(core.create_run(body.get("start_at", "")))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/runs/{run_id}")
def show_run(run_id: str) -> dict:
    return describe(get_run(run_id))


@app.get("/api/runs/{run_id}/decisions")
def decisions(run_id: str) -> dict:
    return pipeline.read_decisions(get_run(run_id))


@app.post("/api/runs/{run_id}/stages/{stage}")
async def start_stage(run_id: str, stage: str, body: dict = Body(default={}),
                      x_harness_password: str | None = Header(None)) -> dict:
    authorise(x_harness_password)
    run = get_run(run_id)
    if stage not in core.STAGE_IDS:
        raise HTTPException(404, "No such stage.")
    if active["task"]:
        raise HTTPException(409, f"Stage '{active['stage']}' of run {active['run']} is running. "
                                 "One stage runs at a time.")
    reason = pipeline.can_run(run, stage)
    if reason:
        raise HTTPException(409, reason)

    async def job() -> None:
        try:
            await pipeline.run_stage(run, stage, body)
        finally:
            active.update(task=None, run=None, stage=None)

    active.update(task=asyncio.create_task(job()), run=run.id, stage=stage)
    return {"started": stage}


@app.post("/api/runs/{run_id}/stop")
async def stop(run_id: str, x_harness_password: str | None = Header(None)) -> dict:
    authorise(x_harness_password)
    if active["run"] != run_id or not active["task"]:
        raise HTTPException(409, "Nothing is running in this run.")
    active["task"].cancel()
    return {"stopping": active["stage"]}


@app.get("/api/runs/{run_id}/events")
async def events(run_id: str, since: int = Query(0, ge=0)) -> StreamingResponse:
    run = get_run(run_id)

    async def stream():
        sent = since
        while True:
            while sent < len(run.events):
                yield f"data: {json.dumps(run.events[sent])}\n\n"
                sent += 1
            try:
                async with run.changed:
                    await asyncio.wait_for(run.changed.wait(), timeout=15)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/runs/{run_id}/file")
def view_file(run_id: str, path: str) -> PlainTextResponse:
    """Serve one file from the run's outputs/ folder, shortened if it is large."""
    run = get_run(run_id)
    root = run.outputs.resolve()
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(404, "No such output file.")
    if target.suffix == ".csv":
        with target.open(errors="replace") as f:
            lines = [line for _, line in zip(range(MAX_CSV_LINES + 1), f)]
        truncated = len(lines) > MAX_CSV_LINES
        text = "".join(lines[:MAX_CSV_LINES])
    else:
        raw = target.read_bytes()
        truncated = len(raw) > MAX_VIEW_BYTES
        text = raw[:MAX_VIEW_BYTES].decode(errors="replace")
    return PlainTextResponse(text, headers={"X-Truncated": "1" if truncated else "0"})
