"""The agent team: three long-lived sessions and a message bus between them.

In Claude Code the planner, challenger and qa-reviewer are teammates that talk
through the built-in SendMessage tool, with the main chat as their lead. Here
the harness is the lead. Each teammate is its own Agent SDK session that stays
open across turns; a small in-process MCP tool, `send_message`, puts a message
in the recipient's inbox, and every batch of inbox messages is delivered to the
recipient as its next turn. The agents' own instructions (.claude/agents/*.md)
are used unchanged: they already describe the protocol in terms of messages.
"""
from __future__ import annotations

import asyncio
from typing import Any

from claude_agent_sdk import ClaudeSDKClient, create_sdk_mcp_server, tool

from .core import Run, agent_options, kickoff, load_agent, turn

LEAD = "lead"
MEMBERS = ("planner", "challenger", "qa-reviewer")
DONE_LINES = {"planner": "PLANNER DONE", "challenger": "CHALLENGER DONE", "qa-reviewer": "QA DONE"}
SEND_TOOL = "mcp__team__send_message"
MAX_NUDGES = 2
_STOP = object()

TEAM_NOTE = """## How messages work in this deployment

You are `{name}`. Your teammates are {others}; the lead is `lead`.

The SendMessage tool your instructions refer to is provided here as the
`send_message` tool (`mcp__team__send_message`), which takes `to` and
`message`. Text you write outside that tool reaches no one. Messages addressed
to you arrive as your next turn, so when you are waiting for a teammate, end
your turn. The lead is an automated harness: it starts the team, relays
nothing, and cannot make the auditor's decisions."""


class Team:
    def __init__(self, run: Run, stage: str = "team"):
        self.run = run
        self.stage = stage
        self.inbox: dict[str, asyncio.Queue] = {m: asyncio.Queue() for m in MEMBERS}
        self.busy = {m: False for m in MEMBERS}
        self.done: dict[str, str | None] = {m: None for m in MEMBERS}
        self.to_lead: list[tuple[str, str]] = []
        self.failure = ""
        self.wake = asyncio.Event()

    # ---------------------------------------------------------------- bus

    def post(self, sender: str, to: str, text: str) -> None:
        self.run.emit(self.stage, sender, "message", text, to=to)
        if to == LEAD:
            self.to_lead.append((sender, text))
            line = DONE_LINES.get(sender)
            if line and text.lstrip().upper().startswith(line):
                self.done[sender] = text.strip()
        else:
            self.inbox[to].put_nowait((sender, text))
        self.wake.set()

    def _server(self, sender: str) -> Any:
        recipients = [m for m in (*MEMBERS, LEAD) if m != sender]

        @tool("send_message",
              "Send a message to a teammate or to the lead. This is the SendMessage tool "
              f"your instructions refer to. Recipients: {', '.join(recipients)}.",
              {"to": str, "message": str})
        async def send_message(args: dict[str, Any]) -> dict[str, Any]:
            to = str(args.get("to", "")).strip().lower()
            if to not in recipients:
                reply = f"Not delivered: unknown recipient {to!r}. Use one of: {', '.join(recipients)}."
            else:
                self.post(sender, to, str(args.get("message", "")))
                reply = f"Delivered to {to}."
            return {"content": [{"type": "text", "text": reply}]}

        return create_sdk_mcp_server(name="team", tools=[send_message])

    # ------------------------------------------------------------ members

    async def _member(self, name: str) -> None:
        """Hold one teammate's session open; each batch of messages is one turn."""
        first = await self.inbox[name].get()
        if first is _STOP:
            return
        self.busy[name] = True  # before the first await, so connecting never looks idle
        agent = load_agent(self.run, name)
        others = ", ".join(f"`{m}`" for m in MEMBERS if m != name)
        options = agent_options(
            self.run, agent,
            extra_prompt=TEAM_NOTE.format(name=name, others=others),
            mcp_servers={"team": self._server(name)}, mcp_tools=[SEND_TOOL],
        )
        batch, first_turn = [first], True
        async with ClaudeSDKClient(options=options) as client:
            while True:
                while not self.inbox[name].empty():
                    batch.append(self.inbox[name].get_nowait())
                stop = _STOP in batch
                messages = [m for m in batch if m is not _STOP]
                if messages:
                    text = "\n\n---\n\n".join(f"Message from `{s}`:\n\n{t}" for s, t in messages)
                    outcome = await turn(self.run, self.stage, name, client,
                                         kickoff(agent, text) if first_turn else text)
                    first_turn = False
                    self.run.state["stages"][self.stage].setdefault("sessions", {})[name] = \
                        outcome.get("cost_total") or 0.0
                    if not outcome["ok"] and not self.done[name]:
                        # A member that has already sent its done line has nothing
                        # left that the others depend on, so its failure is not fatal.
                        self.failure = f"{name}: {outcome['note']}"
                # Idle only if nothing arrived while this turn was running.
                self.busy[name] = not self.inbox[name].empty()
                self.wake.set()
                if stop or self.failure:
                    return
                batch = [await self.inbox[name].get()]
                self.busy[name] = True

    def _idle(self) -> bool:
        return not any(self.busy.values()) and all(q.empty() for q in self.inbox.values())

    # --------------------------------------------------------------- lead

    async def run_team(self, gate_line: str) -> dict:
        tasks = {m: asyncio.create_task(self._member(m)) for m in MEMBERS}
        self.post(LEAD, "planner",
                  f"The lead has run the gate check: `{gate_line}`. Your teammates are "
                  "`challenger` and `qa-reviewer`; both are waiting for your PACK READY v1. "
                  "Start now.")
        nudges = 0
        try:
            while not all(self.done.values()) and not self.failure:
                await self.wake.wait()
                self.wake.clear()
                await asyncio.sleep(0)  # let a finishing member mark itself idle
                for name, task in tasks.items():
                    if task.done() and task.exception():
                        self.failure = f"{name}: {task.exception()!r}"[:300]
                if self.failure or all(self.done.values()) or not self._idle():
                    continue
                # Everyone is waiting and no message is in flight.
                if nudges >= MAX_NUDGES:
                    waiting = [m for m in MEMBERS if not self.done[m]]
                    self.failure = ("The team stopped before finishing; no done line from "
                                    + ", ".join(waiting) + ". See the messages to the lead.")
                    break
                nudges += 1
                for name in MEMBERS:
                    if not self.done[name]:
                        self.post(LEAD, name,
                                  "Every teammate is idle and no message is in flight. If your "
                                  "finishing conditions hold, send your done line now. If not, "
                                  "send the teammate you are waiting on what you need, or tell "
                                  "the lead what is blocking you.")
        finally:
            for name in MEMBERS:
                self.inbox[name].put_nowait(_STOP)
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for name, result in zip(tasks, results):
                if isinstance(result, Exception) and not self.failure:
                    self.failure = f"{name}: {result!r}"[:300]
            sessions = self.run.state["stages"][self.stage].pop("sessions", {})
            self.run.add_cost(self.stage, sum(sessions.values()))
        return {"ok": not self.failure, "note": self.failure, "qa_done": self.done["qa-reviewer"] or ""}
