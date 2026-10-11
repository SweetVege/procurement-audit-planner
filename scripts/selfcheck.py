"""Step 5: independent re-derivation of one flagged item per test.

Each item is identified from analytics.json, then re-derived from the source
workbooks (openpyxl, by sheet row number), data/contracts.csv (csv module) and
outputs/rules.json, not from the cleaned CSVs or the test outputs.
Prints one PASS/FAIL line per check. Exit code 1 on any FAIL.
"""
import csv
import json
import re
import sys
from datetime import datetime, timedelta

from openpyxl import load_workbook

from common import CONTRACTS, FULL, OUT, RULES, SHEET, SPEND_DIR, normalise_supplier

A = json.loads((OUT / "analytics.json").read_text())
RULES_RAW = json.loads(RULES.read_text())
RESULTS = []


def report(test, ok, detail):
    RESULTS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {test} | {detail}")


def p(x):
    return int(round(float(x) * 100))


# ---- raw workbook access -------------------------------------------------
_WS = {}


def ws(fname):
    if fname not in _WS:
        _WS[fname] = load_workbook(SPEND_DIR / fname, data_only=True)[SHEET]
    return _WS[fname]


def wb_row(row_id):
    fname, n = row_id.rsplit(":", 1)
    v = [c.value for c in ws(fname)[int(n)][:6]]
    return {"service": v[0], "category": v[1], "narrative": v[2], "ts": v[3],
            "amount_p": p(v[4]), "supplier": v[5]}


def excluded(r):
    """Independent restatement of the three exclusion categories."""
    sup = str(r["supplier"]).upper().replace("&", " AND ")
    sup = re.sub(r"\s+", " ", sup)
    narr = str(r["narrative"] or "")
    if str(r["supplier"]).strip().lower() == "redacted":
        return True
    if re.search(r"LGPS|PENSION|SUPERANNUATION", narr, re.I):
        return True
    inter = re.search(r"\b(COUNCIL|BOROUGH|COUNTY|CNCL|NHS|POLICE|FIRE AUTHORITY|FIRE AND RESCUE|"
                      r"HMRC|HM REVENUE|DEPARTMENT FOR|MINISTRY OF)\b", sup) \
        or re.search(r"JOINT ARRANGEMENTS", narr, re.I)
    return bool(inter) and narr.strip().lower() != "private contractors"


def all_rows():
    for f in sorted(SPEND_DIR.glob("*.xlsx")):
        for i, row in enumerate(ws(f.name).iter_rows(values_only=True), start=1):
            v = row[:6]
            if v[0] is None and v[5] is None:
                continue
            if str(v[0]).strip() == "Service":
                continue
            yield {"row_id": f"{f.name}:{i}", "service": v[0], "narrative": v[2], "ts": v[3],
                   "amount_p": p(v[4]), "supplier": v[5]}


ROWS = [r for r in all_rows()]
KEPT = [r for r in ROWS if not excluded(r)]
DATES = [r["ts"].date() for r in ROWS]
W_START, W_END = min(DATES), max(DATES)
MONTHS = len({(d.year, d.month) for d in DATES})


def supplier_total(name):
    n = normalise_supplier(name)
    rows = [r for r in KEPT if normalise_supplier(r["supplier"]) == n]
    return sum(r["amount_p"] for r in rows), len(rows)


