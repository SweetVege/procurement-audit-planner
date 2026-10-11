"""The six stages, in order, and the code that runs each one.

The harness, not a model, decides what runs next. After every agent stage it
re-runs the project's own verifier and trusts that exit code over the agent's
report; the two human gates are forms whose input the harness writes to the
same files the auditor edits by hand in Claude Code.
"""
from __future__ import annotations

import asyncio
import json
import re
import time

from .core import STAGE_IDS, Run, run_agent
from .team import Team

STAGES = [
    {"id": "rules", "title": "Extract the rules", "kind": "agent", "actor": "extract-rules skill",
     "about": "Reads the Contract Rules PDF and writes one entry per testable rule, each with "
              "its clause, page and a verbatim quote. The harness then re-runs the quote verifier."},
    {"id": "evidence", "title": "Analyse the evidence", "kind": "agent",
     "actor": "spend-analyst ∥ findings-analyst",
     "about": "Two sub-agents run side by side. One writes and runs Python over every published "
              "payment; the other records the audit history and the council's own risk scoring "
              "method from the committee papers."},
    {"id": "register", "title": "Draft the risk register", "kind": "agent",
     "actor": "risk-assessor + risk-assessment skill",
     "about": "Merges rules, analytics and history into rated risks. Every rating cites its "
              "evidence; every figure is filled in by the builder script, never typed."},
    {"id": "gate1", "title": "Auditor decides each risk", "kind": "human", "actor": "you, the auditor",
     "about": "Approve, revise, override or reject every risk. The risk-assessor then revises the "
              "register, and the harness checks that the scope gate is closed."},
    {"id": "team", "title": "Build and check the pack", "kind": "agent",
     "actor": "planner ⇄ challenger ⇄ qa-reviewer",
     "about": "Three agents that message each other: the planner builds the pack, the challenger "
              "tests it against the evidence, the qa-reviewer runs four automated checks on every "
              "version."},
    {"id": "signoff", "title": "Auditor signs off", "kind": "human", "actor": "you, the auditor",
     "about": "Read the challenges left for you and the QA verdict, then approve the pack or "
              "return it to the team."},
]
DECISIONS = ("approve", "revise", "override", "reject")
SIGNOFF_DECISIONS = ("Approve the pack", "Return it to the team")


def can_run(run: Run, stage: str) -> str:
    """Empty string if the stage may start now, otherwise the reason it may not."""
    if run.readonly:
        return "The reference run is read-only. Start a new run to execute stages."
    for earlier in STAGE_IDS[:STAGE_IDS.index(stage)]:
        if run.state["stages"][earlier]["status"] != "done":
            return f"Stage '{earlier}' has to finish first."
    return ""


def _cell(text: str) -> str:
    """Make free text safe inside one Markdown table cell."""
    return re.sub(r"\s+", " ", str(text)).replace("|", "/").strip()


# ---------------------------------------------------------------- gate 1 file

def read_decisions(run: Run) -> dict:
    """Parse outputs/auditor-comments.md into rows the decision form can show."""
    path = run.outputs / "auditor-comments.md"
    if not path.exists():
        return {"risks": [], "general": ""}
    text = path.read_text()
    risks = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and re.fullmatch(r"R-\d+", cells[0]):
            risks.append(dict(zip(("id", "title", "rating", "decision", "comment"), cells)))
    general = text.split("## General comments", 1)[-1] if "## General comments" in text else ""
    general = re.sub(r"<!--.*?-->", "", general, flags=re.S).strip()
    return {"risks": risks, "general": general}


def write_decisions(run: Run, payload: dict) -> None:
    """Enter the form's decisions into the template, leaving every other cell as built."""
    given = {d["id"]: d for d in payload.get("decisions", [])}
    path = run.outputs / "auditor-comments.md"
    lines, seen = [], set()
    for line in path.read_text().split("## General comments", 1)[0].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] in given:
            choice = given[cells[0]]
            if choice.get("decision") not in DECISIONS:
                raise ValueError(f"{cells[0]}: decision must be one of {', '.join(DECISIONS)}")
            if choice["decision"] != "approve" and not _cell(choice.get("comment", "")):
                raise ValueError(f"{cells[0]}: a {choice['decision']} decision needs a comment")
            cells[3], cells[4] = choice["decision"], _cell(choice.get("comment", ""))
            line = "| " + " | ".join(cells) + " |"
            seen.add(cells[0])
        lines.append(line)
    missing = [r["id"] for r in read_decisions(run)["risks"] if r["id"] not in seen]
    if missing:
        raise ValueError("every risk needs a decision; missing: " + ", ".join(missing))
    general = str(payload.get("general", "")).strip()
    path.write_text("\n".join(lines).rstrip() + "\n\n## General comments\n\n"
                    "<!-- Anything not tied to one risk, including a request to add a risk. -->\n"
                    + general + "\n")


def write_signoff(run: Run, payload: dict) -> None:
    decision, auditor = payload.get("decision"), _cell(payload.get("auditor", ""))
    if decision not in SIGNOFF_DECISIONS:
        raise ValueError("decision must be one of: " + "; ".join(SIGNOFF_DECISIONS))
    if not auditor:
        raise ValueError("the auditor's name is required")
    values = {"Decision": decision, "Auditor": auditor, "Date": time.strftime("%Y-%m-%d"),
              "Comments": _cell(payload.get("comments", ""))}
    path = run.outputs / "review.md"
    head, block = path.read_text().rsplit("## Auditor sign-off", 1)
    lines = []
    for line in block.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        key = next((k for k in values if len(cells) == 2 and cells[0].startswith(k)), None)
        lines.append(f"| {cells[0]} | {values[key]} |" if key else line)
    path.write_text(head + "## Auditor sign-off" + "\n".join(lines) + "\n")


