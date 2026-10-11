"""Shared helpers for the QA checks. Standard library only."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IN_SCOPE = ("approve", "revise", "override")
DECISIONS = IN_SCOPE + ("reject",)
ROW_ID = re.compile(r"[A-Za-z0-9_.\-]+\.xlsx:\d+")
RULE_TAG = re.compile(r"\[rule:([A-Za-z0-9\-]+)\]")


class Missing(Exception):
    """A file the check needs is not there: reported as a failure, not a crash."""


def args(doc):
    ap = argparse.ArgumentParser(description=doc.strip().split("\n")[0])
    ap.add_argument("--outputs", default="outputs")
    ap.add_argument("--data", default="data")
    a = ap.parse_args()
    return Path(a.outputs), Path(a.data)


def need(path):
    if not Path(path).is_file():
        raise Missing(f"{path} not found")
    return Path(path)


def text(path):
    return need(path).read_text(encoding="utf-8")


def load(path):
    try:
        return json.loads(text(path))
    except json.JSONDecodeError as exc:
        raise Missing(f"{path} is not valid JSON: {exc}")


def rows(path):
    with open(need(path), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def cells(line):
    """Cells of a markdown table row, or None."""
    if not line.lstrip().startswith("|"):
        return None
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def table_after(markdown, heading):
    """Rows (lists of cells, header first) of the first table under a heading."""
    out, on = [], False
    for line in markdown.splitlines():
        if line.startswith("#"):
            if on and out:
                break
            on = line.lstrip("#").strip().lower().startswith(heading.lower())
            continue
        c = cells(line) if on else None
        if c and not all(set(x) <= set("-: ") for x in c):
            out.append(c)
    return out


def decisions(outputs):
    """{risk_id: (decision, comment)} from auditor-comments.md."""
    out = {}
    for line in text(outputs / "auditor-comments.md").split("\n## General comments")[0].splitlines():
        c = cells(line)
        if c and len(c) >= 5 and re.fullmatch(r"R-\d{2,}", c[0]):
            out[c[0]] = (c[3].lower().strip("* "), c[4])
    return out


def finish(name, items, summary=""):
    """Print the result block every check uses and return the exit code."""
    status = "FAIL" if items else "PASS"
    print(f"{status} {name}: {len(items)} item(s)" + (f" | {summary}" if summary else ""))
    for item in items:
        print(f"  - {item}")
    return 1 if items else 0


def main(name, run, doc):
    outputs, data = args(doc)
    try:
        items, summary = run(outputs, data)
    except Missing as exc:
        items, summary = [str(exc)], "could not complete"
    sys.exit(finish(name, items, summary))
