"""Shared helpers for clean.py / analyse.py / selfcheck.py.

Nothing in this file contains a threshold figure: every monetary threshold is
read from outputs/rules.json at run time.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "outputs" / "rules.json"
SPEND_DIR = ROOT / "data" / "spend"
CONTRACTS = ROOT / "data" / "contracts.csv"
REGISTER = ROOT / "data" / "contract-register.csv"
OUT = ROOT / "outputs"
FULL = OUT / "analytics-full"

SHEET = "Data to publish"
EXPECTED_COLS = ["Service", "Expenditure category", "Narrative", "Date",
                 "Net amount", "Supplier name"]
TAGS = ["general_procurement", "care_or_education_placement", "grant",
        "agency_staff", "premises"]

# ---------------------------------------------------------------- suppliers
DROP_TOKENS = {"LTD", "LIMITED", "PLC", "LLP", "LLC", "INC", "CIC", "CIO",
               "UK", "THE"}
_BRACKETS = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_UNCLOSED = re.compile(r"\([^)]*$")
_TRADING = re.compile(r"\s+(T/AS?|TRADING\s+AS)(?![A-Z0-9]).*$")


def normalise_supplier(name):
    """Same function for spend suppliers and notice suppliers."""
    s = str(name).upper()
    s = s.replace("&", " AND ")
    s = _BRACKETS.sub(" ", s)          # (CHAPS ONLY), (SOUTHERN), ( T/A ...)
    s = _UNCLOSED.sub(" ", s)          # unbalanced opening bracket
    s = _TRADING.sub(" ", s)           # T/A ..., T/AS ..., TRADING AS ...
    s = s.replace("'", "").replace("’", "").replace(".", "")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = [t for t in s.split() if t not in DROP_TOKENS]
    return " ".join(toks)


# ------------------------------------------------------------------- rules
THRESHOLD_TYPES = ["procedure", "approval", "waiver", "anti-avoidance"]
COMPETITION_RE = re.compile(r"quot|tender", re.I)
FLOOR_RE = re.compile(r"publish the expenditure", re.I)


def pence(x):
    return int(round(float(x) * 100))


def gbp(p):
    return round(p / 100.0, 2)


def load_rules():
    if not RULES.exists():
        raise SystemExit("STOP: outputs/rules.json is missing")
    d = json.loads(RULES.read_text())
    for k in ("rules", "parameters"):
        if k not in d:
            raise SystemExit(f"STOP: rules.json has no '{k}' key")
    return d


def derive_thresholds(d):
    """Build the threshold list from rules.json.

    Returns dict with:
      thresholds   one entry per distinct numeric boundary
      tiers        named tiers (threshold_*_param) with value and citing rules
      publication  the publication threshold entry (or None)
      floor        the 'expenditure over' publication floor (or None)

    `inclusive` True  -> the higher requirement applies at amount >= value
    `inclusive` False -> it applies at amount > value (amount == value is under)
    """
    cites, tiers = [], {}
    for r in d["rules"]:
        if r["type"] not in THRESHOLD_TYPES:
            continue
        comp = bool(r["type"] == "procedure"
                    and COMPETITION_RE.search(r.get("required_action") or ""))
        for side in ("low", "high"):
            v = r.get(f"threshold_{side}")
            inc = r.get(f"threshold_{side}_inclusive")
            p = r.get(f"threshold_{side}_param")
            if v is not None:
                cites.append({"p": pence(v), "rule_id": r["rule_id"],
                              "type": r["type"], "side": side, "inclusive": inc,
                              "competition": comp,
                              "as_printed": r.get("threshold_text")})
            if p is not None:
                t = tiers.setdefault(p, {"tier": p, "rule_ids": [],
                                         "competition_triggering": False})
                t["rule_ids"].append(r["rule_id"])
                t["competition_triggering"] = t["competition_triggering"] or comp
    # boundary of each citation: a lower bound "> x" (exclusive) is the same
    # boundary as ">= x + 1p" when another citation sits at x + 1p inclusive.
    values = {c["p"] for c in cites}
    incl_lows = {c["p"] for c in cites if c["side"] == "low" and c["inclusive"] is True}
    for c in cites:
        c["key"] = c["p"]
        if (c["side"] == "low" and c["inclusive"] is False
                and (c["p"] + 1) in incl_lows):
            c["key"] = c["p"] + 1
            c["merged_from_pence"] = c["p"]
    out = []
    for key in sorted({c["key"] for c in cites}):
        cs = [c for c in cites if c["key"] == key]
        lows = [c for c in cs if c["side"] == "low"]
        highs = [c for c in cs if c["side"] == "high"]
        votes = set()
        for c in lows:
            votes.add(True if "merged_from_pence" in c else bool(c["inclusive"]))
        low_votes = set(votes)
        for c in highs:
            votes.add(not bool(c["inclusive"]))
        if lows:
            trig = True in low_votes
            basis = "lower bounds of the rules that start at this value"
        else:
            trig = any(c["inclusive"] is False for c in highs)
            basis = "upper bounds only"
        out.append({
            "value": gbp(key), "value_pence": key, "inclusive": trig,
            "inclusive_meaning": ("higher requirement applies at amount >= value"
                                  if trig else
                                  "higher requirement applies at amount > value; "
                                  "an amount equal to the value counts as under"),
            "inclusivity_basis": basis,
            "inclusivity_conflict": len(votes) > 1,
            "as_printed": sorted({c["as_printed"] for c in cs if c["as_printed"]}),
            "competition_triggering": any(c["competition"] for c in cs),
            "publication_threshold": False,
            "rule_ids": sorted({c["rule_id"] for c in cs}),
            "citations": [{"rule_id": c["rule_id"], "type": c["type"],
                           "side": c["side"], "inclusive": c["inclusive"],
                           "bound_value": gbp(c["p"])} for c in cs],
        })
    # publication threshold: lowest numeric threshold_low among advertising
    # rules in Appendix B
    pubs = [(pence(r["threshold_low"]), r["rule_id"]) for r in d["rules"]
            if r["type"] == "advertising" and r.get("threshold_low") is not None
            and str(r.get("clause", "")).startswith("App B")]
    publication = None
    if pubs:
        pv = min(p for p, _ in pubs)
        ids = sorted(i for p, i in pubs if p == pv)
        hit = [t for t in out if t["value_pence"] == pv]
        if hit:
            hit[0]["publication_threshold"] = True
            hit[0]["publication_rule_ids"] = ids
            publication = hit[0]
        else:
            inc = [r["threshold_low_inclusive"] for r in d["rules"] if r["rule_id"] == ids[0]][0]
            publication = {"value": gbp(pv), "value_pence": pv, "inclusive": bool(inc),
                           "rule_ids": ids, "publication_rule_ids": ids}
    # 'expenditure over' floor of the published population
    fl = [(pence(r["threshold_low"]), r["rule_id"]) for r in d["rules"]
          if r["type"] == "record" and r.get("threshold_low") is not None
          and FLOOR_RE.search(r.get("required_action") or "")]
    floor = None
    if fl:
        fv = min(p for p, _ in fl)
        floor = {"value": gbp(fv), "value_pence": fv,
                 "rule_ids": sorted(i for p, i in fl if p == fv)}
    params = d["parameters"]
    tier_list = []
    for name, t in sorted(tiers.items()):
        if name not in params:
            raise SystemExit(f"STOP: rules cite parameter {name} not in rules.json parameters")
        t["rule_ids"] = sorted(set(t["rule_ids"]))
        t["value"] = params[name].get("value")
        tier_list.append(t)
    return {"thresholds": out, "tiers": tier_list, "publication": publication,
            "floor": floor,
            "null_parameters": sorted(k for k, v in params.items() if v.get("value") is None)}


def triggers(amount_p, t):
    """True when an amount (pence) is at/over threshold t per its inclusivity."""
    return amount_p >= t["value_pence"] if t["inclusive"] else amount_p > t["value_pence"]


def rule_ids_for_clause(d, prefix):
    return sorted(r["rule_id"] for r in d["rules"] if str(r.get("clause", "")).startswith(prefix))
