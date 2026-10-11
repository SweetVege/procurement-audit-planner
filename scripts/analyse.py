"""Step 3/4: run the tests on spend-clean.csv and write outputs/analytics.json
plus full lists in outputs/analytics-full/.

No threshold figure appears in this file: all come from outputs/rules.json via
common.derive_thresholds().
"""
import json
import sys
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

import pandas as pd

from common import (FULL, OUT, TAGS, derive_thresholds, gbp, load_rules,
                    rule_ids_for_clause, triggers)

BAND = (9, 10)            # lower edge of the "just under" band as a fraction of T
COMPARATOR = (11, 10)     # upper edge of the comparator band
BASELINE = ((5, 10), (15, 10))
SPLIT_WINDOW_DAYS = 30
DUP_DAYS = 7
NEAR_RATIO = 0.85
SPEND_VS_AWARD_RATIO = 1.25
TOP = 20
ROW_ID_CAP = 12

GENERIC = set("""AND OF THE SERVICES SERVICE GROUP CARE COMPANY HOMES HOME HOUSE UNIVERSITY
COUNCIL TRUST SOLUTIONS CONSULTANCY CONSULTING ASSOCIATES PARTNERSHIP NETWORK CENTRE CENTER
TRAVEL CARS COACHES TAXIS CONSTRUCTION HEALTHCARE HEALTH SCHOOL SCHOOLS EDUCATION SUPPORT
LIVING CHILDREN CHILDRENS SEN BERKSHIRE WEST SOUTH NORTH EAST READING NEWBURY THATCHAM
HUNGERFORD SOUTHERN SYSTEMS SOFTWARE HOUSING SECURITY CLEANING FOSTERING COMMUNITY BUSINESS
MANAGEMENT FACILITIES SUPPLIES CATERING TRANSPORT ENGINEERING HIRE PROPERTY PROPERTIES
VALLEY""".split())

CAVEAT = (
    "contracts.csv holds published notices, not a contract register. It holds awards "
    "published on Contracts Finder in roughly the last five years. A contract awarded "
    "earlier (long-running waste or highways contracts), one advertised only on Find a "
    "Tender, a framework call-off recorded under another buyer, or an exempt placement "
    "will have no notice here. Expect only a small share of high-value suppliers to match "
    "a notice by name. \"No notice found\" is therefore an indicator to check against the "
    "council's contract register, never evidence of off-contract spend.")


def stop(msg):
    print("STOP:", msg)
    sys.exit(1)


def tag_split(df, pence_col="amount_pence", tag_col="tag"):
    out = {}
    for t in TAGS:
        g = df[df[tag_col] == t]
        out[t] = {"rows": int(len(g)), "gbp": gbp(int(g[pence_col].sum()))}
    return out


def cap_ids(joined):
    """row_ids for analytics.json: first ROW_ID_CAP, with the total; full list is in the CSV."""
    ids = joined.split(";")
    return ids[:ROW_ID_CAP], len(ids)


def tname(t):
    return f"{t['value']:.2f}"


def under(amount_p, t):
    return not triggers(amount_p, t)


def distinctive(norm):
    return frozenset(x for x in norm.split() if len(x) >= 3 and x not in GENERIC)


# ------------------------------------------------------------- matching
def build_matcher(spend_names, notice_names):
    notice_names = sorted(set(notice_names))
    nset = set(notice_names)
    ndist = {n: distinctive(n) for n in notice_names}
    sdist = {s: distinctive(s) for s in spend_names}
    tok_notice, tok_spend = {}, {}
    for d_, cnt in ((ndist, tok_notice), (sdist, tok_spend)):
        for toks in d_.values():
            for tk in toks:
                cnt[tk] = cnt.get(tk, 0) + 1

    def match_supplier(s):
        if s in nset:
            return {"match_class": "exact", "candidate": s, "rule": "normalised names equal",
                    "score": 1.0}
        best, bname = 0.0, None
        sm = SequenceMatcher(None, "", s, autojunk=False)
        for n in notice_names:
            sm.set_seq1(n)
            if sm.real_quick_ratio() < NEAR_RATIO or sm.quick_ratio() < NEAR_RATIO:
                continue
            r = sm.ratio()
            if r > best:
                best, bname = r, n
        if bname is not None and best >= NEAR_RATIO:
            return {"match_class": "near_ratio", "candidate": bname,
                    "rule": f"SequenceMatcher ratio >= {NEAR_RATIO}", "score": round(best, 4)}
        a = sdist[s]
        if a:
            for n in notice_names:
                b = ndist[n]
                if not b:
                    continue
                small, large = (a, b) if len(a) <= len(b) else (b, a)
                if not small <= large:
                    continue
                if len(small) >= 2:
                    return {"match_class": "near_contain", "candidate": n,
                            "rule": "distinctive tokens subset (>= 2 tokens)", "score": None}
                tk = next(iter(small))
                if tok_spend.get(tk, 0) == 1 and tok_notice.get(tk, 0) == 1:
                    return {"match_class": "near_contain", "candidate": n,
                            "rule": "single distinctive token unique on both sides",
                            "score": None}
        return {"match_class": "none", "candidate": None, "rule": None, "score": None}

    return match_supplier


