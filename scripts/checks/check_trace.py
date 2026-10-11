#!/usr/bin/env python3
"""Traceability check: rule -> risk -> control -> test, scope, and challenges.

1. Every rule in rules.json is cited by a rated risk, a control or a test, or is
   listed in audit-plan.json as not tested with a reason.
2. Every approved in-scope risk has a control with a test, every control has a
   test, and the risk appears in the matrix and in the program.
3. Every risk the register labels High or Extreme is in scope, or was rejected
   by the auditor with a recorded reason that the memo carries.
4. challenges.md exists, every row cites evidence, and no row is open.
"""
import re

import common as c

NAME = "trace"
HIGH = re.compile(r"high|extreme", re.I)
EVIDENCE = re.compile(r"\[(?:rule|metric|history):[^\]\s][^\]]*\]|\b[TCP]-\d{2}(?:\.\d+)?\b")
CLOSED = ("resolved", "declined", "for the auditor")


def risk_text(risk):
    parts = [risk.get("description", ""), risk.get("proposed_focus", "")] + list(risk.get("evidence") or [])
    for key in ("likelihood", "impact"):
        parts.append((risk.get(key) or {}).get("justification", ""))
    return " ".join(str(p) for p in parts)


def run(outputs, data):
    items = []
    rules = {r["rule_id"]: r for r in c.load(outputs / "rules.json")["rules"]}
    ratings = c.load(outputs / "risk-ratings.json")
    decisions = c.decisions(outputs)
    plan = c.load(outputs / "audit-plan.json")
    register = c.text(outputs / "risk-register.md")
    matrix, program = c.text(outputs / "risk-control-matrix.md"), c.text(outputs / "audit-program.md")
    memo = c.text(outputs / "planning-memo.md")
    risks = {r["risk_id"]: r for r in ratings.get("risks", [])}
    scope = [rid for rid in risks if decisions.get(rid, ("", ""))[0] in c.IN_SCOPE]
    planned = {r["risk_id"]: r for r in plan.get("risks", [])}

    # 1. rules
    cited = {}
    for rid, risk in risks.items():
        for rule in c.RULE_TAG.findall(risk_text(risk)):
            cited.setdefault(rule, set()).add(rid)
    for risk in planned.values():
        for control in risk.get("controls", []):
            for rule in control.get("rules", []):
                cited.setdefault(rule, set()).add(control["control_id"])
        for test in risk.get("tests", []):
            for rule in c.RULE_TAG.findall(test.get("step", "")):
                cited.setdefault(rule, set()).add(test["test_id"])
    not_tested = {}
    for entry in plan.get("rules_not_tested", []):
        for rule in entry.get("rule_ids", []):
            not_tested[rule] = str(entry.get("reason", "")).strip()
    for rule in rules:
        if rule in cited:
            continue
        if rule not in not_tested:
            items.append(f"{rule} (cl. {rules[rule]['clause']}) is cited by no risk, control or test and is not "
                         "listed as not tested")
        elif not not_tested[rule]:
            items.append(f"{rule} is listed as not tested with no reason")
    for rule in sorted(set(cited) | set(not_tested)):
        if rule not in rules:
            items.append(f"{rule} is cited or listed but is not a rule in rules.json")

    # 2. risk -> control -> test, and presence in the documents
    matrix_rows = " ".join(row[0] for row in c.table_after(matrix, "Risk and control matrix")[1:])
    for rid in scope:
        risk = planned.get(rid)
        if not risk:
            items.append(f"{rid} is approved and in scope but is not in audit-plan.json")
            continue
        controls = [x["control_id"] for x in risk.get("controls", [])]
        tested = {cid for t in risk.get("tests", []) for cid in t.get("controls", [])}
        if not controls:
            items.append(f"{rid} has no control")
        elif not tested & set(controls):
            items.append(f"{rid} has no control with a test")
        for cid in controls:
            if cid not in tested:
                items.append(f"{cid} has no test")
        if not re.search(rf"\b{rid}\b", matrix_rows):
            items.append(f"{rid} does not appear in risk-control-matrix.md")
        if not re.search(rf"^## {rid}\b", program, re.M):
            items.append(f"{rid} has no section in audit-program.md")
    for rid in planned:
        if rid not in scope:
            items.append(f"{rid} is planned in audit-plan.json but is not an approved in-scope risk")

    # 3. High risks
    summary = c.table_after(register, "Summary")
    high = []
    if summary:
        head = [h.lower() for h in summary[0]]
        col = {name: head.index(name) for name in ("risk", "matrix label", "band") if name in head}
        for row in summary[1:]:
            label = " ".join(row[col[k]] for k in ("matrix label", "band") if k in col)
            if HIGH.search(label):
                high.append(row[col["risk"]])
    else:
        items.append("risk-register.md has no Summary table")
    out_of_scope = memo.split("### Out of scope")[1].split("\n## ")[0] if "### Out of scope" in memo else ""
    for rid in high:
        decision, comment = decisions.get(rid, ("", ""))
        if decision in c.IN_SCOPE:
            continue
        if decision != "reject":
            items.append(f"{rid} is rated High or above and has no auditor decision")
        elif not comment.strip():
            items.append(f"{rid} is rated High or above and was rejected with no recorded reason")
        elif rid not in out_of_scope:
            items.append(f"{rid} is rated High or above and rejected, but the memo's out-of-scope section omits it")

    # 4. challenges
    try:
        challenges = c.text(outputs / "challenges.md")
    except c.Missing as exc:          # report it, but keep the results of parts 1-3
        challenges = None
        items.append(str(exc))
    table = c.table_after(challenges, "All challenges") if challenges is not None else []
    n_rows = 0
    if challenges is None:
        pass
    elif not table:
        items.append("challenges.md has no 'All challenges' table")
    else:
        head = [h.lower() for h in table[0]]
        try:
            i_id, i_ev, i_st = head.index("#"), head.index("challenge and evidence"), head.index("status")
        except ValueError:
            items.append("challenges.md table needs the columns '#', 'Challenge and evidence' and 'Status'")
            table = []
        for row in table[1:]:
            if len(row) != len(head):
                items.append(f"challenges.md row is malformed: {row[:2]}")
                continue
            n_rows += 1
            status = row[i_st].lower().strip("* ")
            if not EVIDENCE.search(row[i_ev]):
                items.append(f"challenge #{row[i_id]} cites no evidence (no rule, metric, history or pack reference)")
            if status == "open":
                items.append(f"challenge #{row[i_id]} is still open")
            elif status not in CLOSED:
                items.append(f"challenge #{row[i_id]} has status '{row[i_st]}'; use {', '.join(CLOSED)}")
    return items, (f"{len(rules)} rules ({len([r for r in rules if r in cited])} cited, {len(not_tested)} listed as not "
                   f"tested); {len(scope)} risks in scope; {len(high)} rated High or above; {n_rows} challenges")


if __name__ == "__main__":
    c.main(NAME, run, __doc__)
