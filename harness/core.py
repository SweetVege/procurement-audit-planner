"""Run workspaces, the event log, and the Agent SDK session runner.

A *run* is a private copy of the project (brief, skills, agents, scripts, data)
in its own folder. Every agent session of that run is started with that folder
as its working directory, so the files under outputs/ stay the interface
between stages exactly as they are in Claude Code.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

REPO = Path(__file__).resolve().parent.parent
RUNS_DIR = Path(os.environ.get("HARNESS_RUNS_DIR", REPO / "runs"))
MODEL = os.environ.get("HARNESS_MODEL", "claude-opus-5-5")
MAX_BUDGET_USD = float(os.environ.get("HARNESS_MAX_BUDGET_USD", "25"))
MAX_TURNS = int(os.environ.get("HARNESS_MAX_TURNS", "250"))
MAX_RUNS = int(os.environ.get("HARNESS_MAX_RUNS", "30"))
API_RETRIES = 3
API_RETRY_SECONDS = 90

REFERENCE = "reference"
STAGE_IDS = ("rules", "evidence", "register", "gate1", "team", "signoff")

# The files each stage writes under outputs/ (a trailing slash marks a folder).
STAGE_FILES: dict[str, tuple[str, ...]] = {
    "rules": ("rules.json",),
    "evidence": ("analytics.json", "history.json", "analytics-full/"),
    "register": ("risk-register.md", "auditor-comments.md", "risk-ratings.json",
                 "risk-register.state.json"),
    "gate1": (),
    "team": ("planning-memo.md", "risk-control-matrix.md", "audit-program.md",
             "challenges.md", "review.md", "audit-plan.json", "pack-figures.json",
             "samples/"),
    "signoff": (),
}
# What each stage shows in the browser once it is done.
STAGE_VIEWS: dict[str, tuple[str, ...]] = {
    **STAGE_FILES,
    "gate1": ("risk-register.md", "auditor-comments.md"),
    "signoff": ("review.md",),
}

BASE_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Skill"]


# --------------------------------------------------------------------- runs

class Run:
    def __init__(self, run_id: str, directory: Path, state: dict, readonly: bool = False):
        self.id = run_id
        self.dir = directory
        self.state = state
        self.readonly = readonly
        self.events: list[dict] = []
        self.changed = asyncio.Condition()
        if not readonly:
            log = self.dir / "events.jsonl"
            if log.exists():
                self.events = [json.loads(line) for line in log.read_text().splitlines() if line]

    @property
    def outputs(self) -> Path:
        return self.dir / "outputs"

    def save(self) -> None:
        if not self.readonly:
            (self.dir / "run.json").write_text(json.dumps(self.state, indent=2))

    def emit(self, stage: str, agent: str, kind: str, text: str, **extra: Any) -> None:
        """Append one line to the activity log and wake the browser streams."""
        event = {"n": len(self.events), "t": time.time(), "stage": stage, "agent": agent,
                 "kind": kind, "text": text, **extra}
        self.events.append(event)
        if not self.readonly:
            with (self.dir / "events.jsonl").open("a") as f:
                f.write(json.dumps(event) + "\n")
        asyncio.get_running_loop().create_task(self._notify())

    async def _notify(self) -> None:
        async with self.changed:
            self.changed.notify_all()

    def set_stage(self, stage: str, status: str, **extra: Any) -> None:
        entry = self.state["stages"][stage]
        entry.update(status=status, **extra)
        if status == "running":
            entry.update(started=time.time(), ended=None, note="", cost_usd=0.0)
        elif status in ("done", "failed"):
            entry["ended"] = time.time()
        self.save()
        self.emit(stage, "harness", "status", status, note=entry.get("note", ""))

    def add_cost(self, stage: str, usd: float | None) -> None:
        if usd:
            entry = self.state["stages"][stage]
            entry["cost_usd"] = round(entry.get("cost_usd", 0.0) + usd, 4)
            self.save()

    def reset_from(self, stage: str, *, blank_first: bool = False) -> None:
        """Before a stage re-runs, remove what it and every later stage wrote."""
        for sid in STAGE_IDS[STAGE_IDS.index(stage):]:
            for name in STAGE_FILES[sid]:
                path = self.outputs / name.rstrip("/")
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.exists():
                    path.unlink()
            if sid != stage or blank_first:
                self.state["stages"][sid] = _blank_stage()
        self.save()

    def files(self, stage: str) -> list[str]:
        found: list[str] = []
        for name in STAGE_VIEWS[stage]:
            path = self.outputs / name.rstrip("/")
            if path.is_dir():
                found += sorted(f"{path.name}/{p.name}" for p in path.iterdir() if p.is_file())
            elif path.exists():
                found.append(name)
        return found

    async def python(self, *args: str) -> tuple[int, str]:
        """Run one of the project's own scripts in this run's folder."""
        proc = await asyncio.to_thread(
            subprocess.run, [sys.executable, *args], cwd=self.dir, capture_output=True,
            text=True, timeout=600)
        return proc.returncode, (proc.stdout + proc.stderr).strip()


def _blank_stage() -> dict:
    return {"status": "pending", "started": None, "ended": None, "cost_usd": 0.0, "note": ""}


RUNS: dict[str, Run] = {}


def load_runs() -> None:
    reference_state = {
        "id": REFERENCE, "created": None, "start_at": None,
        "stages": {sid: {**_blank_stage(), "status": "done"} for sid in STAGE_IDS},
    }
    RUNS[REFERENCE] = Run(REFERENCE, REPO, reference_state, readonly=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    for folder in sorted(RUNS_DIR.iterdir()):
        state_file = folder / "run.json"
        if not state_file.exists():
            continue
        run = Run(folder.name, folder, json.loads(state_file.read_text()))
        for entry in run.state["stages"].values():
            if entry["status"] == "running":  # the server stopped mid-stage
                entry.update(status="failed", note="Interrupted: the server restarted.")
        run.save()
        RUNS[run.id] = run


def _copy(src: str, dst: str) -> None:
    """Copy one file by reading and writing its bytes, then check the size.

    The platform fast-copy that shutil uses was seen to leave empty files when
    the source folder is cloud-synced, and an agent given an empty PDF reports
    a blocked run; a plain copy that is checked cannot do that silently.
    """
    data = Path(src).read_bytes()
    Path(dst).write_bytes(data)
    if Path(dst).stat().st_size != len(data) or (len(data) == 0 and Path(src).stat().st_size):
        raise OSError(f"copy of {src} is incomplete")


def create_run(start_at: str) -> Run:
    """Copy the project into a new run folder.

    start_at names the first stage this run will execute. The outputs of every
    earlier stage are copied from the reference run, so a visitor can try a
    human gate or the agent team without first paying for the whole pipeline.
    """
    if start_at not in ("rules", "evidence", "register", "team"):
        raise ValueError(f"cannot start a run at {start_at!r}")
    if len(RUNS) - 1 >= MAX_RUNS:
        raise ValueError(f"run limit reached ({MAX_RUNS}); delete old runs on the server")
    run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    folder = RUNS_DIR / run_id
    ignore = shutil.ignore_patterns("__pycache__", ".DS_Store", "settings*.json", "launch.json")
    for name in (".claude", "data", "scripts"):
        shutil.copytree(REPO / name, folder / name, ignore=ignore, copy_function=_copy)
    _copy(REPO / "CLAUDE.md", folder / "CLAUDE.md")
    (folder / "outputs").mkdir()
    # The agents' instructions call `.venv/bin/python`; point it at this interpreter.
    (folder / ".venv").symlink_to(Path(sys.prefix), target_is_directory=True)

    state = {"id": run_id, "created": time.time(), "start_at": start_at,
             "stages": {sid: _blank_stage() for sid in STAGE_IDS}}
    for sid in STAGE_IDS[:STAGE_IDS.index(start_at)]:
        for name in STAGE_FILES[sid]:
            src = REPO / "outputs" / name.rstrip("/")
            dst = folder / "outputs" / src.name
            shutil.copytree(src, dst, copy_function=_copy) if src.is_dir() else _copy(src, dst)
        state["stages"][sid].update(status="done", note="Copied from the reference run.")
    run = Run(run_id, folder, state)
    run.save()
    RUNS[run_id] = run
    return run


# ------------------------------------------------------------------- agents

def load_agent(run: Run, name: str) -> dict:
    """Read .claude/agents/<name>.md: frontmatter fields plus the prompt body."""
    text = (run.dir / ".claude" / "agents" / f"{name}.md").read_text()
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        raise ValueError(f"agent file for {name} has no frontmatter")
    meta = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    prompt = match.group(2).strip()
    memory = run.dir / ".claude" / "agent-memory" / name / "MEMORY.md"
    if meta.get("memory") and memory.exists():
        prompt += ("\n\n## Your memory notes from earlier runs "
                   f"(`{memory.relative_to(run.dir)}`)\n\n{memory.read_text().strip()}")
    return {
        "name": name,
        "prompt": prompt,
        "tools": [t.strip() for t in meta.get("tools", "").split(",") if t.strip()],
        "skills": [s.strip() for s in meta.get("skills", "").split(",") if s.strip()],
    }


def agent_options(run: Run, agent: dict | None, *, extra_prompt: str = "",
                  mcp_servers: dict | None = None, mcp_tools: list[str] | None = None,
                  ) -> ClaudeAgentOptions:
    """One Agent SDK session, confined to the run folder.

    setting_sources=["project"] is what loads CLAUDE.md and .claude/skills from
    the run folder. dontAsk denies any tool that is not listed, so nothing ever
    waits for a permission prompt that no one is there to answer.
    """
    append = "\n\n".join(p for p in ((agent or {}).get("prompt", ""), extra_prompt) if p)
    system_prompt: dict = {"type": "preset", "preset": "claude_code"}
    if append:
        system_prompt["append"] = append
    return ClaudeAgentOptions(
        cwd=str(run.dir),
        setting_sources=["project"],
        model=MODEL,
        system_prompt=system_prompt,
        tools=BASE_TOOLS,
        allowed_tools=BASE_TOOLS + (mcp_tools or []),
        permission_mode="dontAsk",
        mcp_servers=mcp_servers or {},
        strict_mcp_config=True,  # only the servers passed here, never the host's own
        max_turns=MAX_TURNS,
        max_budget_usd=MAX_BUDGET_USD,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
    )


def kickoff(agent: dict, task: str) -> str:
    """The first user message for an agent: load its skills, then the task."""
    lines = [f"Load the `{s}` skill with the Skill tool before anything else." for s in agent["skills"]]
    return "\n\n".join(lines + [task])


def _tool_summary(run: Run, block: ToolUseBlock) -> str:
    data = block.input or {}
    if block.name == "Bash":
        return str(data.get("command", ""))[:300]
    if block.name in ("Read", "Write", "Edit"):
        return str(data.get("file_path", "")).replace(str(run.dir) + "/", "")
    if block.name == "Skill":
        return str(data.get("skill", ""))
    if block.name in ("Glob", "Grep"):
        return str(data.get("pattern", ""))
    return ""


async def pump(run: Run, stage: str, name: str, client: ClaudeSDKClient) -> dict:
    """Relay one turn of a session to the activity log; return how it ended.

    Tool results are deliberately not logged: they can hold rows of data, and
    the log is only meant to show what each agent is doing.
    """
    outcome = {"ok": False, "text": "", "note": "The session ended without a result."}
    api_error = ""
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            if message.error:
                api_error = str(message.error)
                run.emit(stage, name, "error", f"API error: {message.error}")
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    run.emit(stage, name, "text", block.text.strip())
                elif isinstance(block, ToolUseBlock) and not block.name.startswith("mcp__"):
                    run.emit(stage, name, "tool", _tool_summary(run, block), tool=block.name)
        elif isinstance(message, UserMessage) and isinstance(message.content, list):
            for block in message.content:
                if isinstance(block, ToolResultBlock) and block.is_error:
                    run.emit(stage, name, "tool_error", str(block.content)[:300])
        elif isinstance(message, ResultMessage):
            ok = message.subtype == "success" and not message.is_error
            outcome = {"ok": ok, "text": message.result or "",
                       "note": "" if ok else f"Session ended: {api_error or message.subtype}",
                       "api_error": api_error if not ok else "",
                       "cost_total": message.total_cost_usd}
            run.emit(stage, name, "result",
                     f"{message.subtype} · {message.num_turns} turns · "
                     f"{message.duration_ms / 1000:.0f}s")
    return outcome


async def turn(run: Run, stage: str, name: str, client: ClaudeSDKClient, prompt: str) -> dict:
    """Send one prompt and relay the reply; wait and resume if the API pushed back.

    A rate limit or an overloaded API ends a turn part-way. The session is still
    open, so the harness pauses and asks the agent to carry on, a few times,
    before it gives the stage up.
    """
    await client.query(prompt)
    outcome = await pump(run, stage, name, client)
    for attempt in range(1, API_RETRIES + 1):
        if not outcome.get("api_error"):
            break
        wait = API_RETRY_SECONDS * attempt
        run.emit(stage, "harness", "check",
                 f"{name}: API error ({outcome['api_error']}); retry {attempt}/{API_RETRIES} in {wait}s")
        await asyncio.sleep(wait)
        await client.query("The API interrupted your last turn. Continue from where you stopped.")
        outcome = await pump(run, stage, name, client)
    return outcome


async def run_agent(run: Run, stage: str, name: str, task: str, *, as_agent: bool = True) -> dict:
    """Run one agent to completion on one task (a sub-agent stage)."""
    agent = load_agent(run, name) if as_agent else None
    prompt = kickoff(agent, task) if agent else task
    run.emit(stage, name, "start", task)
    try:
        async with ClaudeSDKClient(options=agent_options(run, agent)) as client:
            outcome = await turn(run, stage, name, client, prompt)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # CLI missing, bad credentials, budget or turn limit
        run.emit(stage, name, "error", f"{type(exc).__name__}: {exc}"[:500])
        return {"ok": False, "text": "", "note": f"{name}: {type(exc).__name__}: {exc}"[:300]}
    run.add_cost(stage, outcome.get("cost_total"))
    return outcome