# ------------------------------------------------------------- tests
def test_clustering(df, thresholds, tiers, skipped, rules):
    block = {"description": "payments within 10% below each threshold, with the band the "
                            "same width above it as comparator",
             "parameters": {"band_lower_fraction": BAND[0] / BAND[1],
                            "comparator_upper_fraction": COMPARATOR[0] / COMPARATOR[1],
                            "baseline_fractions": [BASELINE[0][0] / BASELINE[0][1],
                                                   BASELINE[1][0] / BASELINE[1][1]],
                            "boundary_rule": "inclusive threshold: band is 0.9T <= amount < T, "
                                             "comparator T <= amount < 1.1T; exclusive threshold: "
                                             "band is 0.9T <= amount <= T, comparator "
                                             "T < amount <= 1.1T"},
             "rule_ids": sorted({i for t in thresholds for i in t["rule_ids"]}),
             "per_threshold": {}}
    full = []
    a = df["amount_pence"]
    for t in thresholds:
        T = t["value_pence"]
        if t["inclusive"]:
            m_band = (a * BAND[1] >= T * BAND[0]) & (a < T)
            m_comp = (a >= T) & (a * COMPARATOR[1] < T * COMPARATOR[0])
        else:
            m_band = (a * BAND[1] >= T * BAND[0]) & (a <= T)
            m_comp = (a > T) & (a * COMPARATOR[1] <= T * COMPARATOR[0])
        m_base = (a * BASELINE[0][1] >= T * BASELINE[0][0]) & (a * BASELINE[1][1] < T * BASELINE[1][0])
        band, comp, base = df[m_band], df[m_comp], df[m_base]
        conc = (band.groupby("supplier_norm")
                .agg(supplier=("Supplier name", "first"), payments=("amount_pence", "count"),
                     p=("amount_pence", "sum"), tag=("tag", lambda s: s.value_counts().index[0]))
                .sort_values(["payments", "p"], ascending=False).head(TOP))
        top = band.sort_values("amount_pence", ascending=False).head(TOP)
        block["per_threshold"][tname(t)] = {
            "threshold": t["value"], "inclusive": t["inclusive"], "rule_ids": t["rule_ids"],
            "competition_triggering": t["competition_triggering"],
            "band_count": int(len(band)), "band_gbp": gbp(int(band["amount_pence"].sum())),
            "band_distinct_suppliers": int(band["supplier_norm"].nunique()),
            "comparator_count": int(len(comp)), "comparator_gbp": gbp(int(comp["amount_pence"].sum())),
            "baseline_count": int(len(base)), "baseline_gbp": gbp(int(base["amount_pence"].sum())),
            "band_share_of_baseline": (round(len(band) / len(base), 4) if len(base) else None),
            "band_to_comparator_ratio": (round(len(band) / len(comp), 4) if len(comp) else None),
            "band_by_tag": tag_split(band), "comparator_by_tag": tag_split(comp),
            "supplier_concentration_top20": [
                {"supplier": r["supplier"], "payments": int(r["payments"]),
                 "gbp": gbp(int(r["p"])), "tag": r["tag"]} for _, r in conc.iterrows()],
            "top20": [{"row_id": r["row_id"], "supplier": r["Supplier name"],
                       "amount": gbp(int(r["amount_pence"])), "pay_date": r["pay_date"],
                       "service": r["Service"], "narrative": r["Narrative"], "tag": r["tag"]}
                      for _, r in top.iterrows()]}
        b = band.copy()
        b.insert(0, "threshold", t["value"])
        full.append(b)
    for tier in tiers:
        if tier["value"] is None:
            skipped.append({"test": "threshold_clustering", "tier": tier["tier"],
                            "reason": f"parameter {tier['tier']} is null in rules.json"})
    out = pd.concat(full) if full else df.head(0)
    out.to_csv(FULL / "threshold-clustering.csv", index=False)
    block["full_list"] = "outputs/analytics-full/threshold-clustering.csv"
    block["rows_in_full_list"] = int(len(out))
    return block


