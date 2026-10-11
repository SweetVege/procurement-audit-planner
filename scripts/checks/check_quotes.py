#!/usr/bin/env python3
"""Quote check: rules.json against the Contract Rules PDF, and the register against rules.json.

1. Runs the extract-rules verifier (every verbatim quote on its stated PDF page).
2. Every rule citation in risk-register.md names a rule in rules.json with the right clause.
3. Every quote excerpt in the register's "Rules cited" table is the start of that
   rule's verbatim quote, with the right clause and page.
"""
import re
import subprocess
import sys

import common as c

NAME = "quotes"


def run(outputs, data):
    items = []
    rules_path, pdf = c.need(outputs / "rules.json"), c.need(data / "contract-rules.pdf")
    verifier = c.need(c.ROOT / ".claude/skills/extract-rules/verify_quotes.py")
    out = subprocess.run([sys.executable, str(verifier), "--rules", str(rules_path), "--pdf", str(pdf)],
                         capture_output=True, text=True)
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    if out.returncode != 0:
        errors = [l for l in lines if l.startswith("ERROR")] or lines[-3:] or [out.stderr.strip()]
        items += [f"rules.json verifier: {l.replace('ERROR', '').strip()}" for l in errors]
    rules = {r["rule_id"]: r for r in c.load(rules_path)["rules"]}
    norm = lambda s: " ".join(str(s).split())

    register = c.text(outputs / "risk-register.md")
    cited = re.findall(r"\[(CPR-\d+), cl\. ([^\]]+)\]", register)
    for rule_id, clause in sorted(set(cited)):
        if rule_id not in rules:
            items.append(f"risk-register.md cites {rule_id}, which is not in rules.json")
        elif rules[rule_id]["clause"] != clause:
            items.append(f"risk-register.md cites {rule_id} as cl. {clause}; rules.json says {rules[rule_id]['clause']}")
    table = c.table_after(register, "Rules cited")[1:]
    if cited and not table:
        items.append("risk-register.md cites rules but has no 'Rules cited' table of quote excerpts")
    listed = set()
    for row in table:
        if len(row) != 4:
            items.append(f"'Rules cited' row is malformed: {row}")
            continue
        rule_id, clause, page, quote = row
        listed.add(rule_id)
        rule = rules.get(rule_id)
        if not rule:
            items.append(f"'Rules cited' lists {rule_id}, which is not in rules.json")
            continue
        if clause != rule["clause"] or str(page) != str(rule.get("page", "")):
            items.append(f"{rule_id}: register shows cl. {clause} p. {page}; rules.json says "
                         f"cl. {rule['clause']} p. {rule.get('page')}")
        want = norm(rule.get("verbatim_quote", ""))
        got = norm(quote)
        cut = got.endswith("…")
        got = got[:-1].rstrip() if cut else got
        if not got or not (want.startswith(got) if cut else want == got):
            items.append(f"{rule_id}: quote excerpt in the register does not match rules.json: \"{got[:60]}…\"")
    for rule_id in sorted({r for r, _ in cited} - listed):
        items.append(f"{rule_id} is cited in the register but has no excerpt in 'Rules cited'")
    summary = (f"verifier: {lines[-1] if lines else 'no output'}; {len(set(cited))} rules cited in the register, "
               f"{len(table)} excerpts compared")
    return items, summary


if __name__ == "__main__":
    c.main(NAME, run, __doc__)
