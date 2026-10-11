#!/usr/bin/env python3
"""Build the audit planning pack from outputs/audit-plan.json.

The planner supplies judgments (audit-plan.json). This script supplies the
scope, every sample and every number:
  - computes the approved scope from auditor-comments.md and risk-ratings.json,
    and fails if any register risk is undecided or the register is not a
    revision (--gate runs only this check);
  - resolves every [rule:ID], [metric:$.path] and [history:ID] citation and
    fills every {{$.path}} and {{pack.name}} placeholder;
  - draws every sample deterministically from outputs/analytics-full/, checks
    that each transaction exists in spend-clean.csv and writes
    outputs/samples/<test>.csv;
  - checks every approved risk has controls and tests, every control cites a
    rule and has a test, every test cites a rule or metric and names its PBC
    items, and every rule in rules.json is cited by a risk, control or test or
    listed as not tested with a reason;
  - renders planning-memo.md, risk-control-matrix.md and audit-program.md, and
    writes pack-figures.json listing every figure it filled or computed.

Usage (from the project root):
  .venv/bin/python .claude/skills/audit-program/build_pack.py --gate
  .venv/bin/python .claude/skills/audit-program/build_pack.py
  ... build_pack.py --outputs DIR      (all inputs and outputs live in DIR)

Exit code 0 = gate closed / pack written, 1 = failed (nothing written),
2 = cannot run. Standard library only.
"""
import argparse
import csv
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "build_register", Path(__file__).resolve().parent.parent / "risk-assessment" / "build_register.py")
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

IN_SCOPE = ("approve", "revise", "override")
# Sample size by the risk's score: (minimum score, items). Method parameters, not data.
SIZE_BY_SCORE = ((15, 25), (8, 15), (4, 10), (1, 5))
CENSUS_LIMIT = 50                      # "all" is allowed only up to this many items
ROW_ID_COLUMNS = ("row_id", "row_ids", "largest_payment_row_ids")
SPEND_COLUMNS = ("row_id", "source_file", "sheet_row", "pay_date", "Net amount", "Supplier name",
                 "Service", "Expenditure category", "Narrative", "tag")
OPS = ("==", "!=", ">=", "<=", ">", "<", "in", "contains")
MEMO_FIELDS = ("objective", "scope", "approach", "limitations")
PACK_PLACEHOLDER = re.compile(r"\{\{\s*pack\.([a-z_]+)\s*\}\}")
ID = {"control": re.compile(r"C-\d{2}\.\d+"), "test": re.compile(r"T-\d{2}\.\d+"), "pbc": re.compile(r"P-\d{2,}")}


def number(text):
    try:
        return float(str(text).replace(",", ""))
    except ValueError:
        return None


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def gate(out):
    """Scope check. Returns (errors, info). info has ratings, decisions, general, title."""
    errors, info = [], {}
    paths = {n: out / n for n in ("risk-ratings.json", "auditor-comments.md", "risk-register.md",
                                  "risk-register.state.json")}
    for name, p in paths.items():
        if not p.is_file():
            errors.append(f"{p} not found: run the risk-assessor first")
    if errors:
        return errors, info
    ratings = br.load(paths["risk-ratings.json"], "risk ratings")
    state = br.load(paths["risk-register.state.json"], "register state")
    decisions, general, bad = br.read_comments(paths["auditor-comments.md"])
    errors += bad
    last = state.get("last_build") or {}
    registered = last.get("risks") or []
    heading = paths["risk-register.md"].read_text(encoding="utf-8").splitlines()[0]
    revision = (ratings.get("revision") or {}).get("number")
    if last.get("mode") != "revision" or not br.is_int(revision) or "Revision" not in heading:
        errors.append("the register is not yet a revision: the auditor completes auditor-comments.md "
                      "and the risk-assessor is re-run")
    undecided = [rid for rid in registered if not decisions.get(rid, ("", ""))[0]]
    if undecided:
        errors.append(f"{len(undecided)} risk(s) have no auditor decision: {', '.join(undecided)}")
    built = last.get("decisions") or {}
    stale = [rid for rid in registered if built.get(rid, "") != decisions.get(rid, ("", ""))[0]]
    if stale and not undecided:
        errors.append(f"decisions for {', '.join(stale)} changed after the register was built: "
                      "re-run the risk-assessor so the register shows them")
    if last.get("dropped"):
        errors.append(f"the register build dropped {', '.join(last['dropped'])}; the risk-assessor must resolve that")
    raw = {r["risk_id"]: r for r in ratings.get("risks", []) if isinstance(r, dict) and "risk_id" in r}
    missing = [rid for rid in registered if rid not in raw]
    if missing:
        errors.append(f"risk-ratings.json no longer holds {', '.join(missing)}")
    info.update(ratings=ratings, raw=raw, decisions=decisions, general=general, registered=registered,
                title=heading.split("—")[-1].strip() if "—" in heading else heading.lstrip("# "),
                scope=[rid for rid in registered if decisions.get(rid, ("", ""))[0] in IN_SCOPE],
                rejected=[rid for rid in registered if decisions.get(rid, ("", ""))[0] == "reject"])
    return errors, info