def test_split(df, thresholds, tiers, floor, skipped, rules):
    block = {"description": "same normalised supplier, two or more payments each under the "
                            "threshold whose calendar dates fall in a 30-day window and whose "
                            "total reaches the threshold",
             "parameters": {"window_days": SPLIT_WINDOW_DAYS,
                            "window_definition": "anchor date through anchor date + "
                                                 f"{SPLIT_WINDOW_DAYS - 1} days, calendar dates",
                            "dedupe": "one window per supplier per threshold: the highest total",
                            "window_tag": "tag carrying the most GBP among the window's payments",
                            "row_id_note": f"top-20 rows list the first {ROW_ID_CAP} row_ids; "
                                           "all are in the CSV",
                            "lower_bound_note": "payments of the publication floor or less are "
                                                "not in the data; results are lower bounds"},
             "rule_ids": sorted({i for t in thresholds if t["competition_triggering"]
                                 for i in t["rule_ids"]}
                                | {r["rule_id"] for r in rules["rules"] if r["type"] == "anti-avoidance"}),
             "per_threshold": {}}
    full = []
    span = timedelta(days=SPLIT_WINDOW_DAYS - 1)
    for t in thresholds:
        if not t["competition_triggering"]:
            continue
        T = t["value_pence"]
        elig = df[df["amount_pence"].map(lambda x: under(x, t))]
        wins = []
        for sup, g in elig.groupby("supplier_norm"):
            if len(g) < 2:
                continue
            best = None
            for d0 in sorted(g["pay_dt"].unique()):
                w = g[(g["pay_dt"] >= d0) & (g["pay_dt"] <= d0 + span)]
                if len(w) < 2:
                    continue
                tot = int(w["amount_pence"].sum())
                if not triggers(tot, t):
                    continue
                if best is None or tot > best[0]:
                    best = (tot, w)
            if best is None:
                continue
            tot, w = best
            w = w.sort_values(["pay_dt", "sheet_row"])
            by_tag = w.groupby("tag")["amount_pence"].sum().sort_values(ascending=False)
            wins.append({"threshold": t["value"], "supplier": w["Supplier name"].iloc[0],
                         "supplier_norm": sup, "window_start": w["pay_dt"].min().isoformat(),
                         "window_end": w["pay_dt"].max().isoformat(),
                         "n_payments": int(len(w)),
                         "distinct_amounts": int(w["amount_pence"].nunique()),
                         "total_pence": tot, "total_gbp": gbp(tot),
                         "largest_payment": gbp(int(w["amount_pence"].max())),
                         "tag": by_tag.index[0], "tags_in_window": ";".join(sorted(by_tag.index)),
                         "services": ";".join(sorted(w["Service"].astype(str).unique())),
                         "row_ids": ";".join(w["row_id"])})
        wdf = pd.DataFrame(wins)
        entry = {"threshold": t["value"], "inclusive": t["inclusive"], "rule_ids": t["rule_ids"],
                 "low_information": None}
        if floor is not None:
            entry["low_information"] = bool(T < 2 * floor["value_pence"])
            entry["threshold_to_floor_ratio"] = round(T / floor["value_pence"], 4)
            entry["floor_rule_ids"] = floor["rule_ids"]
        if len(wdf):
            entry.update({
                "windows": int(len(wdf)), "distinct_suppliers": int(wdf["supplier_norm"].nunique()),
                "gbp": gbp(int(wdf["total_pence"].sum())),
                "by_tag": {tg: {"windows": int((wdf["tag"] == tg).sum()),
                                "gbp": gbp(int(wdf.loc[wdf["tag"] == tg, "total_pence"].sum()))}
                           for tg in TAGS}})
            gp = wdf[wdf["tag"] == "general_procurement"].sort_values("total_pence", ascending=False)
            pl = wdf[wdf["tag"] == "care_or_education_placement"].sort_values("total_pence", ascending=False)
            entry["headline_general_procurement"] = {
                "windows": int(len(gp)), "gbp": gbp(int(gp["total_pence"].sum()))}
            entry["placement_reported_separately"] = {
                "windows": int(len(pl)), "gbp": gbp(int(pl["total_pence"].sum())),
                "note": "periodic care fees legitimately recur"}

            def rows(x):
                out = []
                for _, r in x.head(TOP).iterrows():
                    d = {k: r[k] for k in ("supplier", "window_start", "window_end", "n_payments",
                                           "distinct_amounts", "total_gbp", "largest_payment",
                                           "tag", "tags_in_window")}
                    d["n_services"] = len(r["services"].split(";"))
                    d["row_ids"], d["row_ids_total"] = cap_ids(r["row_ids"])
                    out.append(d)
                return out
            entry["top20"] = rows(gp)
            entry["top20_placement"] = rows(pl)
            full.append(wdf)
        else:
            entry.update({"windows": 0, "distinct_suppliers": 0, "gbp": 0.0,
                          "by_tag": {tg: {"windows": 0, "gbp": 0.0} for tg in TAGS},
                          "headline_general_procurement": {"windows": 0, "gbp": 0.0},
                          "placement_reported_separately": {"windows": 0, "gbp": 0.0},
                          "top20": [], "top20_placement": []})
        block["per_threshold"][tname(t)] = entry
    for tier in tiers:
        if tier["value"] is None and tier["competition_triggering"]:
            skipped.append({"test": "split_purchases", "tier": tier["tier"],
                            "reason": f"parameter {tier['tier']} is null in rules.json"})
    out = pd.concat(full) if full else pd.DataFrame()
    out.drop(columns=["total_pence"], errors="ignore").to_csv(FULL / "split-purchases.csv", index=False)
    block["full_list"] = "outputs/analytics-full/split-purchases.csv"
    return block


def supplier_table(df, months):
    rows = []
    for sup, g in df.groupby("supplier_norm"):
        by_tag = g.groupby("tag")["amount_pence"].sum().sort_values(ascending=False)
        by_narr = g.groupby("Narrative")["amount_pence"].sum().sort_values(ascending=False)
        by_svc = g.groupby("Service")["amount_pence"].sum().sort_values(ascending=False)
        tot = int(g["amount_pence"].sum())
        big = g.sort_values("amount_pence", ascending=False).head(3)
        rows.append({"supplier_norm": sup,
                     "supplier": g["Supplier name"].value_counts().index[0],
                     "n_payments": int(len(g)), "total_pence": tot, "total_gbp": gbp(tot),
                     "annualised_pence": tot * 12 / months,
                     "annualised_estimate": round(tot * 12 / months / 100, 2),
                     "dominant_tag": by_tag.index[0],
                     "dominant_tag_share": round(int(by_tag.iloc[0]) / tot, 4),
                     "spans_several_tags": bool(len(by_tag) > 1),
                     "tags": ";".join(by_tag.index),
                     "main_narrative": by_narr.index[0], "main_service": by_svc.index[0],
                     "n_services": int(len(by_svc)),
                     "largest_payment_row_ids": ";".join(big["row_id"])})
    return pd.DataFrame(rows)


