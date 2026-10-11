#!/usr/bin/env python3
"""Verify outputs/history.json against the PDFs in data/committee/.

Checks, in order:
  1. structure  - top-level keys, item fields, unique IDs, allowed values
  2. sources    - every item cites at least one {file, pdf_page, quote}; the file
                  is a PDF in the committee folder and the page exists
  3. quotes     - every quote appears on its stated page (plain or -layout text,
                  whitespace collapsed; nothing else is forgiven)
  4. printed    - recorded opinions, labels, scores and bands are printed inside
                  the item's own quotes (nothing recorded that the quote does not show)
  5. coverage   - every PDF in the folder is listed with its page count; the
                  mandatory gaps are present (risk register; agreed actions and
                  scoring method when those sections are empty)

Usage (from the project root):
  .venv/bin/python scripts/verify_history.py
  .venv/bin/python scripts/verify_history.py --history X.json --dir some/folder

Exit code 0 = all checks pass, 1 = at least one error, 2 = cannot run.
Standard library only; needs pdftotext (poppler) on PATH.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOP = {"generated_from", "audits", "opinion_basis", "agreed_actions",
       "risk_themes", "scoring_method", "discrepancies", "gaps"}
SCORING = {"usable", "reason_if_not_usable", "rating_stages", "likelihood_scale",
           "impact_scale", "matrix", "bands", "appetite"}
AUDIT_KINDS = {"audit", "follow_up", "advisory"}
GAP_TOPICS = {"risk_register", "agreed_actions", "scoring_method",
              "opinion_definitions", "audit_plan_detail", "other"}
MIN_QUOTE_CHARS = 10

# section -> (id prefix, required fields besides id and sources)
LISTS = {
    "audits": ("AUD", {"kind", "area", "directorate", "service", "opinion",
                       "follow_up_opinion", "period"}),
    "opinion_basis": ("OPB", {"statement"}),
    "agreed_actions": ("ACT", {"theme", "due_date", "status"}),
    "risk_themes": ("THM", {"theme", "detail"}),
    "discrepancies": ("DIS", {"description"}),
}
SCORING_LISTS = {
    "rating_stages": ("STG", {"name", "definition"}),
    "likelihood_scale": ("LIK", {"score", "label", "definition", "probability"}),
    "impact_scale": ("IMP", {"score", "label", "criteria"}),
    "bands": ("BND", {"band", "score_range", "rag", "escalation", "response"}),
    "appetite": ("APP", {"category", "level", "statement"}),
}
MATRIX_ROW = {"impact_score", "impact_label", "scores", "bands"}
# Fields whose value must be printed in the item's own quotes.
PRINTED = {
    "audits": ("area", "opinion", "follow_up_opinion"),
    "likelihood_scale": ("score", "label", "probability"),
    "impact_scale": ("score", "label"),
    "bands": ("band", "score_range", "rag"),
    "appetite": ("level",),
    "rating_stages": ("name",),
}


def normalise(text):
    return " ".join(str(text).split())


def pdf_pages(pdf, layout):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + [str(pdf), "-"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        sys.exit(f"CANNOT RUN: pdftotext failed on {pdf}: {out.stderr.strip()}")
    pages = out.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [normalise(p) for p in pages]


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def tokens(value):
    """Words and numbers of a recorded value, edge punctuation stripped."""
    return [t for t in (w.strip(".,;:()[]\"'“”‘’") for w in normalise(value).split()) if t]


def printed_in(value, text):
    return all(re.search(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", text)
               for t in tokens(value))


class Checker:
    def __init__(self, data, folder):
        self.data = data
        self.folder = folder
        self.pdfs = {p.name: p for p in sorted(folder.glob("*.pdf"))}
        self.text = {}          # file name -> (plain pages, layout pages)
        self.errors = []
        self.quotes_checked = 0

    def err(self, check, where, msg):
        self.errors.append(f"[{check}] {where}: {msg}")

    def pages(self, name):
        if name not in self.text:
            pdf = self.pdfs[name]
            self.text[name] = (pdf_pages(pdf, False), pdf_pages(pdf, True))
        return self.text[name]

    # -- sources and quotes ---------------------------------------------
    def sources(self, item, where):
        """Check an item's sources; return the combined text of the quotes that verified."""
        srcs = item.get("sources")
        if not isinstance(srcs, list) or not srcs:
            self.err("sources", where, "needs a non-empty 'sources' list")
            return ""
        found = []
        for n, src in enumerate(srcs):
            at = f"{where} sources[{n}]"
            if not isinstance(src, dict) or set(src) - {"section"} != {"file", "pdf_page", "quote"}:
                self.err("sources", at, "must have exactly file, pdf_page, quote (and optional section)")
                continue
            name, page, quote = src["file"], src["pdf_page"], src["quote"]
            if name not in self.pdfs:
                self.err("sources", at, f"file {name!r} is not a PDF in {self.folder}")
                continue
            plain, layout = self.pages(name)
            if not is_int(page) or not 1 <= page <= len(plain):
                self.err("sources", at, f"pdf_page {page!r} is outside 1-{len(plain)} for {name}")
                continue
            if not isinstance(quote, str) or len(normalise(quote)) < MIN_QUOTE_CHARS:
                self.err("quotes", at, f"quote must be text of at least {MIN_QUOTE_CHARS} characters")
                continue
            wanted = normalise(quote)
            self.quotes_checked += 1
            if wanted in plain[page - 1] or wanted in layout[page - 1]:
                found.append(wanted)
                continue
            elsewhere = [i + 1 for i in range(len(plain))
                         if wanted in plain[i] or wanted in layout[i]]
            short = wanted[:70] + ("..." if len(wanted) > 70 else "")
            if elsewhere:
                self.err("quotes", at, f"quote is not on page {page} of {name}; it is on page "
                                       f"{', '.join(map(str, elsewhere))}")
            else:
                self.err("quotes", at, f"quote not found on page {page} of {name} "
                                       f"or any other page: \"{short}\"")
        return " ".join(found)

    def printed(self, section, item, where, quote_text):
        if not quote_text:
            return
        for field in PRINTED.get(section, ()):
            value = item.get(field)
            if value is None or value == "":
                continue
            if not printed_in(value, quote_text):
                self.err("printed", where, f"'{field}' {value!r} is not printed in this item's quotes")

    # -- structure -------------------------------------------------------
    def items(self, section, items, prefix, required, seen):
        if not isinstance(items, list):
            self.err("structure", section, "must be a list")
            return
        for n, item in enumerate(items):
            ident = item.get("id") if isinstance(item, dict) else None
            where = ident if isinstance(ident, str) else f"{section}[{n}]"
            if not isinstance(item, dict):
                self.err("structure", where, "must be an object")
                continue
            if not (isinstance(ident, str) and re.fullmatch(prefix + r"-\d{2,}", ident)):
                self.err("structure", f"{section}[{n}]", f"'id' must look like {prefix}-01, got {ident!r}")
            elif ident in seen:
                self.err("structure", where, "id is used more than once")
            seen.add(ident)
            expected = required | {"id", "sources"}
            for key in sorted(expected - item.keys()):
                self.err("structure", where, f"missing field '{key}'")
            for key in sorted(item.keys() - expected):
                self.err("structure", where, f"unexpected field '{key}'")
            if section == "audits":
                self.audit(item, where)
            if section == "discrepancies" and isinstance(item.get("sources"), list) \
                    and len(item["sources"]) < 2:
                self.err("structure", where, "a discrepancy cites both places that disagree (2+ sources)")
            self.printed(section, item, where, self.sources(item, where))

    def audit(self, item, where):
        kind = item.get("kind")
        if "kind" in item and kind not in AUDIT_KINDS:
            self.err("structure", where, f"'kind' {kind!r} not in {sorted(AUDIT_KINDS)}")
        if kind != "follow_up" and item.get("follow_up_opinion") is not None:
            self.err("structure", where, "'follow_up_opinion' must be null unless kind is follow_up")
        for key in ("area", "period"):
            if key in item and not (isinstance(item[key], str) and item[key].strip()):
                self.err("structure", where, f"'{key}' must be a non-empty string")

    def scoring(self, seen):
        sm = self.data.get("scoring_method")
        if not isinstance(sm, dict):
            self.err("structure", "scoring_method", "must be an object")
            return None
        for key in sorted(SCORING - sm.keys()):
            self.err("structure", "scoring_method", f"missing field '{key}'")
        for key in sorted(sm.keys() - SCORING):
            self.err("structure", "scoring_method", f"unexpected field '{key}'")
        usable = sm.get("usable")
        if not isinstance(usable, bool):
            self.err("structure", "scoring_method", "'usable' must be true or false")
        for section, (prefix, required) in SCORING_LISTS.items():
            if section in sm:
                self.items(section, sm[section], prefix, required, seen)
        matrix = sm.get("matrix")
        has_matrix = False
        if matrix is not None:
            has_matrix = self.matrix(matrix)
        if usable is True:
            for part in ("likelihood_scale", "impact_scale"):
                if not sm.get(part):
                    self.err("structure", "scoring_method", f"'usable' is true but '{part}' is empty")
            if not has_matrix and not sm.get("bands"):
                self.err("structure", "scoring_method", "'usable' is true but there is neither a matrix nor bands")
            if sm.get("reason_if_not_usable") is not None:
                self.err("structure", "scoring_method", "'reason_if_not_usable' must be null when usable")
        if usable is False and not (isinstance(sm.get("reason_if_not_usable"), str)
                                    and sm["reason_if_not_usable"].strip()):
            self.err("structure", "scoring_method", "'usable' is false: give 'reason_if_not_usable'")
        return usable

    def matrix(self, matrix):
        if not isinstance(matrix, dict) or set(matrix) != {"likelihood_labels", "rows", "sources"}:
            self.err("structure", "matrix", "must be null or have exactly likelihood_labels, rows, sources")
            return False
        text = self.sources(matrix, "matrix")
        labels = matrix["likelihood_labels"]
        if not isinstance(labels, list) or not labels:
            self.err("structure", "matrix", "'likelihood_labels' must be a non-empty list")
            labels = []
        elif text:
            for label in labels:
                if not printed_in(label, text):
                    self.err("printed", "matrix", f"likelihood label {label!r} is not printed in the matrix quotes")
        rows = matrix["rows"]
        if not isinstance(rows, list) or not rows:
            self.err("structure", "matrix", "'rows' must be a non-empty list")
            return False
        for n, row in enumerate(rows):
            where = f"matrix.rows[{n}]"
            if not isinstance(row, dict) or set(row) != MATRIX_ROW | {"sources"}:
                self.err("structure", where, f"must have exactly {sorted(MATRIX_ROW | {'sources'})}")
                continue
            row_text = self.sources(row, where)
            for key in ("scores", "bands"):
                cells = row[key]
                if not isinstance(cells, list) or (labels and len(cells) != len(labels)):
                    self.err("structure", where, f"'{key}' must be a list with one entry per likelihood label")
                elif row_text:
                    for cell in cells:
                        if cell is not None and not printed_in(cell, row_text):
                            self.err("printed", where, f"{key[:-1]} {cell!r} is not printed in this row's quotes")
            if row_text and not printed_in(row["impact_label"], row_text):
                self.err("printed", where, f"impact_label {row['impact_label']!r} is not printed in this row's quotes")
        return True

    def coverage(self, usable):
        listed = {}
        gen = self.data.get("generated_from")
        if not isinstance(gen, list):
            self.err("structure", "generated_from", "must be a list")
            gen = []
        for n, entry in enumerate(gen):
            if not isinstance(entry, dict) or set(entry) != {"file", "pages", "describes"}:
                self.err("structure", f"generated_from[{n}]", "must have exactly file, pages, describes")
                continue
            listed[entry["file"]] = entry["pages"]
        for name in self.pdfs:
            if name not in listed:
                self.err("coverage", name, "PDF is in the folder but not listed in generated_from")
            elif listed[name] != len(self.pages(name)[0]):
                self.err("coverage", name, f"generated_from says {listed[name]!r} pages; the PDF has "
                                           f"{len(self.pages(name)[0])}")
        for name in sorted(set(listed) - set(self.pdfs)):
            self.err("coverage", name, "listed in generated_from but not in the folder")

        topics = set()
        gaps = self.data.get("gaps")
        if not isinstance(gaps, list):
            self.err("structure", "gaps", "must be a list")
            gaps = []
        for n, gap in enumerate(gaps):
            where = f"gaps[{n}]"
            if not isinstance(gap, dict) or set(gap) != {"topic", "expected", "searched", "note"}:
                self.err("structure", where, "must have exactly topic, expected, searched, note")
                continue
            if gap["topic"] not in GAP_TOPICS:
                self.err("structure", where, f"'topic' {gap['topic']!r} not in {sorted(GAP_TOPICS)}")
            if not isinstance(gap["searched"], list) or not gap["searched"] \
                    or set(gap["searched"]) - set(self.pdfs):
                self.err("structure", where, "'searched' must list the PDFs searched, by file name")
            for key in ("expected", "note"):
                if not (isinstance(gap[key], str) and gap[key].strip()):
                    self.err("structure", where, f"'{key}' must be a non-empty string")
            topics.add(gap["topic"])
        if "risk_register" not in topics:
            self.err("coverage", "gaps", "no 'risk_register' gap: the register is exempt and its absence must be recorded")
        if self.data.get("agreed_actions") == [] and "agreed_actions" not in topics:
            self.err("coverage", "gaps", "agreed_actions is empty but there is no 'agreed_actions' gap")
        if usable is False and "scoring_method" not in topics:
            self.err("coverage", "gaps", "scoring_method is not usable but there is no 'scoring_method' gap")

    def run(self):
        if not isinstance(self.data, dict):
            self.err("structure", "top level", "must be an object")
            return
        for key in sorted(TOP - self.data.keys()):
            self.err("structure", "top level", f"missing key '{key}'")
        for key in sorted(self.data.keys() - TOP):
            self.err("structure", "top level", f"unexpected key '{key}'")
        seen = set()
        for section, (prefix, required) in LISTS.items():
            if section in self.data:
                self.items(section, self.data[section], prefix, required, seen)
        usable = self.scoring(seen) if "scoring_method" in self.data else None
        self.coverage(usable)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--history", default="outputs/history.json")
    parser.add_argument("--dir", default="data/committee")
    args = parser.parse_args()

    folder = Path(args.dir)
    if not Path(args.history).is_file():
        print(f"CANNOT RUN: {args.history} not found")
        return 2
    if not folder.is_dir() or not list(folder.glob("*.pdf")):
        print(f"CANNOT RUN: no PDFs in {folder}")
        return 2
    if not shutil.which("pdftotext"):
        print("CANNOT RUN: pdftotext (poppler) is not on PATH")
        return 2
    try:
        data = json.loads(Path(args.history).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"CANNOT RUN: {args.history} is not valid JSON: {exc}")
        return 2

    checker = Checker(data, folder)
    checker.run()
    for line in checker.errors:
        print("ERROR  ", line)
    if isinstance(data, dict):
        sm = data.get("scoring_method") if isinstance(data.get("scoring_method"), dict) else {}
        counts = [f"{len(data[k])} {k}" for k in ("audits", "agreed_actions", "risk_themes",
                                                   "discrepancies", "gaps")
                  if isinstance(data.get(k), list)]
        print(f"{args.history}: " + ", ".join(counts)
              + f"; scoring method usable: {sm.get('usable')!r}; "
                f"{checker.quotes_checked} quotes checked against {len(checker.pdfs)} PDFs")
    print(f"{'FAIL' if checker.errors else 'PASS'}: {len(checker.errors)} errors")
    return 1 if checker.errors else 0


if __name__ == "__main__":
    sys.exit(main())
