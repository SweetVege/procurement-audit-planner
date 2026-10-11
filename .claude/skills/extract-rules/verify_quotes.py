#!/usr/bin/env python3
"""Verify outputs/rules.json against data/contract-rules.pdf.

Checks, in order:
  1. schema      - top-level keys, field names, types and allowed values
  2. rule IDs    - CPR-01, CPR-02, ... in order, no gaps or repeats
  3. parameters  - every named threshold a rule uses is declared, with a null value
  4. quotes      - every verbatim quote appears on its stated PDF page, and every
                   threshold amount is printed inside its rule's quote
  5. coverage    - every numbered clause and every appendix in the PDF is in
                   rules or excluded, and every clause cited exists in the PDF

Usage (from the project root):
  .venv/bin/python .claude/skills/extract-rules/verify_quotes.py
  .venv/bin/python .claude/skills/extract-rules/verify_quotes.py --rules X.json --pdf Y.pdf

Exit code 0 = all checks pass, 1 = at least one error, 2 = cannot run
(missing file, pdftotext not installed, JSON does not parse).
Standard library only; needs pdftotext (poppler) on PATH.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TYPES = {
    "procedure", "advertising", "approval", "waiver", "exclusion",
    "anti-avoidance", "valuation", "record", "contract-form",
}
SCOPES = {"goods", "services", "works", "concession", "light_touch", "all"}
EVIDENCE = {"spend_data", "contract_notices", "council_records"}
NOTE_KINDS = {"contradiction", "gap", "drafting"}

RULE_FIELDS = {
    "rule_id", "clause", "page", "type", "scope", "condition",
    "threshold_low", "threshold_low_inclusive", "threshold_low_param",
    "threshold_high", "threshold_high_inclusive", "threshold_high_param",
    "threshold_text", "required_action", "approver", "evidence_source",
    "verbatim_quote",
}
PARAM_FIELDS = {"value", "defined_in", "page", "description", "verbatim_quote"}
EXCLUDED_FIELDS = {"clause", "page", "reason"}
NOTE_FIELDS = {"kind", "clauses", "description"}
TOP_FIELDS = {"source", "parameters", "rules", "excluded", "notes"}

NUMBERED = re.compile(r"\d{1,2}(?:\.\d{1,2}){1,3}")
APPENDIX = re.compile(r"App ([A-Z]) (?:row [A-Z0-9]+|note \*{1,4}|intro|closing)")
PARAM_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
RULE_ID = re.compile(r"CPR-(\d{2,})")
# Layout mode puts a clause number at the start of a line, then a run of spaces.
CLAUSE_LINE = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){1,3})\s{2,}\S", re.M)
APPENDIX_HEADING = re.compile(r"Appendix ([A-Z])\s*$", re.M)

MIN_QUOTE_CHARS = 10
MAX_REASON_CHARS = 200
BULLET = ""  # Word bullet glyph as pdftotext emits it


def normalise(text):
    """Collapse whitespace and drop bullet glyphs. Nothing else is forgiven."""
    return " ".join(text.replace(BULLET, " ").split())


def pdf_pages(pdf, layout):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + [str(pdf), "-"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        sys.exit(f"CANNOT RUN: pdftotext failed on {pdf}: {out.stderr.strip()}")
    pages = out.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def is_amount(v):
    """Whole pounds as int; a float only where the PDF prints pence."""
    if is_int(v):
        return v >= 0
    return isinstance(v, float) and v >= 0 and v != int(v) and round(v, 2) == v


def printed_forms(amount):
    forms = []
    if is_int(amount):
        forms += [f"£{amount:,}", f"£{amount}"]
        if amount >= 1_000_000 and amount % 100_000 == 0:
            m = f"{amount / 1_000_000:g}"
            forms += [f"£{m}million", f"£{m} million", f"£{m}m"]
    else:
        forms += [f"£{amount:,.2f}", f"£{amount:.2f}"]
    return forms


def amount_printed_in(amount, text):
    return any(
        re.search(re.escape(form) + r"(?![,.]?\d)", text)
        for form in printed_forms(amount)
    )


def valid_clause(ref):
    return isinstance(ref, str) and bool(
        NUMBERED.fullmatch(ref) or APPENDIX.fullmatch(ref)
    )


class Checker:
    def __init__(self, data, plain, layout):
        self.data = data
        self.plain = [normalise(p) for p in plain]
        self.layout = [normalise(p) for p in layout]
        self.raw_layout = layout
        self.errors = []
        self.warnings = []

    def err(self, check, where, msg):
        self.errors.append(f"[{check}] {where}: {msg}")

    def warn(self, check, where, msg):
        self.warnings.append(f"[{check}] {where}: {msg}")

    # -- helpers ---------------------------------------------------------
    def fields(self, obj, expected, where):
        """Exact field set. Returns False if obj is unusable."""
        if not isinstance(obj, dict):
            self.err("schema", where, "must be an object")
            return False
        for key in sorted(expected - obj.keys()):
            self.err("schema", where, f"missing field '{key}'")
        for key in sorted(obj.keys() - expected):
            self.err("schema", where, f"unexpected field '{key}'")
        return True

    def text(self, obj, key, where):
        value = obj.get(key)
        if key in obj and not (isinstance(value, str) and value.strip()):
            self.err("schema", where, f"'{key}' must be a non-empty string")

    def page(self, obj, where):
        """Returns the page number if it is usable, else None."""
        if "page" not in obj:
            return None
        page = obj["page"]
        if not is_int(page) or not 1 <= page <= len(self.plain):
            self.err("schema", where,
                     f"'page' must be an integer 1-{len(self.plain)}, got {page!r}")
            return None
        return page

    def clause(self, ref, where, key="clause"):
        if not valid_clause(ref):
            self.err("schema", where,
                     f"'{key}' {ref!r} is not a clause reference (use '6.16', "
                     "'App B row B1', 'App B note ***', 'App C intro', 'App C closing')")
            return False
        return True

    def quote(self, obj, page, where):
        quote = obj.get("verbatim_quote")
        if not isinstance(quote, str) or page is None:
            return
        wanted = normalise(quote)
        if len(wanted) < MIN_QUOTE_CHARS:
            self.err("quotes", where,
                     f"quote is shorter than {MIN_QUOTE_CHARS} characters")
            return
        if wanted in self.plain[page - 1] or wanted in self.layout[page - 1]:
            return
        elsewhere = [n + 1 for n in range(len(self.plain))
                     if wanted in self.plain[n] or wanted in self.layout[n]]
        if elsewhere:
            self.err("quotes", where,
                     f"quote is not on page {page}; it is on page "
                     f"{', '.join(map(str, elsewhere))}")
        else:
            self.err("quotes", where,
                     f"quote not found on page {page} or any other page: "
                     f"\"{wanted[:70]}{'...' if len(wanted) > 70 else ''}\"")

    # -- checks ----------------------------------------------------------
    def check_top(self):
        if not self.fields(self.data, TOP_FIELDS, "top level"):
            return False
        ok = True
        for key, kind in (("parameters", dict), ("rules", list),
                          ("excluded", list), ("notes", list)):
            if key in self.data and not isinstance(self.data[key], kind):
                self.err("schema", "top level",
                         f"'{key}' must be {'an object' if kind is dict else 'a list'}")
                ok = False
        source = self.data.get("source")
        if self.fields(source, {"file", "pages"}, "source"):
            self.text(source, "file", "source")
            if "pages" in source and source["pages"] != len(self.plain):
                self.err("schema", "source",
                         f"'pages' is {source['pages']!r} but the PDF has "
                         f"{len(self.plain)} pages")
        return ok

    def check_parameters(self):
        params = self.data.get("parameters", {})
        for name, body in params.items():
            where = f"parameters.{name}"
            if not PARAM_NAME.fullmatch(name):
                self.err("parameters", where, "name must be UPPER_SNAKE_CASE")
            if not self.fields(body, PARAM_FIELDS, where):
                continue
            if "value" in body and body["value"] is not None:
                self.err("parameters", where,
                         f"'value' must be null (the PDF names this threshold "
                         f"without printing it), got {body['value']!r}")
            if "defined_in" in body:
                self.clause(body["defined_in"], where, "defined_in")
            self.text(body, "description", where)
            self.text(body, "verbatim_quote", where)
            self.quote(body, self.page(body, where), where)
        return params

    def check_bound(self, rule, side, quote, params, where):
        amount = rule.get(f"threshold_{side}")
        param = rule.get(f"threshold_{side}_param")
        inclusive = rule.get(f"threshold_{side}_inclusive")
        if amount is not None and not is_amount(amount):
            self.err("schema", where,
                     f"'threshold_{side}' must be a GBP integer (or pounds.pence "
                     f"only where the PDF prints pence) or null, got {amount!r}")
            amount = None
        if param is not None and not isinstance(param, str):
            self.err("schema", where, f"'threshold_{side}_param' must be a string or null")
            param = None
        if amount is not None and param is not None:
            self.err("schema", where,
                     f"threshold_{side} has both an amount and a parameter; use one")
        present = amount is not None or param is not None
        if present and not isinstance(inclusive, bool):
            self.err("schema", where,
                     f"'threshold_{side}_inclusive' must be true or false when "
                     "the bound is set")
        if not present and inclusive is not None:
            self.err("schema", where,
                     f"'threshold_{side}_inclusive' must be null when the bound is open")
        if param is not None and param not in params:
            self.err("parameters", where,
                     f"threshold_{side}_param '{param}' is not declared in parameters")
        if amount is not None and isinstance(quote, str) \
                and not amount_printed_in(amount, normalise(quote)):
            self.err("quotes", where,
                     f"threshold_{side} {amount:,} is not printed in the rule's "
                     "verbatim_quote; never supply an amount the quote does not show")
        return amount, param

    def check_rules(self, params):
        used = set()
        for index, rule in enumerate(self.data.get("rules", [])):
            expected_id = f"CPR-{index + 1:02d}"
            rule_id = rule.get("rule_id") if isinstance(rule, dict) else None
            where = rule_id if isinstance(rule_id, str) else f"rules[{index}]"
            if not self.fields(rule, RULE_FIELDS, where):
                continue
            if rule_id != expected_id:
                detail = "" if isinstance(rule_id, str) and RULE_ID.fullmatch(rule_id) \
                    else " (format is CPR-NN)"
                self.err("rule IDs", f"rules[{index}]",
                         f"expected {expected_id}, got {rule_id!r}{detail}")
            if "clause" in rule:
                self.clause(rule["clause"], where)
            if "type" in rule and rule["type"] not in TYPES:
                self.err("schema", where,
                         f"'type' {rule['type']!r} not in {sorted(TYPES)}")
            self.check_list(rule, "scope", SCOPES, where)
            scope = rule.get("scope")
            if isinstance(scope, list) and "all" in scope and len(scope) > 1:
                self.err("schema", where, "'scope' must be [\"all\"] alone or a list of categories")
            self.check_list(rule, "evidence_source", EVIDENCE, where)
            for key in ("condition", "required_action", "verbatim_quote"):
                self.text(rule, key, where)
            approver = rule.get("approver")
            if approver is not None and not (isinstance(approver, str) and approver.strip()):
                self.err("schema", where, "'approver' must be a non-empty string or null")

            quote = rule.get("verbatim_quote")
            low, low_param = self.check_bound(rule, "low", quote, params, where)
            high, high_param = self.check_bound(rule, "high", quote, params, where)
            used.update(p for p in (low_param, high_param) if p)
            bounded = any(v is not None for v in (low, low_param, high, high_param))
            threshold_text = rule.get("threshold_text")
            if bounded and not (isinstance(threshold_text, str) and threshold_text.strip()):
                self.err("schema", where,
                         "'threshold_text' must give the value band as printed "
                         "when a bound is set")
            if not bounded and threshold_text is not None:
                self.err("schema", where,
                         "'threshold_text' must be null when no bound is set")
            if low is not None and high is not None and low > high:
                self.err("schema", where, "threshold_low is greater than threshold_high")

            self.quote(rule, self.page(rule, where), where)
        for name in sorted(params.keys() - used):
            self.warn("parameters", f"parameters.{name}", "declared but no rule uses it")

    def check_list(self, obj, key, allowed, where):
        value = obj.get(key)
        if key not in obj:
            return
        if not isinstance(value, list) or not value \
                or not all(isinstance(v, str) for v in value):
            self.err("schema", where, f"'{key}' must be a non-empty list of strings")
        elif set(value) - allowed:
            self.err("schema", where,
                     f"'{key}' has {sorted(set(value) - allowed)}; allowed: {sorted(allowed)}")
        elif len(set(value)) != len(value):
            self.err("schema", where, f"'{key}' repeats a value")

    def check_excluded(self):
        seen = set()
        for index, item in enumerate(self.data.get("excluded", [])):
            where = f"excluded[{index}]"
            if not self.fields(item, EXCLUDED_FIELDS, where):
                continue
            clause = item.get("clause")
            if "clause" in item and self.clause(clause, where):
                where = f"excluded[{index}] ({clause})"
                if clause in seen:
                    self.err("schema", where, "clause is excluded more than once")
                seen.add(clause)
            self.page(item, where)
            reason = item.get("reason")
            if "reason" in item and not (
                    isinstance(reason, str) and reason.strip()
                    and "\n" not in reason and len(reason) <= MAX_REASON_CHARS):
                self.err("schema", where,
                         f"'reason' must be one line of 1-{MAX_REASON_CHARS} characters")

    def check_notes(self):
        for index, note in enumerate(self.data.get("notes", [])):
            where = f"notes[{index}]"
            if not self.fields(note, NOTE_FIELDS, where):
                continue
            if "kind" in note and note["kind"] not in NOTE_KINDS:
                self.err("schema", where,
                         f"'kind' {note['kind']!r} not in {sorted(NOTE_KINDS)}")
            clauses = note.get("clauses")
            if "clauses" in note:
                if not isinstance(clauses, list) or not clauses:
                    self.err("schema", where, "'clauses' must be a non-empty list")
                else:
                    for ref in clauses:
                        self.clause(ref, where, "clauses")
            self.text(note, "description", where)

    def check_coverage(self):
        """Every clause in the PDF is in rules or excluded; every clause cited exists."""
        layout_text = "\n".join(self.raw_layout)
        in_pdf = set(CLAUSE_LINE.findall(layout_text))
        appendices = set(APPENDIX_HEADING.findall(layout_text))

        def refs(items, key="clause"):
            return [i[key] for i in items
                    if isinstance(i, dict) and valid_clause(i.get(key))]

        rule_refs = set(refs(self.data.get("rules", [])))
        excluded_refs = set(refs(self.data.get("excluded", [])))
        for ref in sorted(rule_refs & excluded_refs):
            self.err("coverage", ref, "clause is in both rules and excluded")
        placed = rule_refs | excluded_refs

        note_refs = {r for n in self.data.get("notes", []) if isinstance(n, dict)
                     and isinstance(n.get("clauses"), list)
                     for r in n["clauses"] if valid_clause(r)}
        param_refs = set(refs(self.data.get("parameters", {}).values(), "defined_in"))
        for ref in sorted(placed | note_refs | param_refs):
            if NUMBERED.fullmatch(ref):
                if ref not in in_pdf:
                    self.err("coverage", ref, "clause number does not exist in the PDF")
            elif APPENDIX.fullmatch(ref).group(1) not in appendices:
                self.err("coverage", ref, "the PDF has no such appendix")

        # A clause is covered by itself, by an ancestor (an entry for 10.7 covers
        # 10.7.1) or by a descendant (entries for 7.4.1-7.4.3 cover the 7.4 lead-in).
        numbered = {r for r in placed if NUMBERED.fullmatch(r)}

        def covered(clause):
            return any(p == clause or clause.startswith(p + ".")
                       or p.startswith(clause + ".") for p in numbered)

        def order(clause):
            return [int(part) for part in clause.split(".")]

        for clause in sorted(in_pdf, key=order):
            if not covered(clause):
                self.err("coverage", clause, "clause is in neither rules nor excluded")
        for letter in sorted(appendices):
            if not any(r.startswith(f"App {letter} ") for r in placed):
                self.err("coverage", f"App {letter}",
                         "appendix has no entry in rules or excluded")
        return len(in_pdf), len(appendices)

    def run(self):
        if self.check_top():
            params = self.check_parameters()
            self.check_rules(params)
            self.check_excluded()
            self.check_notes()
            return self.check_coverage()
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--rules", default="outputs/rules.json")
    parser.add_argument("--pdf", default="data/contract-rules.pdf")
    args = parser.parse_args()

    for path in (args.rules, args.pdf):
        if not Path(path).is_file():
            print(f"CANNOT RUN: {path} not found")
            return 2
    if not shutil.which("pdftotext"):
        print("CANNOT RUN: pdftotext (poppler) is not on PATH")
        return 2
    try:
        data = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"CANNOT RUN: {args.rules} is not valid JSON: {exc}")
        return 2

    checker = Checker(data, pdf_pages(args.pdf, False), pdf_pages(args.pdf, True))
    counts = checker.run()

    for line in checker.errors:
        print("ERROR  ", line)
    for line in checker.warnings:
        print("WARNING", line)
    if isinstance(data, dict) and counts:
        sizes = {k: len(data[k]) for k in ("rules", "excluded", "notes", "parameters")
                 if isinstance(data.get(k), (list, dict))}
        print(f"{args.rules}: " + ", ".join(f"{n} {k}" for k, n in sizes.items())
              + f"; PDF has {len(checker.plain)} pages, {counts[0]} numbered clauses, "
                f"{counts[1]} appendices")
    verdict = "FAIL" if checker.errors else "PASS"
    print(f"{verdict}: {len(checker.errors)} errors, {len(checker.warnings)} warnings")
    return 1 if checker.errors else 0


if __name__ == "__main__":
    sys.exit(main())