def hv_rows(x, extra=()):
    cols = ["supplier", "annualised_estimate", "total_gbp", "n_payments", "main_narrative",
            "main_service", "dominant_tag", "spans_several_tags", "largest_payment_row_ids"] + list(extra)
    out = []
    for _, r in x.head(TOP).iterrows():
        d = {k: r[k] for k in cols}
        d["largest_payment_row_ids"] = d["largest_payment_row_ids"].split(";")
        for k, v in list(d.items()):
            if isinstance(v, float) and pd.isna(v):
                d[k] = None
        out.append(d)
    return out


def test_high_value(sup, pub, tiers, months, skipped):
    hv = sup[sup["annualised_pence"].map(lambda p: triggers(p, pub))].copy()
    hv = hv.sort_values("annualised_pence", ascending=False)
    by_tag = {}
    for t in TAGS:
        g = hv[hv["dominant_tag"] == t]
        by_tag[t] = {"suppliers": int(len(g)), "gbp": gbp(int(g["total_pence"].sum())),
                     "annualised_estimate_gbp": round(float(g["annualised_pence"].sum()) / 100, 2)}
    block = {"description": "suppliers whose annualised estimate is at or above the publication "
                            "threshold; the population for which contract evidence is requested "
                            "during fieldwork",
             "parameters": {"publication_threshold": pub["value"],
                            "publication_threshold_inclusive": pub["inclusive"],
                            "months_covered": months, "annualisation_factor": round(12 / months, 6),
                            "annualised_estimate": "supplier total x (12 / months_covered)",
                            "class": "dominant tag = tag carrying the most GBP for the supplier"},
             "rule_ids": pub.get("publication_rule_ids", []) + [i for i in pub["rule_ids"]
                                                                if i not in pub.get("publication_rule_ids", [])],
             "suppliers_total": int(len(sup)),
             "suppliers_at_or_above_publication_threshold": int(len(hv)),
             "gbp": gbp(int(hv["total_pence"].sum())),
             "annualised_estimate_gbp": round(float(hv["annualised_pence"].sum()) / 100, 2),
             "suppliers_spanning_several_tags": int(hv["spans_several_tags"].sum()),
             "by_tag": by_tag,
             "headline_general_procurement": by_tag["general_procurement"],
             "top20": hv_rows(hv[hv["dominant_tag"] == "general_procurement"]),
             "top20_care_or_education_placement": hv_rows(hv[hv["dominant_tag"] == "care_or_education_placement"]),
             "top20_grant": hv_rows(hv[hv["dominant_tag"] == "grant"]),
             "top20_agency_staff": hv_rows(hv[hv["dominant_tag"] == "agency_staff"]),
             "top20_premises": hv_rows(hv[hv["dominant_tag"] == "premises"]),
             "named_tiers": {},
             "full_list": "outputs/analytics-full/high-value-suppliers.csv"}
    for tier in tiers:
        if tier["value"] is None:
            skipped.append({"test": "high_value_suppliers", "tier": tier["tier"],
                            "reason": f"parameter {tier['tier']} is null in rules.json"})
            block["named_tiers"][tier["tier"]] = {"skipped": True,
                                                  "reason": f"parameter {tier['tier']} is null in rules.json"}
        else:
            tp = int(round(float(tier["value"]) * 100))
            g = hv[hv["annualised_pence"] > tp]
            block["named_tiers"][tier["tier"]] = {
                "value": tier["value"], "suppliers_above": int(len(g)),
                "gbp": gbp(int(g["total_pence"].sum()))}
    return hv, block


