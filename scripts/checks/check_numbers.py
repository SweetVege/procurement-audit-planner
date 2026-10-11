#!/usr/bin/env python3
"""Number check: every figure in the three pack documents is a value in the evidence.

A figure is anything with a £ sign, or a number of three or more digits, in
planning-memo.md, risk-control-matrix.md or audit-program.md. Each must equal a
value in analytics.json, pack-figures.json, rules.json or outputs/samples/*.csv
(to the decimals shown; a percentage may be the value times 100).

Skipped, because they are references and not figures: anything in `code`
(row IDs, file names, analytics paths, recipe values), rule/test/risk IDs,
dates and times, years, clause and page references, and the auditor's own
comments, which are quoted word for word from auditor-comments.md.
"""
import re

import common as c

NAME = "numbers"
DOCS = ("planning-memo.md", "risk-control-matrix.md", "audit-program.md")
FIGURE = re.compile(r"(£\s?)?(\d[\d,]*(?:\.\d+)?)\s?(million|m\b|k\b|%)?", re.I)
REFERENCE = re.compile(r"(?:clauses?|cl\.|rows?|pages?|p\.|pp\.|table|figure|appendix|app|section|paragraphs?|para\.?|"
                       r"revision|round|version|v)\s*$", re.I)
SCRUB = [re.compile(p) for p in (
    r"`[^`]*`",                                         # code spans
    r"[A-Za-z0-9_.\-]+\.xlsx:\d+",                      # row IDs outside code
    r"\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?\b",  # dates and times
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b[A-Z]{1,4}-\d+(?:\.\d+)?\b",                    # CPR-58, T-01.1, R-01, AUD-01
)]


def numbers_in(node, out):
    if isinstance(node, bool) or node is None:
        return
    if isinstance(node, (int, float)):
        out.add(float(node))
    elif isinstance(node, str):
        for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", node):
            try:
                out.add(float(m.group(0).replace(",", "")))
            except ValueError:
                pass
    elif isinstance(node, dict):
        for v in node.values():
            numbers_in(v, out)
    elif isinstance(node, list):
        for v in node:
            numbers_in(v, out)


def run(outputs, data):
    values = set()
    for name in ("analytics.json", "pack-figures.json", "rules.json"):
        numbers_in(c.load(outputs / name), values)
    samples = sorted((outputs / "samples").glob("*.csv")) if (outputs / "samples").is_dir() else []
    for path in samples:
        for row in c.rows(path):
            numbers_in(list(row.values()), values)
    clauses = {r["clause"] for r in c.load(outputs / "rules.json")["rules"]}
    comments = [comment for _, comment in c.decisions(outputs).values() if comment]
    items, checked = [], 0
    for doc in DOCS:
        for n, line in enumerate(c.text(outputs / doc).splitlines(), 1):
            for comment in comments:
                line = line.replace(comment, " ")
            for pattern in SCRUB:
                line = pattern.sub(" ", line)
            for m in FIGURE.finditer(line):
                pound, digits, unit = m.group(1), m.group(2), (m.group(3) or "").lower()
                plain = digits.replace(",", "")
                if not pound and sum(ch.isdigit() for ch in plain) < 3:
                    continue
                before = line[:m.start()]
                if not pound:
                    if REFERENCE.search(before) or plain in clauses:
                        continue
                    if re.fullmatch(r"(19|20)\d{2}", plain):
                        continue                        # a year
                    if before.endswith(".") and before[-2:-1].isdigit():
                        continue                        # tail of a dotted clause number
                value = float(plain) * {"million": 1e6, "m": 1e6, "k": 1e3}.get(unit, 1)
                places = len(plain.split(".")[1]) if "." in plain and unit in ("", "%") else 0
                checked += 1
                ok = any(round(v, places) == round(value, places) for v in values)
                if not ok and unit == "%":
                    ok = any(round(v * 100, places) == round(value, places) for v in values)
                if not ok and unit in ("million", "m", "k"):
                    ok = any(abs(v - value) < 0.5 for v in values)
                if not ok:
                    items.append(f"{doc}:{n}: {m.group(0).strip()} is not a value in analytics.json, "
                                 "pack-figures.json, rules.json or the sample files")
    return items, f"{checked} figures checked in {len(DOCS)} documents against {len(values):,} evidence values"


if __name__ == "__main__":
    c.main(NAME, run, __doc__)