class Pack:
    def __init__(self, out, info, plan):
        self.out, self.info, self.plan = out, info, plan
        self.rules = {r["rule_id"]: r for r in br.load(out / "rules.json", "rules").get("rules", [])}
        self.analytics = br.load(out / "analytics.json", "analytics")
        history = br.load(out / "history.json", "history")
        self.helper = br.Builder({"risks": []}, {"rules": list(self.rules.values())}, self.analytics, history)
        self.method = self.helper.method
        self.errors, self.warnings, self.figures = [], [], []
        self.full = out / "analytics-full"
        self.spend = {}
        self.pack = {}
        self.rule_use = {}        # rule_id -> set of places citing it
        self.samples = {}         # test_id -> dict

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    # -- text ------------------------------------------------------------
    def text(self, value, where, cited=None):
        """Resolve citations and placeholders; any that fail are errors."""
        if not isinstance(value, str) or not value.strip():
            self.err(where, "text is empty")
            return ""
        problems, cites = [], []

        def pack(m):
            name = m.group(1)
            if name not in self.pack:
                problems.append(f"placeholder {{{{pack.{name}}}}} is not available here "
                                f"(pack figures can be used in the memo only: {sorted(self.pack) or 'none yet'})")
                return m.group(0)
            self.figures.append({"where": where, "source": f"computed: pack.{name}", "value": self.pack[name]["value"],
                                 "shown_as": self.pack[name]["shown_as"]})
            return self.pack[name]["shown_as"]

        for m in br.PLACEHOLDER.finditer(value):
            found, v = br.resolve(self.analytics, m.group(1))
            if found and not isinstance(v, (dict, list, bool)) and v is not None:
                self.figures.append({"where": where, "source": f"analytics.json {m.group(1)}", "value": v,
                                     "shown_as": br.fmt(v, m.group(1), m.group(2))[0]})
        self.helper.warnings.clear()
        out = self.helper.render(PACK_PLACEHOLDER.sub(pack, value), problems, cites)
        problems += self.helper.warnings          # an unresolved citation is an error in the pack
        self.helper.warnings.clear()
        self.helper.typed_figures(where, "text", PACK_PLACEHOLDER.sub(" ", value))
        self.warnings += self.helper.warnings
        self.helper.warnings.clear()
        for problem in problems:
            self.err(where, problem)
        for kind, ident in cites:
            if kind == "rule":
                self.rule_use.setdefault(ident, set()).add(where.split()[0])
        if cited is not None:
            cited.extend(cites)
        return out

    def rating(self, rid):
        r = self.info["raw"][rid]
        l, i = r["likelihood"]["score"], r["impact"]["score"]
        rate = self.method.rate(l, i)
        rate.update(l=l, i=i, l_label=self.method.likelihood[l], i_label=self.method.impact[i])
        rate["text"] = (f"{rate['l_label']} ({l}) × {rate['i_label']} ({i}) = {rate['score']}"
                        + (f" {rate['matrix_label']}" if rate["matrix_label"] else ""))
        return rate

    # -- samples -----------------------------------------------------------
    def load_spend(self):
        path = self.full / "spend-clean.csv"
        if not path.is_file():
            self.err("samples", f"{path} not found")
            return
        _, rows = read_csv(path)
        self.spend = {r["row_id"]: r for r in rows}
        self.by_supplier = {}
        for r in rows:
            self.by_supplier.setdefault(r.get("supplier_norm", ""), []).append(r)

    def keep(self, row, cond, where):
        value, op, want = row.get(cond["column"], ""), cond["op"], cond["value"]
        if op == "in":
            return value in [str(w) for w in want] or (number(value) is not None and number(value) in
                                                       [w for w in want if isinstance(w, (int, float))])
        if op == "contains":
            return str(want).lower() in value.lower()
        if isinstance(want, bool):
            same = value.strip().lower() == str(want).lower()
            return same if op == "==" else not same
        if isinstance(want, (int, float)):
            n = number(value)
            if n is None:
                return False
            return {"==": n == want, "!=": n != want, ">=": n >= want, "<=": n <= want,
                    ">": n > want, "<": n < want}[op]
        return {"==": value == want, "!=": value != want}.get(op, False)

    def draw(self, test, rid, score, where):
        s = test.get("sample")
        allowed = {"file", "filter", "sort", "size", "transactions", "per_item_limit", "keep", "rows_column"}
        if not isinstance(s, dict) or set(s) - allowed:
            self.err(where, f"'sample' must be an object with fields from {sorted(allowed)}")
            return None
        path = self.full / str(s.get("file", ""))
        if "/" in str(s.get("file", "")) or not str(s.get("file", "")).endswith(".csv") or not path.is_file():
            self.err(where, f"sample.file {s.get('file')!r} is not a CSV in {self.full}")
            return None
        columns, rows = read_csv(path)
        for cond in s.get("filter") or []:
            if not isinstance(cond, dict) or set(cond) != {"column", "op", "value"} or cond["op"] not in OPS:
                self.err(where, f"filter entry {cond!r} needs column, op (one of {', '.join(OPS)}) and value")
                return None
            if cond["column"] not in columns:
                self.err(where, f"filter column {cond['column']!r} is not in {s['file']} ({', '.join(columns)})")
                return None
            if cond["op"] in (">=", "<=", ">", "<") and not isinstance(cond["value"], (int, float)):
                self.err(where, f"filter {cond['column']} {cond['op']} needs a number")
                return None
            rows = [r for r in rows if self.keep(r, cond, where)]
        if not rows:
            self.err(where, f"the filter leaves no rows in {s['file']}; a test cannot sample an empty population")
            return None
        sort = s.get("sort") or []
        if not sort:
            self.err(where, "sample.sort is required so the draw is deterministic")
            return None
        for key in reversed(sort):
            if not isinstance(key, dict) or key.get("column") not in columns or key.get("order") not in ("asc", "desc"):
                self.err(where, f"sort entry {key!r} needs a column of {s['file']} and order asc or desc")
                return None
            numeric = all(number(r[key["column"]]) is not None for r in rows)
            rows.sort(key=(lambda r, c=key["column"]: number(r[c])) if numeric else (lambda r, c=key["column"]: r[c]),
                      reverse=key["order"] == "desc")
        population = len(rows)
        if s.get("size") == "by_score":
            size = next(n for low, n in SIZE_BY_SCORE if score >= low)
            basis = f"by score ({score}): up to {size}"
        elif s.get("size") == "all":
            if population > CENSUS_LIMIT:
                self.err(where, f"size 'all' would take {population} items; the limit for a census is {CENSUS_LIMIT}")
                return None
            size, basis = population, "all items (census)"
        else:
            self.err(where, "sample.size must be \"by_score\" or \"all\"")
            return None
        chosen = rows[:size]
        id_col = s.get("rows_column") or next((c for c in ROW_ID_COLUMNS if c in columns), None)
        mode = s.get("transactions", "listed")
        if mode not in ("listed", "supplier_all") or (mode == "listed" and id_col not in columns) \
                or (mode == "supplier_all" and "supplier_norm" not in columns):
            self.err(where, f"cannot find transactions for {s['file']}: transactions={mode!r}, row id column {id_col!r}")
            return None
        keep = s.get("keep") or []
        if any(c not in columns for c in keep):
            self.err(where, f"sample.keep has columns not in {s['file']}: {[c for c in keep if c not in columns]}")
            return None
        limit = s.get("per_item_limit")
        if limit is not None and not (br.is_int(limit) and limit > 0):
            self.err(where, "sample.per_item_limit must be a positive integer")
            return None
        out_rows, missing = [], []
        for n, item in enumerate(chosen, 1):
            if mode == "listed":
                ids = [i.strip() for i in item[id_col].split(";") if i.strip()]
                found = [self.spend[i] for i in ids if i in self.spend]
                missing += [i for i in ids if i not in self.spend]
            else:
                found = list(self.by_supplier.get(item["supplier_norm"], []))
                if not found:
                    missing.append(f"(no payments for supplier_norm {item['supplier_norm']!r})")
            if limit:
                found = sorted(found, key=lambda r: (-(number(r["Net amount"]) or 0), r["row_id"]))[:limit]
            for r in found:
                row = {"test_id": test["test_id"], "risk_id": rid, "item_no": n}
                row.update({f"item_{c}": item[c] for c in keep})
                row.update({c: r.get(c, "") for c in SPEND_COLUMNS})
                out_rows.append(row)
        if missing:
            self.err(where, f"{len(missing)} sampled transaction(s) are not in spend-clean.csv, e.g. {missing[:3]}")
            return None
        if not out_rows:
            self.err(where, "the sample holds no transactions")
            return None
        gbp = round(sum(number(r["Net amount"]) or 0 for r in out_rows), 2)
        return {"file": s["file"], "filter": s.get("filter") or [], "sort": sort, "basis": basis, "mode": mode,
                "per_item_limit": limit, "population": population, "items": len(chosen),
                "transactions": len(out_rows), "gbp": gbp, "rows": out_rows,
                "header": ["test_id", "risk_id", "item_no"] + [f"item_{c}" for c in keep] + list(SPEND_COLUMNS),
                "csv": f"samples/{test['test_id']}.csv"}

    # -- structure ---------------------------------------------------------
    def check(self):
        plan, info = self.plan, self.info
        for key in sorted({"memo", "risks", "pbc", "rules_not_tested"} - plan.keys()):
            self.err("audit-plan.json", f"missing key '{key}'")
        for key in sorted(plan.keys() - {"memo", "risks", "pbc", "rules_not_tested"}):
            self.err("audit-plan.json", f"unexpected key '{key}'")
        if self.errors:
            return
        self.load_spend()
        planned = {r.get("risk_id"): r for r in plan["risks"] if isinstance(r, dict)}
        for rid in info["scope"]:
            if rid not in planned:
                self.err(rid, "approved by the auditor but missing from audit-plan.json")
        for rid in planned:
            if rid not in info["scope"]:
                why = "rejected by the auditor" if rid in info["rejected"] else "not in the register"
                self.err(str(rid), f"is in audit-plan.json but is {why}; plan only auditor-approved risks")
        self.pbc = {}
        for n, p in enumerate(plan["pbc"]):
            pid = p.get("pbc_id") if isinstance(p, dict) else None
            if not (isinstance(pid, str) and ID["pbc"].fullmatch(pid)) or set(p) != {"pbc_id", "request"}:
                self.err(f"pbc[{n}]", "needs exactly pbc_id (P-01) and request")
            elif pid in self.pbc:
                self.err(pid, "pbc_id is used more than once")
            else:
                self.pbc[pid] = {"request_raw": p["request"], "tests": []}
        seen, self.rows = set(), []
        for rid in info["scope"]:
            risk = planned.get(rid)
            if not risk:
                continue
            if set(risk) != {"risk_id", "controls", "tests"}:
                self.err(rid, "needs exactly risk_id, controls, tests")
                continue
            rate = self.rating(rid)
            controls, tests = {}, []
            if not isinstance(risk["controls"], list) or not risk["controls"]:
                self.err(rid, "has no expected control")
            if not isinstance(risk["tests"], list) or not risk["tests"]:
                self.err(rid, "has no test step")
            prefix = rid[2:]
            for c in risk["controls"] or []:
                cid = c.get("control_id") if isinstance(c, dict) else None
                where = cid if isinstance(cid, str) else f"{rid} control"
                if not isinstance(c, dict) or set(c) != {"control_id", "control", "rules"} \
                        or not (isinstance(cid, str) and ID["control"].fullmatch(cid) and cid.startswith(f"C-{prefix}.")):
                    self.err(where, f"a control needs control_id (C-{prefix}.1), control and rules")
                    continue
                if cid in seen:
                    self.err(cid, "control_id is used more than once")
                seen.add(cid)
                rules = c["rules"] if isinstance(c["rules"], list) else []
                if not rules:
                    self.err(cid, "control cites no rule; an expected control must come from the Rules")
                for rule in rules:
                    if rule not in self.rules:
                        self.err(cid, f"cites {rule!r}, which is not a rule in rules.json")
                    else:
                        self.rule_use.setdefault(rule, set()).add(cid)
                controls[cid] = {"text": self.text(c["control"], f"{cid} control"), "tests": [],
                                 "rules": [r for r in rules if r in self.rules]}
            for t in risk["tests"] or []:
                tid = t.get("test_id") if isinstance(t, dict) else None
                where = tid if isinstance(tid, str) else f"{rid} test"
                fields = {"test_id", "controls", "step", "sample", "no_sample_reason", "pbc"}
                if not isinstance(t, dict) or set(t) != fields \
                        or not (isinstance(tid, str) and ID["test"].fullmatch(tid) and tid.startswith(f"T-{prefix}.")):
                    self.err(where, f"a test needs exactly {sorted(fields)} with test_id like T-{prefix}.1")
                    continue
                if tid in seen:
                    self.err(tid, "test_id is used more than once")
                seen.add(tid)
                cites = []
                step = self.text(t["step"], f"{tid} step", cites)
                if not any(kind in ("rule", "metric") for kind, _ in cites):
                    self.err(tid, "test step cites no rule and no metric")
                linked = t["controls"] if isinstance(t["controls"], list) else []
                if not linked:
                    self.err(tid, "test is linked to no control")
                for cid in linked:
                    if cid not in controls:
                        self.err(tid, f"is linked to {cid!r}, which is not a control of {rid}")
                    else:
                        controls[cid]["tests"].append(tid)
                needs = t["pbc"] if isinstance(t["pbc"], list) else []
                if not needs:
                    self.err(tid, "names no PBC item; say what the council must provide for this test")
                for pid in needs:
                    if pid not in self.pbc:
                        self.err(tid, f"needs {pid!r}, which is not in the pbc list")
                    else:
                        self.pbc[pid]["tests"].append(tid)
                sample, reason = None, None
                if t["sample"] is None:
                    reason = self.text(t["no_sample_reason"], f"{tid} no_sample_reason") \
                        if t["no_sample_reason"] else self.err(tid, "has no sample and no no_sample_reason")
                else:
                    if t["no_sample_reason"] is not None:
                        self.err(tid, "has both a sample and a no_sample_reason")
                    sample = self.draw(t, rid, rate["score"], f"{tid} sample") if self.spend else None
                    if sample:
                        self.samples[tid] = sample
                tests.append({"id": tid, "step": step, "controls": linked, "pbc": needs,
                              "sample": sample, "reason": reason})
            for cid, c in controls.items():
                if not c["tests"]:
                    self.err(cid, "control has no test")
            self.rows.append({"risk_id": rid, "title": info["raw"][rid]["title"], "rate": rate,
                              "decision": info["decisions"][rid], "controls": controls, "tests": tests})
        for pid, p in self.pbc.items():
            if not p["tests"]:
                self.err(pid, "PBC item is not needed by any test")
        self.rule_coverage()

    def rule_coverage(self):
        for rid in self.info["scope"]:
            r = self.info["raw"][rid]
            texts = [r["description"], r["proposed_focus"], r["likelihood"]["justification"],
                     r["impact"]["justification"]] + list(r["evidence"])
            for text in texts:
                for m in br.CITE.finditer(text):
                    if m.group(1) == "rule" and m.group(2) in self.rules:
                        self.rule_use.setdefault(m.group(2), set()).add(rid)
        self.not_tested = {}
        for n, entry in enumerate(self.plan["rules_not_tested"]):
            if not isinstance(entry, dict) or set(entry) != {"rule_ids", "reason"} \
                    or not isinstance(entry["rule_ids"], list) or not entry["rule_ids"]:
                self.err(f"rules_not_tested[{n}]", "needs rule_ids (a list) and reason")
                continue
            reason = self.text(entry["reason"], f"rules_not_tested[{n}] reason")
            for rule in entry["rule_ids"]:
                if rule not in self.rules:
                    self.err(f"rules_not_tested[{n}]", f"{rule!r} is not a rule in rules.json")
                elif rule in self.not_tested:
                    self.err(rule, "is listed as not tested more than once")
                else:
                    self.not_tested[rule] = reason
        for rule in self.rules:
            used = {u for u in self.rule_use.get(rule, ()) if u[:2] in ("R-", "C-", "T-")}
            if used and rule in self.not_tested:
                self.err(rule, f"is listed as not tested but is cited by {', '.join(sorted(used))}")
            if not used and rule not in self.not_tested:
                self.err(rule, f"(cl. {self.rules[rule]['clause']}) is not cited by any approved risk, control or "
                               "test and is not listed in rules_not_tested with a reason")
        self.rule_use = {k: {u for u in v if u[:2] in ("R-", "C-", "T-")} for k, v in self.rule_use.items()}

    def compute(self):
        def put(name, value, money=False):
            shown = (f"£{value:,.2f}" if money else f"{value:,}")
            self.pack[name] = {"value": value, "shown_as": shown}
        put("risks_in_register", len(self.info["registered"]))
        put("risks_in_scope", len(self.info["scope"]))
        put("risks_rejected", len(self.info["rejected"]))
        put("controls", sum(len(r["controls"]) for r in self.rows))
        put("tests", sum(len(r["tests"]) for r in self.rows))
        put("tests_with_sample", len(self.samples))
        put("sample_items", sum(s["items"] for s in self.samples.values()))
        put("sample_transactions", sum(s["transactions"] for s in self.samples.values()))
        put("sample_gbp", round(sum(s["gbp"] for s in self.samples.values()), 2), money=True)
        put("pbc_items", len(self.pbc))
        put("rules_total", len(self.rules))
        put("rules_cited", sum(1 for r in self.rules if self.rule_use.get(r)))
        put("rules_not_tested", len(self.not_tested))

    # -- rendering ---------------------------------------------------------
    def render(self, built_at):
        info = self.info
        memo = self.plan["memo"]
        if not isinstance(memo, dict) or set(memo) != set(MEMO_FIELDS):
            self.err("memo", f"needs exactly {', '.join(MEMO_FIELDS)}")
            return {}
        parts = {k: self.text(memo[k], f"memo {k}") for k in MEMO_FIELDS}
        for pid, p in self.pbc.items():
            p["request"] = self.text(p["request_raw"], f"{pid} request")
        banner = ("> This pack plans work on **risk indicators to investigate**, drawn from public data. Nothing in it "
                  "is a finding of wrongdoing by the council, a service, an officer or a supplier.")
        basis = (f"Built {built_at} from the risk register **{info['title']}** and the auditor's decisions in "
                 "`auditor-comments.md`.")
        M = ["# Planning memo: procurement audit", "", banner, "", basis, "",
             "## Objective", "", parts["objective"], "", "## Scope", "", parts["scope"], "",
             "### Risks in scope (auditor's decisions)", "",
             "| Risk | Title | Rating | Auditor decision | Tests |", "| --- | --- | --- | --- | --- |"]
        for r in self.rows:
            M.append(f"| {r['risk_id']} | {r['title']} | {r['rate']['text']} | {r['decision'][0]} "
                     f"| {', '.join(t['id'] for t in r['tests'])} |")
        M += ["", "### Out of scope", ""]
        if not info["rejected"]:
            M.append("The auditor rejected no risk.")
        for rid in info["rejected"]:
            comment = info["decisions"][rid][1]
            M.append(f"- **{rid} {info['raw'][rid]['title']}**: rejected by the auditor."
                     + (f" “{comment}”" if comment else ""))
        M += ["", "## Approach", "", parts["approach"], "",
              "### Samples", "",
              "Samples are targeted at the flagged items, not statistical; results will not be extrapolated. "
              "Size follows the risk's score: " + "; ".join(f"score {low}+ → {n} items" for low, n in SIZE_BY_SCORE)
              + f"; a population at or below that size is taken whole. A census is allowed up to {CENSUS_LIMIT} items.", "",
              "| Test | Risk | Flagged population | Items sampled | Transactions | Value of transactions | File |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in self.rows:
            for t in r["tests"]:
                s = t["sample"]
                M.append(f"| {t['id']} | {r['risk_id']} | {s['population']:,} | {s['items']:,} | {s['transactions']:,} "
                         f"| £{s['gbp']:,.2f} | `{s['csv']}` |" if s else
                         f"| {t['id']} | {r['risk_id']} | — | — | — | — | no data sample: {t['reason']} |")
        p = self.pack
        M += ["", f"Totals: {p['tests']['shown_as']} tests, {p['tests_with_sample']['shown_as']} with a data sample; "
                  f"{p['sample_items']['shown_as']} items; {p['sample_transactions']['shown_as']} transactions worth "
                  f"{p['sample_gbp']['shown_as']}; {p['pbc_items']['shown_as']} requests to the council.", "",
              "## Limitations", "", parts["limitations"], "",
              "## Rule coverage", "",
              f"Testable rules: {p['rules_total']['shown_as']}. Cited by an approved risk, control or test: "
              f"{p['rules_cited']['shown_as']}. Listed as not tested, each with a reason: "
              f"{p['rules_not_tested']['shown_as']}. Both lists are in `risk-control-matrix.md`.", ""]

        C = ["# Risk and control matrix", "", banner, "", basis, "",
             "| Risk | Rating | Expected control | Rules | Tests |", "| --- | --- | --- | --- | --- |"]
        for r in self.rows:
            for cid, c in r["controls"].items():
                rules = ", ".join(f"{x} (cl. {self.rules[x]['clause']})" for x in c["rules"])
                C.append(f"| {r['risk_id']} {r['title']} | {r['rate']['text']} | **{cid}** {c['text']} | {rules} "
                         f"| {', '.join(c['tests'])} |")
        C += ["", "## Rule coverage", "", "### Rules cited", "", "| Rule | Clause | Type | Cited by |",
              "| --- | --- | --- | --- |"]
        for rule, r in self.rules.items():
            if self.rule_use.get(rule):
                C.append(f"| {rule} | {r['clause']} | {r.get('type', '')} | {', '.join(sorted(self.rule_use[rule]))} |")
        C += ["", "### Rules not tested", "", "| Rule | Clause | Type | Reason |", "| --- | --- | --- | --- |"]
        for rule, reason in self.not_tested.items():
            C.append(f"| {rule} | {self.rules[rule]['clause']} | {self.rules[rule].get('type', '')} | {reason} |")
        C.append("")

        A = ["# Audit program", "", banner, "", basis, ""]
        for r in self.rows:
            A += [f"## {r['risk_id']} {r['title']}", "", f"Rating: {r['rate']['text']}. Auditor decision: "
                  f"{r['decision'][0]}" + (f" — “{r['decision'][1]}”" if r["decision"][1] else "") + ".", ""]
            for cid, c in r["controls"].items():
                A.append(f"- **{cid}** {c['text']} ({', '.join(c['rules'])})")
            A.append("")
            for t in r["tests"]:
                A += [f"### {t['id']}", "", f"**Controls tested:** {', '.join(t['controls'])}", "",
                      f"**Test step.** {t['step']}", ""]
                s = t["sample"]
                if s:
                    flt = "; ".join(f"`{c['column']}` {c['op']} `{c['value']}`" for c in s["filter"]) or "none"
                    srt = ", ".join(f"`{k['column']}` {k['order']}" for k in s["sort"])
                    what = "the payments listed against each item" if s["mode"] == "listed" \
                        else "every payment to the item's supplier in the period"
                    if s["per_item_limit"]:
                        what += f", largest {s['per_item_limit']} per item"
                    ids = [row["row_id"] for row in s["rows"]]
                    A += [f"**Sample.** From `analytics-full/{s['file']}`; filter: {flt}; order: {srt}; size: {s['basis']}. "
                          f"{s['items']:,} of {s['population']:,} flagged items, giving {s['transactions']:,} transactions "
                          f"worth £{s['gbp']:,.2f} ({what}).", "",
                          f"**Transactions to pull.** `{s['csv']}`. First rows: "
                          + ", ".join(f"`{i}`" for i in ids[:8]) + (" …" if len(ids) > 8 else "") + ".", ""]
                else:
                    A += [f"**Sample.** No data sample: {t['reason']}", ""]
                A += [f"**Requests needed:** {', '.join(t['pbc'])}", ""]
        A += ["## PBC list (requests to the council)", "", "| Ref | Request | Needed for |", "| --- | --- | --- |"]
        for pid, pb in self.pbc.items():
            A.append(f"| {pid} | {pb.get('request', '')} | {', '.join(pb['tests'])} |")
        A.append("")
        return {"planning-memo.md": "\n".join(M), "risk-control-matrix.md": "\n".join(C), "audit-program.md": "\n".join(A)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outputs", default="outputs")
    ap.add_argument("--gate", action="store_true", help="only check that the scope gate is closed")
    args = ap.parse_args()
    out = Path(args.outputs)
    try:
        errors, info = gate(out)
        if errors:
            for e in errors:
                print(f"GATE OPEN  {e}")
            print(f"BLOCKED: {len(errors)} reason(s); the pack is not built")
            return 1
        print(f"GATE CLOSED: register {info['title']}; {len(info['registered'])} risks decided; "
              f"{len(info['scope'])} in scope ({', '.join(info['scope'])}); "
              f"{len(info['rejected'])} rejected ({', '.join(info['rejected']) or 'none'})")
        if args.gate:
            return 0
        pack = Pack(out, info, br.load(out / "audit-plan.json", "audit plan"))
        if not isinstance(pack.plan, dict):
            raise br.Stop("audit-plan.json must be an object")
        pack.check()
        files = {}
        if not pack.errors:
            pack.compute()
            files = pack.render(datetime.now().strftime("%Y-%m-%d %H:%M"))
    except br.Stop as exc:
        print(f"CANNOT RUN: {exc}")
        return 2
    for w in pack.warnings:
        print(f"WARNING {w}")
    if pack.errors:
        for e in pack.errors:
            print(f"FAIL    {e}")
        print(f"FAILED: {len(pack.errors)} error(s); nothing was written")
        return 1

    samples_dir = out / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    for old in samples_dir.glob("T-*.csv"):
        old.unlink()
    for tid, s in pack.samples.items():
        with open(out / s["csv"], "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=s["header"])
            writer.writeheader()
            writer.writerows(s["rows"])
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    figures = {
        "register": info["title"],
        "method": {"size_by_score": [{"score_at_least": low, "items": n} for low, n in SIZE_BY_SCORE],
                   "census_limit": CENSUS_LIMIT},
        "pack": {k: v["value"] for k, v in pack.pack.items()},
        "scope": {"in_scope": info["scope"], "rejected": info["rejected"],
                  "ratings": {r["risk_id"]: {"likelihood": r["rate"]["l"], "impact": r["rate"]["i"],
                                             "score": r["rate"]["score"], "matrix_label": r["rate"]["matrix_label"],
                                             "band": r["rate"]["band"]} for r in pack.rows}},
        "samples": {tid: {k: s[k] for k in ("file", "population", "items", "transactions", "gbp", "csv")}
                    for tid, s in pack.samples.items()},
        "filled": pack.figures,
    }
    (out / "pack-figures.json").write_text(json.dumps(figures, ensure_ascii=False, indent=2), encoding="utf-8")
    p = pack.pack
    print(f"PACK BUILT: {p['risks_in_scope']['value']} risks, {p['controls']['value']} controls, {p['tests']['value']} tests, "
          f"{len(pack.samples)} sample files ({p['sample_transactions']['value']} transactions), "
          f"{p['pbc_items']['value']} PBC items, {len(pack.warnings)} warning(s) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