def test_duplicates(df):
    groups, full = [], []
    gid = 0
    for (sup, amt), g in df.groupby(["supplier_norm", "amount_pence"]):
        if len(g) < 2:
            continue
        g = g.sort_values(["pay_dt", "Date", "sheet_row"])
        chain = [g.index[0]]
        chains = []
        prev = g["pay_dt"].iloc[0]
        for idx, d0 in zip(g.index[1:], g["pay_dt"].iloc[1:]):
            if (d0 - prev).days <= DUP_DAYS:
                chain.append(idx)
            else:
                chains.append(chain)
                chain = [idx]
            prev = d0
        chains.append(chain)
        for ch in chains:
            if len(ch) < 2:
                continue
            w = g.loc[ch]
            gid += 1
            tier = "same_timestamp" if w["Date"].nunique() == 1 else "different_time"
            tag = w["tag"].value_counts().index[0]
            groups.append({"group_id": gid, "tier": tier, "supplier": w["Supplier name"].iloc[0],
                           "supplier_norm": sup, "amount_pence": int(amt), "amount": gbp(int(amt)),
                           "n_rows": int(len(w)), "distinct_timestamps": int(w["Date"].nunique()),
                           "first_date": w["pay_dt"].min().isoformat(),
                           "last_date": w["pay_dt"].max().isoformat(),
                           "beyond_first_pence": int(amt) * (len(w) - 1),
                           "gbp_beyond_first": gbp(int(amt) * (len(w) - 1)),
                           "tag": tag, "services": ";".join(sorted(w["Service"].astype(str).unique())),
                           "narratives": ";".join(sorted(w["Narrative"].astype(str).unique())),
                           "row_ids": ";".join(w["row_id"])})
            x = w.copy()
            x.insert(0, "tier", tier)
            x.insert(0, "group_id", gid)
            full.append(x)
    gdf = pd.DataFrame(groups)
    block = {"description": "same normalised supplier, same amount to the penny, calendar dates "
                            "within 7 days",
             "parameters": {"days": DUP_DAYS,
                            "grouping": "rows chained while the gap to the previous payment date "
                                        f"is <= {DUP_DAYS} days",
                            "tiers": {"same_timestamp": "every row in the group has an identical "
                                                        "Date to the millisecond",
                                      "different_time": "at least two distinct timestamps"},
                            "group_tag": "most frequent tag among the group's rows"},
             "rule_ids": [],
             "rule_note": "no clause of the Contract Rules sets a duplicate-payment test; this is "
                          "a payment-control indicator",
             "row_id_note": f"top-20 rows list the first {ROW_ID_CAP} row_ids; all are in the CSV",
             "per_tier": {},
             "full_list": "outputs/analytics-full/duplicates.csv",
             "groups_file": "outputs/analytics-full/duplicate-groups.csv"}
    for tier in ("same_timestamp", "different_time"):
        g = gdf[gdf["tier"] == tier] if len(gdf) else gdf
        e = {"groups": int(len(g)), "rows": int(g["n_rows"].sum()) if len(g) else 0,
             "gbp_beyond_first": gbp(int(g["beyond_first_pence"].sum())) if len(g) else 0.0,
             "by_tag": {tg: {"groups": int((g["tag"] == tg).sum()) if len(g) else 0,
                             "rows": int(g.loc[g["tag"] == tg, "n_rows"].sum()) if len(g) else 0,
                             "gbp_beyond_first": gbp(int(g.loc[g["tag"] == tg, "beyond_first_pence"].sum())) if len(g) else 0.0}
                        for tg in TAGS}}

        def rows(x):
            out = []
            for _, r in x.head(TOP).iterrows():
                d = {k: r[k] for k in ("supplier", "amount", "n_rows", "distinct_timestamps",
                                       "first_date", "last_date", "gbp_beyond_first", "tag",
                                       "narratives")}
                d["row_ids"], d["row_ids_total"] = cap_ids(r["row_ids"])
                out.append(d)
            return out
        if len(g):
            s = g.sort_values("amount_pence", ascending=False)
            e["headline_general_procurement"] = e["by_tag"]["general_procurement"]
            e["placement_reported_separately"] = e["by_tag"]["care_or_education_placement"]
            e["top20"] = rows(s[s["tag"] == "general_procurement"])
            e["top20_placement"] = rows(s[s["tag"] == "care_or_education_placement"])
        else:
            e.update({"top20": [], "top20_placement": []})
        block["per_tier"][tier] = e
    (pd.concat(full) if full else df.head(0)).drop(columns=["pay_dt"], errors="ignore").to_csv(
        FULL / "duplicates.csv", index=False)
    gdf.drop(columns=["amount_pence", "beyond_first_pence"], errors="ignore").to_csv(
        FULL / "duplicate-groups.csv", index=False)
    return block


