#!/usr/bin/env python3
"""Build outputs/risk-register.md from outputs/risk-ratings.json.

The agent supplies judgments (risk-ratings.json). This script supplies every
number and every label:
  - resolves each [rule:ID], [metric:$.path] and [history:ID] citation;
  - fills each {{$.path}} placeholder from analytics.json;
  - looks up the score, matrix label and band in the council's own matrix and
    band table in history.json (or the stated fallback if there is none);
  - drops any risk whose likelihood or impact justification has no resolvable
    citation, whose placeholder does not resolve, or whose rating breaks the
    rubric, and lists it with the reason;
  - checks that a repeat-finding uplift cites an audit with an adverse opinion;
  - warns when a figure is typed in prose;
  - writes risk-register.md, auditor-comments.md and risk-register.state.json.

Draft or revision: if auditor-comments.md holds no decision, this is a draft
and becomes the baseline. Once any decision is recorded the build is a
revision: it needs a "revision" block in risk-ratings.json, and it fails,
writing nothing, if a decision was not applied or anything changed that the
auditor did not ask for.

Usage (from the project root):
  .venv/bin/python .claude/skills/risk-assessment/build_register.py
  ... build_register.py --ratings R.json --rules X --analytics Y --history Z --out-dir DIR

Exit code 0 = register written, 1 = failed (nothing written), 2 = cannot run.
Standard library only.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PATH = r"""\$(?:\.[A-Za-z_][\w\-]*|\[(?:"[^"\]]+"|'[^'\]]+')\]|\[\d+\])+"""
STEP = re.compile(r"""\.([A-Za-z_][\w\-]*)|\[(?:"([^"\]]+)"|'([^'\]]+)')\]|\[(\d+)\]""")
CITE = re.compile(r"\[(rule|history):([A-Za-z0-9\-]+)\]|\[metric:(" + PATH + r")\]")
ANY_TAG = re.compile(r"\[(?:rule|metric|history):[^\s]*?\](?!\])")
PLACEHOLDER = re.compile(r"\{\{\s*(" + PATH + r")\s*(?:\|\s*(gbp|pct|int|raw)\s*)?\}\}")
ANY_PLACEHOLDER = re.compile(r"\{\{.*?\}\}")
RISK_ID = re.compile(r"R-\d{2,}")
MONEY_KEY = re.compile(r"gbp|amount|value|total|payment|estimate|rate$|threshold|floor", re.I)
# A typed figure: money, a percentage, or a number of two or more digits.
TYPED = re.compile(r"£\s?\d[\d,.]*\s?(?:k|m|million|bn)?\b|\b\d+(?:\.\d+)?\s?%|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d+\b|\b\d{2,}\b")
NOT_A_FIGURE = re.compile(r"(?:clauses?|cl\.|rows?|pages?|p\.|table|figure|appendix|app|section|paragraph|para\.?)\s+$", re.I)
IDS = re.compile(r"\b[A-Z]{1,4}-\d+\b")
ADVERSE = re.compile(r"limited|weak|unsatisfactory|inadequate|no assurance|minimal", re.I)
ACCUSATION = re.compile(r"\b(fraud\w*|breach\w*|illegal\w*|unlawful\w*|wrongdoing|corrupt\w*|misconduct|collu\w+|"
                        r"circumvent\w*|evad\w+|deliberate\w*)\b", re.I)
DECISIONS = ("approve", "revise", "override", "reject")
RUBRIC = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
FALLBACK = {1: "Very low", 2: "Low", 3: "Medium", 4: "High", 5: "Very high"}
TEXT_FIELDS = ("description", "proposed_focus")
RISK_FIELDS = {"risk_id", "title", "description", "likelihood", "impact", "evidence", "proposed_focus"}
LIKELIHOOD_FIELDS = {"score", "rubric_row", "signals", "justification", "repeat_finding", "auditor_override"}
IMPACT_FIELDS = {"score", "category", "justification", "auditor_override"}


class Stop(Exception):
    """Cannot run (exit 2)."""


def load(path, what):
    p = Path(path)
    if not p.is_file():
        raise Stop(f"{what} not found: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Stop(f"{path} is not valid JSON: {exc}")


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def resolve(root, path):
    """Follow a $.a.b["c.d"][0] path. Returns (found, value)."""
    node, pos = root, 1
    while pos < len(path):
        m = STEP.match(path, pos)
        if not m:
            return False, None
        key, dq, sq, idx = m.groups()
        try:
            node = node[int(idx)] if idx is not None else node[key or dq or sq]
        except (KeyError, IndexError, TypeError):
            return False, None
        pos = m.end()
    return True, node


def last_key(path):
    steps = STEP.findall(path)
    for key, dq, sq, _ in reversed(steps):
        if key or dq or sq:
            return key or dq or sq
    return ""


def fmt(value, path, style):
    """Format a resolved scalar. Returns (text, error)."""
    if isinstance(value, bool) or value is None or isinstance(value, (dict, list)):
        kind = "null" if value is None else type(value).__name__
        return None, f"{{{{{path}}}}} resolves to {kind}, not a figure or text"
    if isinstance(value, str):
        return value, None
    if style == "raw":
        return str(value), None
    if style == "pct":
        return f"{value * 100:.1f}%", None
    if style == "int":
        return f"{round(value):,}", None
    if style == "gbp" or (isinstance(value, float) and MONEY_KEY.search(last_key(path))):
        text = f"£{value:,.2f}"
        return (text[:-3] if text.endswith(".00") else text), None
    if is_int(value):
        return f"{value:,}", None
    return f"{value:,.4f}".rstrip("0").rstrip("."), None


def test_of(path):
    m = re.match(r"\$\.tests\.([A-Za-z_]\w*)", path)
    return m.group(1) if m else None


def parse_range(text):
    """'15 -25' -> (15, 25); 'Up to 3' -> (None, 3); '20+' -> (20, None)."""
    t = str(text).strip().lower()
    m = re.fullmatch(r"(\d+)\s*[-–—]\s*(\d+)", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(?:up to|<=|≤)\s*(\d+)", t)
    if m:
        return None, int(m.group(1))
    m = re.fullmatch(r"(\d+)\s*(?:\+|or (?:more|above))", t)
    if m:
        return int(m.group(1)), None
    m = re.fullmatch(r"\d+", t)
    return (int(t), int(t)) if m else None


class Method:
    """The council's scoring method as recorded in history.json, or the fallback."""

    def __init__(self, history):
        sm = history.get("scoring_method") or {}
        self.notes = []          # header lines about conflicts and fallbacks
        self.usable = bool(sm.get("usable")) and bool(sm.get("likelihood_scale")) \
            and bool(sm.get("impact_scale")) and bool(sm.get("matrix") or sm.get("bands"))
        self.fallback = not self.usable
        self.matrix, self.bands, self.unused_items = {}, [], {}
        self.likelihood, self.impact = dict(FALLBACK), dict(FALLBACK)
        if self.fallback:
            reason = sm.get("reason_if_not_usable") or "history.json holds no usable matrix and scales"
            self.notes.append(f"**Fallback scale in use.** {reason}. Likelihood and impact are rated 1–5 "
                              "(Very low … Very high), score = likelihood × impact as a plain product, no bands.")
            return
        matrix = sm.get("matrix") or {"likelihood_labels": [], "rows": []}
        labels = matrix["likelihood_labels"]
        self.likelihood = {i + 1: label for i, label in enumerate(labels)}
        self.impact = {}
        if not matrix["rows"]:
            # Scales and bands but no printed matrix: labels from the scales, score as a product.
            self.likelihood = {i["score"]: i["label"] for i in reversed(sm["likelihood_scale"])}
            self.impact = {i["score"]: i["label"] for i in reversed(sm["impact_scale"])}
            self.notes.append("The papers print scales and bands but no matrix. Score = likelihood × impact as a "
                              "plain product, computed by the builder; no matrix label is shown.")
        for row in matrix["rows"]:
            self.impact[row["impact_score"]] = row["impact_label"]
            for i, (score, band) in enumerate(zip(row["scores"], row["bands"])):
                self.matrix[(row["impact_score"], i + 1)] = (score, band)
        # Scale items that disagree with the matrix axes are marked, not used.
        for item in sm["likelihood_scale"] if matrix["rows"] else []:
            if self.likelihood.get(item.get("score")) != item.get("label"):
                self.mark_unused(item, "likelihood", self.likelihood)
        for item in sm["impact_scale"] if matrix["rows"] else []:
            if self.impact.get(item.get("score")) != item.get("label"):
                self.mark_unused(item, "impact", self.impact)
        for band in sm.get("bands") or []:
            rng = parse_range(band.get("score_range"))
            if rng is None:
                self.notes.append(f"Band {band.get('id')} prints the range '{band.get('score_range')}', which "
                                  "could not be read; it is **not used**.")
                continue
            self.bands.append((rng, band))
        names = {b["band"] for _, b in self.bands}
        differing = {}
        for (_, _), (score, cell) in sorted(self.matrix.items()):
            band = self.band(score)
            if band and cell != band["band"] and cell not in names:
                differing.setdefault((cell, band["band"], band["id"]), set()).add(score)
        for (cell, name, bid), scores in differing.items():
            self.notes.append(f"The matrix prints **{cell}** in the cells scoring {', '.join(map(str, sorted(scores)))}; "
                              f"the band table prints **{name}** for that range ({bid}). **Used:** the matrix label, "
                              f"shown as printed. **Marked, not used as the label:** the band-table name, shown beside it.")
        unbanded = sorted({s for s, _ in self.matrix.values() if self.band(s) is None})
        if unbanded:
            self.notes.append("No band-table range contains the matrix score(s) "
                              f"{', '.join(map(str, unbanded))}; a risk with that score shows the matrix label only.")

    def mark_unused(self, item, axis, axis_labels):
        self.unused_items[item["id"]] = axis
        printed = ", ".join(f"{label} = {score}" for score, label in sorted(axis_labels.items()))
        self.notes.append(f"{item['id']} records the {axis} level '{item.get('label')}' at {item.get('score')}, which "
                          f"disagrees with the matrix axis ({printed}). **Used:** the matrix axis. "
                          f"**Marked, not used:** {item['id']}.")

    def band(self, score):
        for (low, high), band in self.bands:
            if (low is None or score >= low) and (high is None or score <= high):
                return band
        return None

    def rate(self, likelihood, impact):
        """Returns dict(score, matrix_label, band, rag)."""
        if self.fallback:
            return {"score": likelihood * impact, "matrix_label": None, "band": None, "rag": None}
        score, cell = self.matrix.get((impact, likelihood), (likelihood * impact, None))
        band = self.band(score)
        return {"score": score, "matrix_label": cell,
                "band": band["band"] if band else None, "rag": band.get("rag") if band else None}


class Builder:
    def __init__(self, ratings, rules, analytics, history):
        self.ratings, self.analytics, self.history = ratings, analytics, history
        self.rules = {r["rule_id"]: r for r in rules.get("rules", [])}
        self.hist = {}
        self.collect_ids(history)
        self.method = Method(history)
        self.kept, self.dropped, self.warnings, self.fatal = [], [], [], []
        self.rules_cited = set()

    def collect_ids(self, node):
        if isinstance(node, dict):
            if isinstance(node.get("id"), str):
                self.hist[node["id"]] = node
            for value in node.values():
                self.collect_ids(value)
        elif isinstance(node, list):
            for value in node:
                self.collect_ids(value)

    # -- citations and placeholders --------------------------------------
    def history_label(self, item):
        if item["id"].startswith("AUD"):
            opinion = item.get("opinion") or "no opinion"
            extra = f"; follow-up: {item['follow_up_opinion']}" if item.get("follow_up_opinion") else ""
            return f"{item.get('area')} — {opinion}{extra} ({item.get('period')})"
        if "label" in item and "score" in item:
            return f"{item['label']} ({item['score']})"
        for key in ("theme", "band", "name", "level", "statement", "description"):
            if item.get(key):
                text = str(item[key])
                return text if len(text) <= 70 else text[:67] + "…"
        return ""

    def render(self, text, problems, cites):
        """Fill placeholders and gloss citations. Appends to problems (drop) and cites."""
        def cite(m):
            kind, ident, path = m.group(1), m.group(2), m.group(3)
            if path:
                found, _ = resolve(self.analytics, path)
                if found:
                    cites.append(("metric", path))
                    return f"[analytics `{path[2:]}`]"
                self.warnings.append(f"unresolved citation [metric:{path}]")
                return f"[UNRESOLVED metric `{path}`]"
            if kind == "rule" and ident in self.rules:
                cites.append(("rule", ident))
                self.rules_cited.add(ident)
                return f"[{ident}, cl. {self.rules[ident]['clause']}]"
            if kind == "history" and ident in self.hist:
                cites.append(("history", ident))
                label = self.history_label(self.hist[ident])
                return f"[{ident}: {label}]" if label else f"[{ident}]"
            self.warnings.append(f"unresolved citation [{kind}:{ident}]")
            return f"[UNRESOLVED {kind} {ident}]"

        def fill(m):
            path, style = m.group(1), m.group(2)
            found, value = resolve(self.analytics, path)
            if not found:
                problems.append(f"placeholder {{{{{path}}}}} does not resolve in analytics.json")
                return m.group(0)
            out, error = fmt(value, path, style)
            if error:
                problems.append(error)
                return m.group(0)
            return out

        out = CITE.sub(cite, text)
        out = PLACEHOLDER.sub(fill, out)
        for bad in ANY_PLACEHOLDER.findall(out):
            if not PLACEHOLDER.fullmatch(bad):
                problems.append(f"malformed placeholder {bad}")
        for bad in ANY_TAG.findall(out):
            if not bad.startswith("[analytics"):
                self.warnings.append(f"malformed citation {bad}")
        return out

    def typed_figures(self, rid, field, text):
        bare = IDS.sub(" ", ANY_PLACEHOLDER.sub(" ", ANY_TAG.sub(" ", CITE.sub(" ", text))))
        for m in TYPED.finditer(bare):
            if NOT_A_FIGURE.search(bare[:m.start()]):
                continue
            self.warnings.append(f"{rid} {field}: figure typed in prose ('{m.group(0).strip()}'); "
                                 "use a {{$.path}} placeholder")
        for m in ACCUSATION.finditer(bare):
            self.warnings.append(f"{rid} {field}: '{m.group(0)}' is not indicator language")

    # -- one risk --------------------------------------------------------
    def check_risk(self, risk, index, seen):
        rid = risk.get("risk_id") if isinstance(risk, dict) else None
        name = rid if isinstance(rid, str) else f"risks[{index}]"
        problems = []
        if not isinstance(risk, dict):
            return name, None, ["risk is not an object"]
        if not (isinstance(rid, str) and RISK_ID.fullmatch(rid)):
            problems.append(f"risk_id {rid!r} must look like R-01")
        elif rid in seen:
            problems.append("risk_id is used more than once")
        seen.add(rid)
        for key in sorted(RISK_FIELDS - risk.keys()):
            problems.append(f"missing field '{key}'")
        for key in sorted(risk.keys() - RISK_FIELDS):
            problems.append(f"unexpected field '{key}'")
        lik, imp = risk.get("likelihood"), risk.get("impact")
        for label, block, fields in (("likelihood", lik, LIKELIHOOD_FIELDS), ("impact", imp, IMPACT_FIELDS)):
            if not isinstance(block, dict):
                problems.append(f"'{label}' must be an object")
                continue
            for key in sorted(block.keys() - fields):
                problems.append(f"unexpected field '{label}.{key}'")
            if not (is_int(block.get("score")) and 1 <= block["score"] <= 5):
                problems.append(f"{label}.score must be an integer 1-5, got {block.get('score')!r}")
            if not (isinstance(block.get("justification"), str) and block["justification"].strip()):
                problems.append(f"{label}.justification is empty")
        evidence = risk.get("evidence")
        if not (isinstance(evidence, list) and evidence and all(isinstance(e, str) for e in evidence)):
            problems.append("'evidence' must be a non-empty list of strings")
        for key in ("title",) + TEXT_FIELDS:
            if not (isinstance(risk.get(key), str) and risk[key].strip()):
                problems.append(f"'{key}' must be a non-empty string")
        if problems:
            return name, None, problems

        out = {"risk_id": rid, "title": risk["title"]}
        cites = {}
        for field, text in (("description", risk["description"]), ("proposed_focus", risk["proposed_focus"]),
                            ("likelihood", lik["justification"]), ("impact", imp["justification"])):
            cites[field] = []
            out[field] = self.render(text, problems, cites[field])
            self.typed_figures(rid, field, text)
        cites["evidence"] = []
        out["evidence"] = [self.render(e, problems, cites["evidence"]) for e in evidence]
        for e in evidence:
            self.typed_figures(rid, "evidence", e)
        if ANY_PLACEHOLDER.search(risk["title"]) or CITE.search(risk["title"]):
            problems.append("title must be plain text (no placeholders or citations)")

        for field in ("likelihood", "impact"):
            if not cites[field]:
                problems.append(f"{field} justification has no resolvable citation")

        l_override, i_override = lik.get("auditor_override") is True, imp.get("auditor_override") is True
        out["likelihood_override"], out["impact_override"] = l_override, i_override
        out["repeat"] = None
        self.check_likelihood(lik, cites["likelihood"], problems, out, l_override)
        self.check_impact(imp, cites["impact"], problems, out, i_override)
        if problems:
            return name, None, problems
        out.update(self.method.rate(lik["score"], imp["score"]))
        out["l_score"], out["i_score"] = lik["score"], imp["score"]
        out["l_label"], out["i_label"] = self.method.likelihood[lik["score"]], self.method.impact[imp["score"]]
        out["category"] = imp.get("category")
        return name, out, []

    def check_likelihood(self, lik, cites, problems, out, override):
        row = lik.get("rubric_row")
        signals = lik.get("signals") or []
        repeat = lik.get("repeat_finding")
        out["rubric_row"] = row
        if override:
            return      # the auditor set this score; the rubric does not apply
        if row not in RUBRIC:
            problems.append(f"likelihood.rubric_row must be one of {sorted(RUBRIC)}, got {row!r}")
            return
        values = []
        if not isinstance(signals, list):
            problems.append("likelihood.signals must be a list of analytics paths")
            signals = []
        for path in signals:
            found, value = resolve(self.analytics, path) if isinstance(path, str) and re.fullmatch(PATH, path) \
                else (False, None)
            if not found or isinstance(value, bool) or not isinstance(value, (int, float)):
                problems.append(f"likelihood signal {path!r} does not resolve to a number in analytics.json")
            else:
                values.append((path, value))
                if ("metric", path) not in cites:
                    problems.append(f"likelihood signal {path} is not cited as [metric:…] in the justification")
        positive_tests = {test_of(p) or p for p, v in values if v > 0}
        if not problems:
            if row == "L1" and (not values or positive_tests):
                problems.append("rubric L1 needs at least one signal and every signal equal to zero")
            if row == "L2" and values:
                problems.append("rubric L2 is for risks with no data signal; remove the signals or use L1, L3 or L4")
            if row == "L3" and (len(positive_tests) != 1 or any(v <= 0 for _, v in values)):
                problems.append("rubric L3 needs signals above zero from exactly one test "
                                f"(found {len(positive_tests)} test(s) above zero)")
            if row == "L4" and (len(positive_tests) < 2 or any(v <= 0 for _, v in values)):
                problems.append("rubric L4 needs signals above zero from two or more different tests "
                                f"(found {len(positive_tests)})")
        base = RUBRIC[row]
        expected = base
        if repeat is not None:
            audit = repeat.get("audit") if isinstance(repeat, dict) else None
            item = self.hist.get(audit)
            if not item or not str(audit).startswith("AUD"):
                problems.append(f"repeat_finding.audit {audit!r} is not an audit in history.json")
            else:
                opinions = f"{item.get('opinion') or ''} {item.get('follow_up_opinion') or ''}"
                if not ADVERSE.search(opinions):
                    problems.append(f"repeat-finding uplift cites {audit}, whose opinion "
                                    f"('{opinions.strip() or 'none'}') is not adverse")
                if ("history", audit) not in cites:
                    problems.append(f"repeat-finding audit {audit} is not cited as [history:{audit}] in the justification")
                expected = min(5, base + 1)
                out["repeat"] = {"audit": audit, "base": base, "label": self.history_label(item)}
        if lik["score"] != expected:
            how = f"rubric {row} = {base}" + (" plus 1 for the repeat finding" if repeat is not None else "")
            problems.append(f"likelihood.score is {lik['score']} but {how} gives {expected}")

    def check_impact(self, imp, cites, problems, out, override):
        if self.method.fallback or override:
            return
        cited = [self.hist[i] for kind, i in cites if kind == "history" and i.startswith("IMP")]
        for item in cited:
            if item["id"] in self.method.unused_items:
                problems.append(f"impact cites {item['id']}, which is marked not used (it disagrees with the matrix)")
        if not any(item.get("score") == imp["score"] and item["id"] not in self.method.unused_items for item in cited):
            want = [i for i, item in self.hist.items() if i.startswith("IMP") and item.get("score") == imp["score"]
                    and i not in self.method.unused_items]
            problems.append(f"impact.score is {imp['score']} but the justification does not cite that level of the "
                            f"council's impact scale ({', '.join(f'[history:{w}]' for w in want) or 'none recorded'})")

    def run(self):
        risks = self.ratings.get("risks")
        if not isinstance(risks, list) or not risks:
            self.fatal.append("risk-ratings.json has no 'risks' list")
            return
        seen = set()
        for index, risk in enumerate(risks):
            name, out, problems = self.check_risk(risk, index, seen)
            if problems:
                title = risk.get("title") if isinstance(risk, dict) else None
                self.dropped.append({"risk_id": name, "title": title or "(no title)", "reasons": problems})
            else:
                self.kept.append(out)
        conflicts = (self.ratings.get("method") or {}).get("conflicts") or []
        self.declared = []
        for n, c in enumerate(conflicts):
            ok = isinstance(c, dict) and all(isinstance(c.get(k), str) and c[k].strip()
                                             for k in ("discrepancy", "used", "not_used", "effect"))
            if not ok:
                self.fatal.append(f"method.conflicts[{n}] needs discrepancy, used, not_used and effect")
            elif c["discrepancy"] not in self.hist or not c["discrepancy"].startswith("DIS"):
                self.fatal.append(f"method.conflicts[{n}] cites {c['discrepancy']!r}, not a discrepancy in history.json")
            else:
                self.declared.append(c)
        recorded = [i for i in self.hist if i.startswith("DIS")]
        if recorded and not self.declared:
            self.warnings.append(f"history.json records {len(recorded)} discrepancies and method.conflicts declares none; "
                                 "declare every one that touches a scale, the matrix, a band or an escalation score")
        if not self.kept:
            self.fatal.append("no risk survived the checks; nothing to render")


# -- auditor comments ------------------------------------------------------
def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip())
    return [c.strip().replace("\\|", "|") for c in cells[1:-1]]


def read_comments(path):
    """Returns (decisions {risk_id: (decision, comment)}, general text, errors)."""
    decisions, errors, general = {}, [], ""
    if not path.is_file():
        return decisions, general, errors
    text = path.read_text(encoding="utf-8")
    head, _, tail = text.partition("\n## General comments")
    for line in head.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if len(cells) < 5 or not RISK_ID.fullmatch(cells[0]):
            continue
        decision = cells[3].lower().strip("* ")
        if decision and decision not in DECISIONS:
            errors.append(f"auditor-comments.md: decision for {cells[0]} is '{cells[3]}'; "
                          f"use one of {', '.join(DECISIONS)}")
        decisions[cells[0]] = (decision, cells[4])
    general = "\n".join(l for l in tail.splitlines()[1:] if not l.startswith("<!--")).strip()
    return decisions, general, errors


def rating_text(r):
    text = f"{r['l_label']} ({r['l_score']}) × {r['i_label']} ({r['i_score']}) = {r['score']}"
    if r["matrix_label"]:
        text += f" {r['matrix_label']}"
    return text


def write_comments(path, kept, decisions, general, title):
    def cell(text):
        return str(text).replace("|", "\\|").replace("\n", " ")
    lines = ["# Auditor decisions", "",
             f"Register: {title}. Fill in **Decision** and **Comment** for every risk, then ask for the "
             "risk-assessor to be re-run. Nothing goes to planning until every risk has a decision.", "",
             "| Decision | Meaning |", "| --- | --- |",
             "| `approve` | In scope as rated. The risk must not change. |",
             "| `revise` | Change the risk as the comment says (wording, evidence, focus, or re-rate under the rubric). |",
             "| `override` | Set the likelihood or impact yourself: give the score(s) and your reason in the comment. |",
             "| `reject` | Out of scope. The risk stays in the register, marked rejected. |", "",
             "| Risk | Title | Rating | Decision | Comment |", "| --- | --- | --- | --- | --- |"]
    for r in kept:
        decision, comment = decisions.get(r["risk_id"], ("", ""))
        lines.append(f"| {r['risk_id']} | {cell(r['title'])} | {cell(rating_text(r))} | {decision} | {cell(comment)} |")
    lines += ["", "## General comments", "",
              "<!-- Anything not tied to one risk, including a request to add a risk. -->", general, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# -- revision checks ---------------------------------------------------------
def snapshot(risk):
    lik, imp = risk["likelihood"], risk["impact"]
    return {"title": risk["title"], "description": risk["description"],
            "likelihood_score": lik["score"], "likelihood_justification": lik["justification"],
            "likelihood_rubric_row": lik.get("rubric_row"), "likelihood_signals": lik.get("signals") or [],
            "repeat_finding": lik.get("repeat_finding"),
            "impact_score": imp["score"], "impact_category": imp.get("category"),
            "impact_justification": imp["justification"],
            "evidence": risk["evidence"], "proposed_focus": risk["proposed_focus"]}


def describe_diff(old, new):
    parts = []
    for key, label in (("likelihood_score", "likelihood"), ("impact_score", "impact")):
        if old[key] != new[key]:
            parts.append(f"{label} {old[key]} → {new[key]}")
    for key in old:
        if key.endswith("_score") or old[key] == new[key]:
            continue
        parts.append(key.replace("_", " ") + " changed")
    return parts


def check_revision(b, raw, decisions, general, state, errors):
    """Fill errors if a decision is unapplied or something unrequested changed. Returns change notes."""
    rev = b.ratings.get("revision")
    if not isinstance(rev, dict) or not is_int(rev.get("number")) or rev["number"] < 1 \
            or not isinstance(rev.get("changes", []), list):
        errors.append("auditor decisions are recorded but risk-ratings.json has no valid 'revision' block "
                      "({number, changes, added}); re-run the risk-assessor to apply the decisions")
        return []
    baseline = (state or {}).get("baseline")
    if not isinstance(baseline, dict):
        errors.append("no baseline in risk-register.state.json: the draft the auditor decided on is unknown")
        return []
    listed = {}
    for n, change in enumerate(rev.get("changes", [])):
        if not (isinstance(change, dict) and isinstance(change.get("risk_id"), str)
                and isinstance(change.get("summary"), str) and change["summary"].strip()):
            errors.append(f"revision.changes[{n}] needs risk_id and summary")
        else:
            listed[change["risk_id"]] = change["summary"]
    added = rev.get("added") or []
    kept_ids = {r["risk_id"] for r in b.kept}
    dropped_ids = {d["risk_id"] for d in b.dropped}
    notes = []
    for rid, old in baseline.items():
        decision, comment = decisions.get(rid, ("", ""))
        if rid in dropped_ids:
            errors.append(f"{rid} was in the draft the auditor saw and is now dropped by the builder; fix it")
            continue
        if rid not in raw:
            errors.append(f"{rid} was in the draft the auditor saw and is missing from risk-ratings.json; "
                          "a rejected risk stays in the file")
            continue
        new = snapshot(raw[rid])
        diff = describe_diff(old, new)
        lik, imp = raw[rid]["likelihood"], raw[rid]["impact"]
        flagged = lik.get("auditor_override") is True or imp.get("auditor_override") is True
        if flagged and decision != "override":
            errors.append(f"{rid} is marked auditor_override but the auditor's decision is '{decision or 'blank'}'")
        if decision in ("revise", "override"):
            if not comment.strip():
                errors.append(f"{rid}: decision '{decision}' has no comment saying what to change")
            if not diff:
                errors.append(f"{rid}: decision '{decision}' was not applied (the risk is unchanged from the draft)")
            if rid not in listed:
                errors.append(f"{rid}: decision '{decision}' has no entry in revision.changes")
            if decision == "override" and not flagged:
                errors.append(f"{rid}: decision 'override' but neither likelihood nor impact is marked auditor_override")
            if diff:
                notes.append((rid, decision, diff, listed.get(rid, ""), comment))
        else:
            if diff:
                errors.append(f"{rid} changed ({'; '.join(diff)}) but the auditor's decision is "
                              f"'{decision or 'blank'}': nothing may change that the auditor did not ask for")
            if rid in listed:
                errors.append(f"{rid} is listed in revision.changes but the auditor's decision is '{decision or 'blank'}'")
    for rid in sorted(kept_ids | dropped_ids):
        if rid in baseline:
            continue
        if rid in dropped_ids and rid in (state.get("baseline_dropped") or []):
            continue    # excluded in the draft the auditor saw, and still excluded
        if rid not in added:
            errors.append(f"{rid} is new since the draft and is not listed in revision.added")
        elif not general:
            errors.append(f"{rid} was added but 'General comments' in auditor-comments.md asks for nothing")
        else:
            notes.append((rid, "added", ["new risk"], listed.get(rid, "added at the auditor's request"), ""))
    for rid in decisions:
        if rid not in baseline and rid not in kept_ids:
            errors.append(f"auditor-comments.md has a decision for {rid}, which is not in the register")
    return notes


# -- rendering -------------------------------------------------------------
EXCERPT_CHARS = 160


def excerpt(quote):
    """First EXCERPT_CHARS of a rule's verbatim quote, cut at a word, for the register."""
    if not isinstance(quote, str) or not quote.strip():
        return "(no quote recorded)"
    text = " ".join(quote.split())
    if len(text) > EXCERPT_CHARS:
        text = text[:EXCERPT_CHARS].rsplit(" ", 1)[0] + " …"
    return text.replace("|", "\\|")


def render(b, title, mode, decisions, notes, inputs, built_at):
    def band(r):
        if b.method.fallback:
            return "—"
        if not r["band"]:
            return "none printed"
        return r["band"] + (f" ({r['rag']})" if r["rag"] else "")

    def status(rid):
        decision = decisions.get(rid, ("", ""))[0]
        return {"approve": "Approved", "revise": "Revised", "override": "Auditor override",
                "reject": "Rejected"}.get(decision, "Undecided")

    kept = sorted(b.kept, key=lambda r: (-r["score"], r["risk_id"]))
    undecided = [r["risk_id"] for r in kept if not decisions.get(r["risk_id"], ("", ""))[0]]
    L = [f"# Procurement risk register — {title}", ""]
    L += ["> These are **risk indicators to investigate**, drawn from public data. None of them is a finding of "
          "wrongdoing by the council, a service, an officer or a supplier.", ""]
    L += ["## Header", "",
          f"- **Status:** {title}, built {built_at}. "
          + ("Awaiting auditor decisions in `auditor-comments.md`." if mode == "draft" else
             (f"{len(undecided)} risk(s) still undecided: {', '.join(undecided)}." if undecided
              else "Every risk has an auditor decision.")),
          f"- **Inputs:** `{inputs['rules']}`, `{inputs['analytics']}`, `{inputs['history']}`.",
          "- **Scoring method:** " + ("fallback (see below)." if b.method.fallback else
                                      "the council's own, as recorded in history.json: 5×5 matrix, score and label "
                                      "read from the matrix cell, band from the band table."),
          f"- **Risks:** {len(kept)} rated, {len(b.dropped)} excluded by the builder, {len(b.warnings)} warning(s).",
          "- **Every figure** below was filled from analytics.json by `build_register.py`; none was typed.", ""]
    if b.method.notes or b.declared:
        L += ["### Scoring-method conflicts", "",
              "The papers disagree with themselves in the places below. One reading is used, the other is marked, "
              "and neither has been corrected.", ""]
        L += [f"- {note}" for note in b.method.notes]
        for c in b.declared:
            L.append(f"- {c['discrepancy']}: **Used:** {c['used']} **Marked, not used:** {c['not_used']} "
                     f"**Effect:** {c['effect']}")
        L.append("")
    if mode == "revision":
        L += [f"### What changed in this revision", ""]
        if not notes:
            L.append("- No risk was changed.")
        for rid, decision, diff, summary, comment in notes:
            line = f"- **{rid}** ({'AUDITOR OVERRIDE' if decision == 'override' else decision}): {'; '.join(diff)}."
            if summary:
                line += f" {summary}"
            if comment:
                line += f" Auditor: “{comment}”"
            L.append(line)
        for word, label in (("reject", "Rejected by the auditor (out of scope)"), ("approve", "Approved unchanged")):
            ids = [r["risk_id"] for r in kept if decisions.get(r["risk_id"], ("", ""))[0] == word]
            if ids:
                L.append(f"- {label}: {', '.join(ids)}.")
        L.append("")
    L += ["## Summary", "",
          "| Risk | Title | Likelihood | Impact | Score | Matrix label | Band | Decision |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in kept:
        L.append(f"| {r['risk_id']} | {r['title']} | {r['l_label']} ({r['l_score']}) | {r['i_label']} ({r['i_score']}) "
                 f"| {r['score']} | {r['matrix_label'] or '—'} | {band(r)} | {status(r['risk_id'])} |")
    L.append("")
    for r in kept:
        decision, comment = decisions.get(r["risk_id"], ("", ""))
        L += [f"## {r['risk_id']} {r['title']}", ""]
        if decision == "reject":
            L += [f"**Rejected by the auditor: out of scope.**" + (f" “{comment}”" if comment else ""), ""]
        L += [f"**Risk.** {r['description']}", ""]
        l_note = "set by the auditor" if r["likelihood_override"] else f"rubric {r['rubric_row']}"
        if r["repeat"]:
            l_note += (f"; **repeat finding +1** (rubric {r['repeat']['base']} → {r['l_score']}), citing "
                       f"{r['repeat']['audit']}: {r['repeat']['label']}")
        L += [f"**Likelihood: {r['l_score']} {r['l_label']}** ({l_note}). {r['likelihood']}", ""]
        i_note = "set by the auditor" if r["impact_override"] else (r["category"] or "category not stated")
        L += [f"**Impact: {r['i_score']} {r['i_label']}** ({i_note}). {r['impact']}", ""]
        rating = f"**Rating: {r['score']}**"
        if not b.method.fallback:
            rating += f" — matrix label **{r['matrix_label']}**, band **{band(r)}**"
        if r["likelihood_override"] or r["impact_override"]:
            rating += f". **AUDITOR OVERRIDE**" + (f": “{comment}”" if comment else "")
        L += [rating + ".", "", "**Evidence.**", ""]
        L += [f"- {e}" for e in r["evidence"]]
        L += ["", f"**Proposed focus.** {r['proposed_focus']}", ""]
    if b.dropped:
        L += ["## Excluded by the builder", "",
              "These risks were in risk-ratings.json and are **not rated**: a justification had no resolvable "
              "citation, a figure could not be filled, or the rating did not follow the rubric.", ""]
        for d in b.dropped:
            L.append(f"- **{d['risk_id']} {d['title']}**")
            L += [f"  - {reason}" for reason in d["reasons"]]
        L.append("")
    if b.warnings:
        L += ["## Warnings", ""] + [f"- {w}" for w in b.warnings] + [""]
    cited = sorted(b.rules_cited, key=lambda r: (len(r), r))
    if cited:
        L += ["## Rules cited", "",
              "The start of each cited rule's verbatim quote, copied from rules.json by the builder.", "",
              "| Rule | Clause | Page | Quote from the Contract Rules (excerpt) |", "| --- | --- | --- | --- |"]
        for rule_id in cited:
            rule = b.rules[rule_id]
            L.append(f"| {rule_id} | {rule.get('clause', '')} | {rule.get('page', '')} "
                     f"| {excerpt(rule.get('verbatim_quote'))} |")
        L.append("")
    L += ["## Auditor decisions", ""]
    if mode == "draft":
        L += ["No decision has been recorded. Open `auditor-comments.md`, enter a decision (`approve`, `revise`, "
              "`override` or `reject`) and a comment for every risk, then ask for the risk-assessor to be re-run. "
              "Planning does not start until every risk is decided and this register is a revision.", ""]
    L += ["| Risk | Rating | Decision | Auditor comment |", "| --- | --- | --- | --- |"]
    for r in kept:
        decision, comment = decisions.get(r["risk_id"], ("", ""))
        L.append(f"| {r['risk_id']} | {rating_text(r)} | {decision or '*undecided*'} | {comment.replace('|', chr(92) + '|')} |")
    L.append("")
    return "\n".join(L), undecided


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ratings", default="outputs/risk-ratings.json")
    ap.add_argument("--rules", default="outputs/rules.json")
    ap.add_argument("--analytics", default="outputs/analytics.json")
    ap.add_argument("--history", default="outputs/history.json")
    ap.add_argument("--out-dir", default="outputs")
    args = ap.parse_args()
    out = Path(args.out_dir)
    try:
        ratings = load(args.ratings, "risk ratings")
        b = Builder(ratings, load(args.rules, "rules"), load(args.analytics, "analytics"),
                    load(args.history, "history"))
    except Stop as exc:
        print(f"CANNOT RUN: {exc}")
        return 2
    if not isinstance(ratings, dict):
        print("CANNOT RUN: risk-ratings.json must be an object")
        return 2
    b.run()

    comments_path, state_path = out / "auditor-comments.md", out / "risk-register.state.json"
    decisions, general, errors = read_comments(comments_path)
    errors = b.fatal + errors
    mode = "revision" if any(d for d, _ in decisions.values()) else "draft"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else None
    raw = {r["risk_id"]: r for r in ratings.get("risks", []) if isinstance(r, dict) and isinstance(r.get("risk_id"), str)}
    notes = []
    if mode == "revision" and not b.fatal:
        notes = check_revision(b, raw, decisions, general, state, errors)
    elif ratings.get("revision"):
        b.warnings.append("risk-ratings.json has a 'revision' block but no auditor decision is recorded; "
                          "this build is a draft and the block is ignored")

    for d in b.dropped:
        print(f"DROPPED {d['risk_id']}: " + "; ".join(d["reasons"]))
    for w in b.warnings:
        print(f"WARNING {w}")
    if errors:
        for e in errors:
            print(f"FAIL    {e}")
        print(f"FAILED: {len(errors)} error(s); nothing was written")
        return 1

    number = ratings["revision"]["number"] if mode == "revision" else None
    title = f"Revision {number}" if mode == "revision" else "Draft"
    built_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    inputs = {"rules": args.rules, "analytics": args.analytics, "history": args.history}
    text, undecided = render(b, title, mode, decisions, notes, inputs, built_at)
    out.mkdir(parents=True, exist_ok=True)
    (out / "risk-register.md").write_text(text, encoding="utf-8")
    ordered = sorted(b.kept, key=lambda r: (-r["score"], r["risk_id"]))
    write_comments(comments_path, ordered, decisions, general, title)
    kept_ids = [r["risk_id"] for r in ordered]
    baseline = {rid: snapshot(raw[rid]) for rid in kept_ids} if mode == "draft" else state["baseline"]
    state_path.write_text(json.dumps({
        "baseline": baseline,
        "baseline_dropped": [d["risk_id"] for d in b.dropped] if mode == "draft" else state.get("baseline_dropped", []),
        "last_build": {"mode": mode, "revision": number, "built_at": built_at, "risks": kept_ids,
                       "decisions": {rid: decisions.get(rid, ("", ""))[0] for rid in kept_ids},
                       "undecided": undecided, "dropped": [d["risk_id"] for d in b.dropped],
                       "fallback_scale": b.method.fallback},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{title}: {len(b.kept)} risk(s) rated, {len(b.dropped)} dropped, {len(b.warnings)} warning(s)"
          + (f", {len(undecided)} undecided" if mode == "revision" else "")
          + f" -> {out / 'risk-register.md'}, {comments_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