# ---- raw notices ----------------------------------------------------------
def notices():
    out = []
    with open(CONTRACTS, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["Organisation Name"].strip().lower() not in ("west berkshire council", "west berkshire"):
                continue
            field = [k for k in r if k.startswith("Supplier [")][0]
            names = [normalise_supplier(b.split("|")[0]) for b in r[field].strip()[1:-1].split("][")]
            out.append({"id": r["Notice Identifier"], "names": names,
                        "start": datetime.strptime(r["Contract start date"].strip(), "%d/%m/%Y").date(),
                        "end": datetime.strptime(r["Contract end date"].strip(), "%d/%m/%Y").date(),
                        "value": float(r["Awarded Value"])})
    return out


def rules_numeric_bounds(types):
    s = set()
    for r in RULES_RAW["rules"]:
        if r["type"] in types:
            for k in ("threshold_low", "threshold_high"):
                if r.get(k) is not None:
                    s.add(p(r[k]))
    return s


T = A["tests"]
pub = A["threshold_source"]["publication_threshold"]["value"]
pub_p = p(pub)
key = f"{pub:.2f}"
ok_pub = pub_p in {p(r["threshold_low"]) for r in RULES_RAW["rules"]
                   if r["type"] == "advertising" and str(r["clause"]).startswith("App B")
                   and r.get("threshold_low") is not None}
report("thresholds", ok_pub and pub_p in rules_numeric_bounds(("procedure",)),
       f"publication threshold {pub} is a numeric bound of an Appendix B advertising rule and of a "
       f"procedure rule in rules.json")
report("population", len(ROWS) == A["population"]["rows_raw"]
       and len(KEPT) == A["population"]["rows_after_exclusions"]
       and sum(r["amount_p"] for r in KEPT) == p(A["population"]["total_gbp"])
       and MONTHS == A["population"]["months_covered"],
       f"workbooks re-read with openpyxl: {len(ROWS)} rows, {len(KEPT)} after exclusions, "
       f"total and months agree with analytics.json")

# 1 threshold_clustering
it = T["threshold_clustering"]["per_threshold"][key]["top20"][0]
r = wb_row(it["row_id"])
report("threshold_clustering",
       r["amount_p"] == p(it["amount"]) and r["supplier"] == it["supplier"]
       and r["amount_p"] * 10 >= pub_p * 9 and r["amount_p"] < pub_p,
       f"{it['row_id']}: workbook amount {r['amount_p'] / 100:.2f} is within 10% below {pub}")

# 2 split_purchases
it = T["split_purchases"]["per_threshold"][key]["top20"][0]
ids = None
with open(FULL / "split-purchases.csv", newline="") as fh:
    for row in csv.DictReader(fh):
        if p(row["threshold"]) == pub_p and row["supplier"] == it["supplier"]:
            ids = row["row_ids"].split(";")
rs = [wb_row(i) for i in ids]
ds = [x["ts"].date() for x in rs]
report("split_purchases",
       len(rs) == it["n_payments"] and len({normalise_supplier(x["supplier"]) for x in rs}) == 1
       and all(x["amount_p"] < pub_p for x in rs)
       and sum(x["amount_p"] for x in rs) == p(it["total_gbp"]) >= pub_p
       and (max(ds) - min(ds)) <= timedelta(days=29),
       f"{it['supplier']}: {len(rs)} workbook rows ({ids[0]} ... {ids[-1]}), each under {pub}, "
       f"dates {min(ds)} to {max(ds)}, sum {sum(x['amount_p'] for x in rs) / 100:.2f}")

# 3 high_value_suppliers
it = T["high_value_suppliers"]["top20"][0]
tot, n = supplier_total(it["supplier"])
report("high_value_suppliers",
       n == it["n_payments"] and tot == p(it["total_gbp"])
       and abs(tot * 12 / MONTHS / 100 - it["annualised_estimate"]) < 0.005
       and tot * 12 / MONTHS >= pub_p,
       f"{it['supplier']} (largest rows {', '.join(it['largest_payment_row_ids'])}): {n} workbook "
       f"rows sum {tot / 100:.2f}, x 12/{MONTHS} = {tot * 12 / MONTHS / 100:.2f}")

if not T["off_contract"].get("skipped"):
    N = notices()
    active = {nm for x in N if x["end"] >= W_START and x["start"] <= W_END for nm in x["names"]}
    it = T["off_contract"]["top20"][0]
    ex = None
    with open(FULL / "high-value-suppliers.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["match_class"] == "exact":
                ex = row
                break
    report("off_contract",
           normalise_supplier(it["supplier"]) not in active
           and ex is not None and normalise_supplier(ex["supplier"]) in active,
           f"{it['supplier']} (row {it['largest_payment_row_ids'][0]}): name absent from the "
           f"{len(active)} supplier names on active council notices in contracts.csv; control "
           f"'{ex['supplier']}' (row {ex['largest_payment_row_ids'].split(';')[0]}) is present")

# 4 duplicates
for tier in ("different_time", "same_timestamp"):
    it = T["duplicates"]["per_tier"][tier]["top20"][0]
    rs = [wb_row(i) for i in it["row_ids"]]
    ds = sorted(x["ts"].date() for x in rs)
    nts = len({x["ts"] for x in rs})
    report(f"duplicates.{tier}",
           len({normalise_supplier(x["supplier"]) for x in rs}) == 1
           and {x["amount_p"] for x in rs} == {p(it["amount"])}
           and all((b - a).days <= 7 for a, b in zip(ds, ds[1:]))
           and ((nts > 1) if tier == "different_time" else (nts == 1))
           and it["row_ids_total"] == len(rs),
           f"{', '.join(it['row_ids'])}: same supplier, each {it['amount']:.2f}, dates "
           f"{ds[0]} to {ds[-1]}, {nts} distinct timestamp(s)")

# 5 expired_notice_spend
if not T["expired_notice_spend"].get("skipped") and T["expired_notice_spend"]["top20"]:
    it = T["expired_notice_spend"]["top20"][0]
    nm = normalise_supplier(it["supplier"])
    mine = [x for x in N if nm in x["names"]]
    tot, n = supplier_total(it["supplier"])
    report("expired_notice_spend",
           len(mine) == it["matched_notices"] and all(x["end"] < W_START for x in mine)
           and max(x["end"] for x in mine).isoformat() == it["latest_end_date"]
           and it["notice_id"] in [x["id"] for x in mine]
           and abs(tot * 12 / MONTHS / 100 - it["annualised_estimate"]) < 0.005,
           f"{it['supplier']} (row {it['largest_payment_row_ids'][0]}): {len(mine)} notice(s) in "
           f"contracts.csv, latest end {max(x['end'] for x in mine)} (notice {it['notice_id']}) "
           f"before window start {W_START}")

# 6 spend_vs_award
if not T["spend_vs_award"].get("skipped") and T["spend_vs_award"]["top20"]:
    it = T["spend_vs_award"]["top20"][0]
    nm = normalise_supplier(it["supplier"])
    mine = [x for x in N if nm in x["names"] and x["end"] >= W_START and x["start"] <= W_END]
    tot, n = supplier_total(it["supplier"])
    x = mine[0]
    years = ((x["end"] - x["start"]).days + 1) / 365.25
    ratio = (tot * 12 / MONTHS / 100) / (x["value"] / years)
    report("spend_vs_award",
           len(mine) == 1 and x["id"] == it["notice_id"] and len(x["names"]) == 1
           and abs(ratio - it["ratio"]) < 0.0001 and ratio >= T["spend_vs_award"]["parameters"]["ratio_minimum"],
           f"{it['supplier']} (row {it['largest_payment_row_ids'][0]}), notice {x['id']}: award "
           f"{x['value']:.2f} over {x['start']} to {x['end']}; workbook total {tot / 100:.2f}; "
           f"ratio {ratio:.4f}")

sys.exit(0 if all(RESULTS) else 1)