def main():
    rules = load_rules()
    th = derive_thresholds(rules)
    thresholds, tiers, pub, floor = th["thresholds"], th["tiers"], th["publication"], th["floor"]
    if not any(t["competition_triggering"] for t in thresholds):
        stop("rules.json has no numeric competition-triggering threshold")
    if pub is None:
        stop("rules.json has no numeric Appendix B advertising threshold (publication threshold)")
    log = json.loads((FULL / "cleaning-log.json").read_text())
    months = log["months_covered"]
    df = pd.read_csv(FULL / "spend-clean.csv", dtype={"Date": str})
    df["pay_dt"] = pd.to_datetime(df["pay_date"], format="%Y-%m-%d").dt.date
    cinfo = log["contracts"]
    contracts_present = bool(cinfo.get("contracts_present"))
    register_present = bool(cinfo.get("register_present"))
    skipped = []
    tests = {}

    tests["threshold_clustering"] = test_clustering(df, thresholds, tiers, skipped, rules)
    tests["split_purchases"] = test_split(df, thresholds, tiers, floor, skipped, rules)

    sup = supplier_table(df, months)
    hv, hv_block = test_high_value(sup, pub, tiers, months, skipped)
    tests["high_value_suppliers"] = hv_block

    matching = {"skipped": True, "reason": "no contracts.csv or contract register in data/"}
    row_d_ids = rule_ids_for_clause(rules, "App C row D")
    row_e_ids = rule_ids_for_clause(rules, "App C row E")
    row_f_ids = rule_ids_for_clause(rules, "App C row F")
    grant_clause = [e["clause"] for e in rules.get("excluded", []) if str(e.get("clause")) == "1.6"]

    if contracts_present or register_present:
        nc = pd.read_csv(FULL / "notices-clean.csv", dtype={"companies_house_no": str})
        for c in ("contract_start", "contract_end"):
            nc[c + "_d"] = pd.to_datetime(nc[c], format="%Y-%m-%d").dt.date
        active = nc[nc["active_in_window"]]
        ended = nc[nc["ended_before_window"]]
        match_supplier = build_matcher(sup["supplier_norm"].tolist(), active["supplier_norm"].tolist())
        act_ids = active.groupby("supplier_norm")["notice_id"].agg(lambda s: ";".join(sorted(set(s))))
        res = []
        for s in sup["supplier_norm"]:
            m = match_supplier(s)
            m["supplier_norm"] = s
            m["candidate_notice_ids"] = act_ids.get(m["candidate"]) if m["candidate"] else None
            res.append(m)
        mt = pd.DataFrame(res).merge(
            sup[["supplier_norm", "supplier", "total_gbp", "annualised_estimate", "dominant_tag",
                 "n_payments"]], on="supplier_norm")
        mt = mt[["supplier", "supplier_norm", "match_class", "candidate", "rule", "score",
                 "candidate_notice_ids", "total_gbp", "annualised_estimate", "dominant_tag",
                 "n_payments"]]
        mt.to_csv(FULL / "supplier-match.csv", index=False)
        mt[mt["match_class"].isin(["near_ratio", "near_contain"])].sort_values(
            "annualised_estimate", ascending=False).to_csv(FULL / "near-matches.csv", index=False)
        vc = mt["match_class"].value_counts()
        matching = {"spend_suppliers": int(len(mt)),
                    "matched_against": "suppliers on notices active in the spend window",
                    "active_notice_suppliers": int(active["supplier_norm"].nunique()),
                    "exact": int(vc.get("exact", 0)), "near_ratio": int(vc.get("near_ratio", 0)),
                    "near_contain": int(vc.get("near_contain", 0)), "none": int(vc.get("none", 0)),
                    "near_ratio_minimum": NEAR_RATIO,
                    "note": "near matches are candidates for the auditor to confirm and are not "
                            "counted as matches anywhere",
                    "supplier_match_file": "outputs/analytics-full/supplier-match.csv",
                    "near_matches_file": "outputs/analytics-full/near-matches.csv"}

        hv = hv.merge(mt[["supplier_norm", "match_class", "candidate", "rule", "score",
                          "candidate_notice_ids"]], on="supplier_norm", how="left")
        hv = hv.sort_values("annualised_pence", ascending=False)
        per_class = {}
        for c in ("exact", "near_ratio", "near_contain", "none"):
            g = hv[hv["match_class"] == c]
            per_class[c] = {"suppliers": int(len(g)), "gbp": gbp(int(g["total_pence"].sum())),
                            "annualised_estimate_gbp": round(float(g["annualised_pence"].sum()) / 100, 2)}
        un = hv[hv["match_class"] != "exact"]
        un_by_tag = {}
        for t in TAGS:
            g = un[un["dominant_tag"] == t]
            un_by_tag[t] = {"suppliers": int(len(g)), "gbp": gbp(int(g["total_pence"].sum())),
                            "annualised_estimate_gbp": round(float(g["annualised_pence"].sum()) / 100, 2),
                            "of_which_near_match_candidates": int(g["match_class"].isin(["near_ratio", "near_contain"]).sum())}
        ex_by_tag = {t: int(((hv["match_class"] == "exact") & (hv["dominant_tag"] == t)).sum()) for t in TAGS}
        tests["off_contract"] = {
            "description": "high-value suppliers with no exact name match to a supplier on a "
                           "Contracts Finder notice active in the spend window",
            "parameters": {"population": "suppliers at or above the publication threshold only",
                           "publication_threshold": pub["value"],
                           "unmatched_definition": "match class is not exact (near_ratio, "
                                                   "near_contain and none); near matches are "
                                                   "candidates to confirm, not matches",
                           "companies_house_key": "kept on the notice side; the spend data carries "
                                                  "no company number, so matching is by name only"},
            "rule_ids": pub.get("publication_rule_ids", []) + row_f_ids,
            "context_rules": {"App C row F (placements excluded from competition)": row_f_ids,
                              "clause 1.6 (grant treated as a contract; excluded definition)": grant_clause},
            "contracts_present": contracts_present, "register_present": register_present,
            "caveat": CAVEAT,
            "suppliers_classed": int(len(hv)),
            "by_match_class": per_class,
            "exact_by_tag": ex_by_tag,
            "unmatched": {"suppliers": int(len(un)), "gbp": gbp(int(un["total_pence"].sum())),
                          "annualised_estimate_gbp": round(float(un["annualised_pence"].sum()) / 100, 2)},
            "unmatched_by_tag": un_by_tag,
            "headline_general_procurement": un_by_tag["general_procurement"],
            "placement_reported_separately": un_by_tag["care_or_education_placement"],
            "top20": hv_rows(un[un["dominant_tag"] == "general_procurement"],
                             extra=("match_class", "candidate", "candidate_notice_ids")),
            "full_list": "outputs/analytics-full/high-value-suppliers.csv"}

        # ---- test 5: expired notice spend
        all_ids = nc.groupby("supplier_norm")
        rows5 = []
        for _, r in hv.iterrows():
            s = r["supplier_norm"]
            if s not in all_ids.groups:
                continue
            g = all_ids.get_group(s)
            if not g["ended_before_window"].all():
                continue
            last = g.sort_values("contract_end_d").iloc[-1]
            rows5.append({"supplier": r["supplier"], "supplier_norm": s,
                          "annualised_estimate": r["annualised_estimate"], "total_gbp": r["total_gbp"],
                          "total_pence": r["total_pence"], "annualised_pence": r["annualised_pence"],
                          "n_payments": r["n_payments"], "dominant_tag": r["dominant_tag"],
                          "main_narrative": r["main_narrative"], "main_service": r["main_service"],
                          "matched_notices": int(g["notice_id"].nunique()),
                          "latest_end_date": last["contract_end"],
                          "notice_id": last["notice_id"], "notice_title": last["title"],
                          "procedure_type": last["procedure_type"],
                          "all_notice_ids": ";".join(sorted(set(g["notice_id"]))),
                          "largest_payment_row_ids": r["largest_payment_row_ids"]})
        t5 = pd.DataFrame(rows5)
        b5 = {"description": "suppliers at or above the publication threshold with an exact name "
                             "match to one or more notices, every one of which ended before the "
                             "spend window starts",
              "parameters": {"window_start": log["date_min"], "match": "exact normalised name, "
                             "against all council notices", "publication_threshold": pub["value"]},
              "rule_ids": row_d_ids,
              "caveat": "a newer contract may exist with no notice on Contracts Finder; extensions "
                        "fall under Appendix C row D. " + CAVEAT,
              "count": int(len(t5)),
              "gbp": gbp(int(t5["total_pence"].sum())) if len(t5) else 0.0,
              "annualised_estimate_gbp": round(float(t5["annualised_pence"].sum()) / 100, 2) if len(t5) else 0.0,
              "by_tag": {t: {"suppliers": int((t5["dominant_tag"] == t).sum()) if len(t5) else 0,
                             "gbp": gbp(int(t5.loc[t5["dominant_tag"] == t, "total_pence"].sum())) if len(t5) else 0.0}
                         for t in TAGS},
              "top20": [], "full_list": "outputs/analytics-full/expired-notice-spend.csv"}
        if len(t5):
            t5 = t5.sort_values("annualised_pence", ascending=False)
            b5["top20"] = [{**{k: r[k] for k in ("supplier", "annualised_estimate", "total_gbp",
                                                  "n_payments", "dominant_tag", "main_narrative",
                                                  "latest_end_date", "notice_id", "notice_title",
                                                  "matched_notices")},
                            "largest_payment_row_ids": r["largest_payment_row_ids"].split(";")}
                           for _, r in t5.head(TOP).iterrows()]
        t5.drop(columns=["total_pence", "annualised_pence"], errors="ignore").to_csv(
            FULL / "expired-notice-spend.csv", index=False)
        tests["expired_notice_spend"] = b5

        # ---- test 6: spend vs award
        rows6, not_computable = [], 0
        cand = 0
        for _, r in sup.merge(mt[["supplier_norm", "match_class"]],
                              on="supplier_norm").iterrows():
            if r["match_class"] != "exact":
                continue
            g = active[active["supplier_norm"] == r["supplier_norm"]]
            if g["notice_id"].nunique() != 1:
                continue
            n = g.iloc[0]
            if int(n["suppliers_on_notice"]) != 1 or not float(n["awarded_value"]) > 0:
                continue
            cand += 1
            if pd.isna(n["contract_start_d"]) or pd.isna(n["contract_end_d"]) \
                    or n["contract_end_d"] <= n["contract_start_d"]:
                not_computable += 1
                continue
            days = (n["contract_end_d"] - n["contract_start_d"]).days + 1
            years = days / 365.25
            rate = float(n["awarded_value"]) / years
            ratio = (r["annualised_pence"] / 100) / rate
            rows6.append({"supplier": r["supplier"], "supplier_norm": r["supplier_norm"],
                          "annualised_estimate": r["annualised_estimate"], "total_gbp": r["total_gbp"],
                          "total_pence": r["total_pence"],
                          "n_payments": r["n_payments"], "dominant_tag": r["dominant_tag"],
                          "notice_id": n["notice_id"], "notice_title": n["title"],
                          "procedure_type": n["procedure_type"],
                          "awarded_value": float(n["awarded_value"]),
                          "contract_start": n["contract_start"], "contract_end": n["contract_end"],
                          "contract_years": round(years, 4), "award_annual_rate": round(rate, 2),
                          "ratio": round(ratio, 4), "flag": bool(ratio >= SPEND_VS_AWARD_RATIO),
                          "largest_payment_row_ids": r["largest_payment_row_ids"]})
        t6 = pd.DataFrame(rows6)
        fl = t6[t6["flag"]].sort_values("ratio", ascending=False) if len(t6) else t6
        tests["spend_vs_award"] = {
            "description": "annualised estimate against the yearly rate of the award, for "
                           "suppliers with an exact match to exactly one active single-supplier "
                           "notice with an awarded value above zero",
            "parameters": {"ratio_minimum": SPEND_VS_AWARD_RATIO,
                           "contract_years": "(contract end - contract start + 1 day) / 365.25",
                           "award_annual_rate": "Awarded Value / contract years",
                           "ratio": "annualised estimate / award_annual_rate"},
            "rule_ids": row_e_ids,
            "caveat": "award values may be estimates or maxima, and the three-month window may "
                      "not be typical of the year; variations fall under Appendix C row E",
            "suppliers_eligible": int(cand), "not_computable_dates": int(not_computable),
            "suppliers_compared": int(len(t6)),
            "count": int(len(fl)),
            "gbp": gbp(int(fl["total_pence"].sum())) if len(fl) else 0.0,
            "by_tag": {t: {"suppliers": int((fl["dominant_tag"] == t).sum()) if len(fl) else 0,
                           "gbp": gbp(int(fl.loc[fl["dominant_tag"] == t, "total_pence"].sum())) if len(fl) else 0.0}
                       for t in TAGS},
            "top20": [{**{k: r[k] for k in ("supplier", "ratio", "annualised_estimate", "total_gbp",
                                             "award_annual_rate", "awarded_value", "contract_start",
                                             "contract_end", "contract_years", "notice_id",
                                             "notice_title", "dominant_tag", "n_payments")},
                       "largest_payment_row_ids": r["largest_payment_row_ids"].split(";")}
                      for _, r in fl.head(TOP).iterrows()],
            "full_list": "outputs/analytics-full/spend-vs-award.csv"}
        (t6.sort_values("ratio", ascending=False) if len(t6) else t6).drop(
            columns=["total_pence"], errors="ignore").to_csv(FULL / "spend-vs-award.csv", index=False)
    else:
        reason = "no contracts.csv or contract register in data/"
        if cinfo.get("reason"):
            reason += f" ({cinfo['reason']})"
        for name in ("off_contract", "expired_notice_spend", "spend_vs_award"):
            tests[name] = {"skipped": True, "reason": reason}
            skipped.append({"test": name, "tier": "", "reason": reason})

    hv.drop(columns=["total_pence", "annualised_pence"]).to_csv(
        FULL / "high-value-suppliers.csv", index=False)

    tests["duplicates"] = test_duplicates(df)
    tests = {k: tests[k] for k in ("threshold_clustering", "split_purchases", "high_value_suppliers",
                                   "off_contract", "duplicates", "expired_notice_spend",
                                   "spend_vs_award")}

    tags = {}
    for t in TAGS:
        g = df[df["tag"] == t]
        tags[t] = {"rows": int(len(g)), "gbp": gbp(int(g["amount_pence"].sum())),
                   "suppliers": int(g["supplier_norm"].nunique())}
    contracts = {"contracts_present": contracts_present, "register_present": register_present,
                 "caveat": CAVEAT}
    for k in ("rows_in_file", "rows_for_council", "organisation_names_kept",
              "rows_dropped_other_buyers", "notice_supplier_pairs", "distinct_suppliers",
              "distinct_suppliers_active", "active_in_window", "ended_before_window",
              "not_yet_started", "zero_value_awards", "multi_supplier_notices", "rows_per_year",
              "published_range", "warnings", "notes", "reason"):
        if k in cinfo:
            contracts[k] = cinfo[k]
    if not register_present:
        contracts["register_note"] = ("data/contract-register.csv is absent: no notice-based "
                                      "result has been checked against the council's own register")
    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scripts": ["scripts/clean.py", "scripts/analyse.py"],
        "population": {
            "files": [f["file"] for f in log["files"]],
            "rows_raw": log["rows_raw"], "gbp_raw": log["gbp_raw"],
            "rows_after_exclusions": int(len(df)),
            "date_min": log["date_min"], "date_max": log["date_max"],
            "months_covered": months, "annualisation_factor": round(12 / months, 6),
            "total_gbp": gbp(int(df["amount_pence"].sum())),
            "suppliers": int(df["supplier_norm"].nunique()),
            "excluded": {k: {"rows": v["rows"], "gbp": v["gbp"], "reason": v["reason"],
                             "regex": v["regex"]} for k, v in log["excluded"].items()},
            "tags": tags,
            "rows_dated_outside_file_month": log["rows_dated_outside_file_month"],
            "blank_expenditure_category_rows": sum(f["blank_expenditure_category"] for f in log["files"]),
            "limitations": [
                "population is expenditure over the publication floor only "
                f"(GBP {floor['value'] if floor else 'n/a'}, {floor['rule_ids'] if floor else ''}); "
                "smaller payments are invisible, so split-purchase and duplicate results are lower bounds",
                "Date is a payment-run timestamp, not an invoice date",
                "supplier 'Redacted' rows are excluded from every test",
                "annualised estimate = total x (12 / months_covered); three months may not be typical"]},
        "thresholds": [{k: t[k] for k in ("value", "inclusive", "inclusive_meaning",
                                          "inclusivity_conflict", "as_printed",
                                          "competition_triggering", "publication_threshold",
                                          "rule_ids", "citations")} for t in thresholds],
        "threshold_source": {"rule_types_used": ["procedure", "approval", "waiver", "anti-avoidance"],
                             "publication_threshold": {"value": pub["value"],
                                                       "rule_ids": pub.get("publication_rule_ids", [])},
                             "publication_floor": floor,
                             "named_tiers": tiers, "null_parameters": th["null_parameters"]},
        "skipped": skipped,
        "contracts": contracts,
        "matching": matching,
        "tests": tests,
    }
    (OUT / "analytics.json").write_text(json.dumps(out, indent=1, default=str))
    print("analyse.py done; skipped entries:", len(skipped))


if __name__ == "__main__":
    main()