# --------------------------------------------------------------------- stages

async def _verify(run: Run, stage: str, label: str, *script: str, expect: str = "") -> str:
    """Re-run one of the project's verifiers; return '' on a pass, else why not."""
    code, out = await run.python(*script)
    last = out.splitlines()[-1] if out else "(no output)"
    ok = code == 0 and (expect in out if expect else True)
    run.emit(stage, "harness", "check", f"{label}: {'PASS' if ok else 'FAIL'} — {last}")
    return "" if ok else f"{label} failed: {last}"


async def _rules(run: Run, payload: dict) -> str:
    result = await run_agent(run, "rules", "extract-rules", "/extract-rules", as_agent=False)
    if not result["ok"]:
        return result["note"]
    return await _verify(run, "rules", "Quote verifier", ".claude/skills/extract-rules/verify_quotes.py")


async def _evidence(run: Run, payload: dict) -> str:
    spend, findings = await asyncio.gather(
        run_agent(run, "evidence", "spend-analyst",
                  "Analyse the full spend population against the thresholds in outputs/rules.json "
                  "and the Contracts Finder export, following your instructions from the first "
                  "step to the last. Write outputs/analytics.json and outputs/analytics-full/."),
        run_agent(run, "evidence", "findings-analyst",
                  "Read the committee papers in data/committee/ and write outputs/history.json, "
                  "following your instructions from the first step to the last, then verify it."),
    )
    for result in (spend, findings):
        if not result["ok"]:
            return result["note"]
    return (await _verify(run, "evidence", "Spend self-check", "scripts/selfcheck.py")
            or await _verify(run, "evidence", "History verifier", "scripts/verify_history.py"))


async def _register(run: Run, payload: dict) -> str:
    result = await run_agent(run, "register", "risk-assessor",
                             "Draft the risk register from outputs/rules.json, "
                             "outputs/analytics.json and outputs/history.json.")
    if not result["ok"]:
        return result["note"]
    missing = [f for f in ("risk-register.md", "auditor-comments.md") if not (run.outputs / f).exists()]
    return f"The builder did not write: {', '.join(missing)}" if missing else ""


async def _gate(run: Run, stage: str) -> tuple[str, str]:
    """Run the scope gate. Returns (the GATE line, '' if closed else the reason)."""
    code, out = await run.python(".claude/skills/audit-program/build_pack.py", "--gate")
    line = next((l for l in out.splitlines() if l.startswith("GATE")), out[-300:] or "(no output)")
    closed = line.startswith("GATE CLOSED")
    run.emit(stage, "harness", "check", f"Scope gate: {line}")
    return line, "" if closed else line


async def _gate1(run: Run, payload: dict) -> str:
    write_decisions(run, payload)
    run.emit("gate1", "auditor", "decision", "Decisions recorded in outputs/auditor-comments.md: "
             + ", ".join(f"{d['id']} {d['decision']}" for d in payload["decisions"]))
    result = await run_agent(run, "gate1", "risk-assessor",
                             "The auditor has completed outputs/auditor-comments.md. Revise the "
                             "risk register to apply those decisions.")
    if not result["ok"]:
        return result["note"]
    return (await _gate(run, "gate1"))[1]


async def _team(run: Run, payload: dict) -> str:
    line, problem = await _gate(run, "team")
    if problem:
        return problem
    result = await Team(run).run_team(line)
    if not result["ok"]:
        return result["note"]
    problem = await _verify(run, "team", "QA checks", "scripts/checks/run_checks.py")
    review = run.outputs / "review.md"
    if not problem and not (review.exists() and "READY FOR SIGN-OFF" in review.read_text()):
        problem = "The qa-reviewer's verdict is not READY FOR SIGN-OFF: " + result["qa_done"][:200]
    return problem and f"BLOCKED — the pack goes back to the team. {problem}"


async def _signoff(run: Run, payload: dict) -> str:
    write_signoff(run, payload)
    run.emit("signoff", "auditor", "decision", f"{payload['decision']} — {payload['auditor']}")
    if payload["decision"] != SIGNOFF_DECISIONS[0]:
        return "Returned to the team by the auditor. Re-run the team stage."
    return ""


RUNNERS = {"rules": _rules, "evidence": _evidence, "register": _register,
           "gate1": _gate1, "team": _team, "signoff": _signoff}


async def run_stage(run: Run, stage: str, payload: dict) -> None:
    """Run one stage to done or failed. Never raises, except when cancelled."""
    if stage == "gate1":  # a human gate keeps its input file; the pack is invalidated
        run.reset_from("team", blank_first=True)
    elif stage != "signoff":
        run.reset_from(stage)
    run.set_stage(stage, "running")
    try:
        problem = await RUNNERS[stage](run, payload)
    except asyncio.CancelledError:
        run.set_stage(stage, "failed", note="Stopped by the operator.")
        raise
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        problem = f"{type(exc).__name__}: {exc}"
    run.set_stage(stage, "failed" if problem else "done", note=problem or "")
