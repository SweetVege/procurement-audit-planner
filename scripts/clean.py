"""Step 2: clean spend workbooks and the Contracts Finder export.

Writes to outputs/analytics-full/: spend-clean.csv, spend-excluded.csv,
notices-clean.csv (if contracts.csv present), cleaning-log.json.
Reads data/ only; never writes there. All four files are recreated each run.
"""
import json
import sys
from datetime import datetime

import pandas as pd

from common import (CONTRACTS, EXPECTED_COLS, FULL, REGISTER, SHEET, SPEND_DIR,
                    TAGS, gbp, load_rules, normalise_supplier)

MIN_COUNCIL_NOTICES = 20
EXPORT_CAP_ROWS = 1000
COUNCIL_NAMES = {"west berkshire council", "west berkshire"}  # compared lower-cased
SUPPLIER_COL = "Supplier [Name|Address|Ref type|Ref Number|Is SME|Is VCSE]"

RE_PENSION = r"LGPS|PENSION|SUPERANNUATION"
RE_INTER_SUPPLIER = (r"\b(?:COUNCIL|BOROUGH|COUNTY|CNCL|NHS|POLICE|FIRE AUTHORITY|"
                     r"FIRE AND RESCUE|HMRC|HM REVENUE|DEPARTMENT FOR|MINISTRY OF)\b")
RE_INTER_NARR = r"JOINT ARRANGEMENTS"
EXCLUSIONS = [  # order matters: first match wins
    ("redacted_supplier",
     "Supplier name is 'Redacted': many payees under one label, unusable in supplier-level tests",
     "supplier == 'redacted' (case-insensitive)"),
    ("pension_statutory",
     "Statutory pension contributions, not procurement",
     f"Narrative ~ {RE_PENSION}"),
    ("inter_authority",
     "Payment to another public body or a joint arrangement (and narrative is not "
     "'Private Contractors'): not a purchase from the market",
     f"(Supplier ~ {RE_INTER_SUPPLIER} OR Narrative ~ {RE_INTER_NARR}) AND Narrative != 'Private Contractors'"),
]

PLACEMENT_SERVICE_PREFIXES = ("Adult Social Care", "Children's Social Care", "Education")
PLACEMENT_NARRATIVES = {"private contractors", "other agencies", "voluntary associations",
                        "direct payment", "allowances for provision care",
                        "adult placement allowances"}
RE_GRANT = r"GRANT"
RE_AGENCY = r"AGENCY & TEMPORARY STAFF"
RE_PREMISES = r"RENT|RATES|LEASE"


def stop(msg):
    print("STOP:", msg)
    sys.exit(1)


def load_spend(log):
    files = sorted(SPEND_DIR.glob("*.xlsx"))
    if not files:
        stop("no spend workbooks in data/spend/")
    frames = []
    for f in files:
        xl = pd.ExcelFile(f)
        if SHEET not in xl.sheet_names:
            stop(f"{f.name}: sheet '{SHEET}' not found (sheets: {xl.sheet_names})")
        raw = pd.read_excel(f, sheet_name=SHEET, header=None)
        hits = raw.index[raw.iloc[:, 0].astype(str).str.strip() == "Service"].tolist()
        if len(hits) != 1:
            stop(f"{f.name}: expected one header row starting 'Service', found {len(hits)}")
        h = hits[0]
        df = pd.read_excel(f, sheet_name=SHEET, header=h)
        cols = [str(c).strip() for c in df.columns]
        if cols != EXPECTED_COLS:
            stop(f"{f.name}: columns {cols} != expected {EXPECTED_COLS}")
        df.columns = cols
        df["source_file"] = f.name
        df["sheet_row"] = df.index + h + 2          # worksheet row as Excel shows it
        blank = df[EXPECTED_COLS].isna().all(axis=1)
        df = df[~blank].copy()
        df["row_id"] = df["source_file"] + ":" + df["sheet_row"].astype(str)
        date_kind = "datetime"
        if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
            date_kind = "text, parsed %m/%d/%y"
            try:
                df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%y")
            except Exception as e:
                stop(f"{f.name}: Date failed to parse as %m/%d/%y: {e}")
        if not pd.api.types.is_numeric_dtype(df["Net amount"]):
            stop(f"{f.name}: Net amount is not numeric")
        for c in ("Date", "Net amount", "Supplier name"):
            n = int(df[c].isna().sum())
            if n:
                stop(f"{f.name}: {n} null values in '{c}'")
        neg = int((df["Net amount"] < 0).sum())
        if neg:
            log["negative_amounts"] = {f.name: neg}
            (FULL / "cleaning-log.json").write_text(json.dumps(log, indent=1))
            stop(f"{f.name}: {neg} negative amounts")
        log["files"].append({
            "file": f.name, "sheet": SHEET, "header_sheet_row": h + 1,
            "rows": len(df), "blank_rows_dropped": int(blank.sum()),
            "date_type": date_kind,
            "gbp": round(float(df["Net amount"].sum()), 2),
            "blank_expenditure_category": int(df["Expenditure category"].isna().sum())})
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["pay_date"] = df["Date"].dt.date
    df["amount_pence"] = (df["Net amount"] * 100).round().astype("int64")
    resid = float(((df["Net amount"] * 100) - df["amount_pence"]).abs().max())
    if resid > 1e-4:
        stop(f"Net amount has sub-penny values (max residual {resid})")
    if df["row_id"].duplicated().any():
        stop("duplicate row_id")
    return df


def exclude_and_tag(df, log):
    sup_u = (df["Supplier name"].astype(str).str.upper()
             .str.replace("&", " AND ", regex=False).str.replace(r"\s+", " ", regex=True))
    narr = df["Narrative"].fillna("").astype(str)
    is_red = df["Supplier name"].astype(str).str.strip().str.lower() == "redacted"
    is_pen = narr.str.contains(RE_PENSION, case=False, regex=True)
    is_inter = ((sup_u.str.contains(RE_INTER_SUPPLIER, regex=True)
                 | narr.str.contains(RE_INTER_NARR, case=False, regex=True))
                & (narr.str.strip().str.lower() != "private contractors"))
    cat = pd.Series("", index=df.index)
    for name, mask in (("redacted_supplier", is_red), ("pension_statutory", is_pen),
                       ("inter_authority", is_inter)):
        cat = cat.mask((cat == "") & mask, name)
    df["exclusion"] = cat
    log["excluded"] = {}
    for name, reason, rx in EXCLUSIONS:
        m = df["exclusion"] == name
        log["excluded"][name] = {"rows": int(m.sum()),
                                 "gbp": gbp(int(df.loc[m, "amount_pence"].sum())),
                                 "reason": reason, "regex": rx}
    log["exclusion_order"] = [e[0] for e in EXCLUSIONS]
    ia = df[df["exclusion"] == "inter_authority"]
    log["inter_authority_top_suppliers"] = [
        {"supplier": k, "rows": int(v["n"]), "gbp": gbp(int(v["p"]))}
        for k, v in ia.groupby("Supplier name")["amount_pence"].agg(n="count", p="sum")
        .sort_values("p", ascending=False).head(20).iterrows()]

    excl = df[df["exclusion"] != ""].copy()
    clean = df[df["exclusion"] == ""].copy()

    svc = clean["Service"].fillna("").astype(str)
    n = clean["Narrative"].fillna("").astype(str)
    m_place = (svc.str.startswith(PLACEMENT_SERVICE_PREFIXES)
               & n.str.strip().str.lower().isin(PLACEMENT_NARRATIVES))
    m_grant = n.str.contains(RE_GRANT, case=False, regex=True)
    m_agency = n.str.contains(RE_AGENCY, case=False, regex=True)
    m_prem = n.str.contains(RE_PREMISES, case=False, regex=True)
    tag = pd.Series("general_procurement", index=clean.index)
    done = pd.Series(False, index=clean.index)
    for name, mask in (("care_or_education_placement", m_place), ("grant", m_grant),
                       ("agency_staff", m_agency), ("premises", m_prem)):
        tag = tag.mask(~done & mask, name)
        done = done | mask
    clean["tag"] = tag
    clean["supplier_norm"] = clean["Supplier name"].map(normalise_supplier)
    empty = clean["supplier_norm"] == ""
    log["empty_normalised_names"] = int(empty.sum())
    if empty.any():
        clean.loc[empty, "supplier_norm"] = clean.loc[empty, "Supplier name"].str.upper().str.strip()
    log["tagging_rules"] = {
        "order": ["care_or_education_placement", "grant", "agency_staff", "premises",
                  "general_procurement"],
        "care_or_education_placement": {"service_startswith": list(PLACEMENT_SERVICE_PREFIXES),
                                        "narrative_in": sorted(PLACEMENT_NARRATIVES)},
        "grant": RE_GRANT, "agency_staff": RE_AGENCY, "premises": RE_PREMISES,
        "note": "regexes are case-insensitive and applied to Narrative; first match wins"}
    log["tags"] = {}
    for t in TAGS:
        g = clean[clean["tag"] == t]
        log["tags"][t] = {"rows": len(g), "gbp": gbp(int(g["amount_pence"].sum())),
                          "suppliers": int(g["supplier_norm"].nunique())}
    if sum(v["rows"] for v in log["tags"].values()) != len(clean):
        stop("tag split does not add up to the cleaned row count")
    # narrative -> tag map with rows and GBP, for review of mis-tags
    nt = (clean.groupby(["tag", "Narrative"])["amount_pence"].agg(n="count", p="sum")
          .reset_index().sort_values("p", ascending=False))
    log["narratives_by_tag"] = {
        t: [{"narrative": r["Narrative"], "rows": int(r["n"]), "gbp": gbp(int(r["p"]))}
            for _, r in nt[nt["tag"] == t].iterrows()]
        for t in TAGS}
    log["transfer_payment_rows_kept"] = int(
        (clean["Expenditure category"].fillna("") == "Transfer Payment").sum())
    return clean, excl


def parse_iso(s):
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))


def load_notices(window_start, window_end, log):
    c = {"contracts_present": CONTRACTS.exists(), "register_present": REGISTER.exists(),
         "warnings": []}
    log["contracts"] = c
    if REGISTER.exists():
        stop("data/contract-register.csv is present but no column mapping has been "
             "confirmed for it; inspect its header and extend clean.py")
    if not CONTRACTS.exists():
        c["reason"] = "data/contracts.csv not found"
        return None
    raw = pd.read_csv(CONTRACTS, dtype=str, keep_default_na=False)
    need = ["Notice Identifier", "Organisation Name", "Published Date", "Title",
            "OJEU Procedure Type", "Awarded Date", "Awarded Value", SUPPLIER_COL,
            "Contract start date", "Contract end date"]
    miss = [x for x in need if x not in raw.columns]
    if miss:
        stop(f"contracts.csv lacks columns {miss}")
    c["rows_in_file"] = len(raw)
    if len(raw) >= EXPORT_CAP_ROWS:
        c["warnings"].append(f"file has {len(raw)} rows, at or above the Contracts Finder "
                             f"export cap of {EXPORT_CAP_ROWS}: it may be truncated")
    org = raw["Organisation Name"].str.strip()
    keep = org.str.lower().isin(COUNCIL_NAMES)
    c["organisation_names_kept"] = {k: int(v) for k, v in org[keep].value_counts().items()}
    c["organisation_names_dropped"] = {k: int(v) for k, v in org[~keep].value_counts().items()}
    c["rows_dropped_other_buyers"] = int((~keep).sum())
    df = raw[keep].copy()
    c["duplicate_notice_ids_removed"] = int(df["Notice Identifier"].duplicated().sum())
    df = df.drop_duplicates("Notice Identifier")
    c["rows_for_council"] = len(df)
    if len(df) < MIN_COUNCIL_NOTICES:
        c["contracts_present"] = False
        c["reason"] = (f"only {len(df)} notices for the council after filtering "
                       f"(minimum {MIN_COUNCIL_NOTICES}); treated as absent")
        return None
    for col in ("Contract start date", "Contract end date", "Awarded Date"):
        blank = df[col].str.strip() == ""
        try:
            parsed = pd.to_datetime(df[col].str.strip().where(~blank), format="%d/%m/%Y")
        except Exception as e:
            stop(f"contracts.csv: '{col}' failed to parse as %d/%m/%Y: {e}")
        df[col + "_p"] = parsed.dt.date
    try:
        pub = df["Published Date"].map(parse_iso)
    except Exception as e:
        stop(f"contracts.csv: 'Published Date' is not ISO: {e}")
    df["published_date"] = pub.map(lambda x: x.date().isoformat())
    df["published_year"] = pub.map(lambda x: x.year)
    try:
        df["awarded_value"] = df["Awarded Value"].str.strip().astype(float)
    except Exception as e:
        stop(f"contracts.csv: 'Awarded Value' not numeric: {e}")
    start, end = df["Contract start date_p"], df["Contract end date_p"]
    ended = end.notna() & (end < window_start)
    not_started = ~ended & start.notna() & (start > window_end)
    df["status_in_window"] = "active"
    df.loc[ended, "status_in_window"] = "ended_before_window"
    df.loc[not_started, "status_in_window"] = "not_yet_started"

    rows = []
    for _, r in df.iterrows():
        s = r[SUPPLIER_COL].strip()
        if not (s.startswith("[") and s.endswith("]")):
            stop(f"contracts.csv: supplier field not bracketed for notice {r['Notice Identifier']}")
        blocks = s[1:-1].split("][")
        for b in blocks:
            parts = b.split("|")
            if len(parts) != 6:
                stop(f"contracts.csv: notice {r['Notice Identifier']} has a supplier block "
                     f"with {len(parts)} fields, expected 6")
            name = parts[0].strip()
            ch = parts[3].strip() if parts[2].strip() == "COMPANIES_HOUSE" else ""
            rows.append({
                "notice_id": r["Notice Identifier"], "title": r["Title"],
                "organisation": r["Organisation Name"].strip(),
                "procedure_type": r["OJEU Procedure Type"].strip(),
                "published_date": r["published_date"], "published_year": r["published_year"],
                "awarded_date": r["Awarded Date_p"], "contract_start": r["Contract start date_p"],
                "contract_end": r["Contract end date_p"], "awarded_value": r["awarded_value"],
                "suppliers_on_notice": len(blocks),
                "supplier_name": name, "supplier_norm": normalise_supplier(name),
                "companies_house_no": ch,
                "status_in_window": r["status_in_window"],
                "active_in_window": r["status_in_window"] == "active",
                "ended_before_window": r["status_in_window"] == "ended_before_window",
                "source": "contracts_finder"})
    nc = pd.DataFrame(rows)
    c["blank_supplier_names_dropped"] = int((nc["supplier_norm"] == "").sum())
    nc = nc[nc["supplier_norm"] != ""]
    per_year = df["published_year"].value_counts().sort_index()
    st = df["status_in_window"].value_counts()
    c.update({
        "notice_supplier_pairs": len(nc),
        "distinct_suppliers": int(nc["supplier_norm"].nunique()),
        "distinct_suppliers_active": int(nc.loc[nc["active_in_window"], "supplier_norm"].nunique()),
        "pairs_with_companies_house_no": int((nc["companies_house_no"] != "").sum()),
        "active_in_window": int(st.get("active", 0)),
        "ended_before_window": int(st.get("ended_before_window", 0)),
        "not_yet_started": int(st.get("not_yet_started", 0)),
        "blank_end_dates": int(end.isna().sum()),
        "zero_value_awards": int((df["awarded_value"] == 0).sum()),
        "multi_supplier_notices": int((df[SUPPLIER_COL].str.count(r"\]\[") > 0).sum()),
        "rows_per_year": {str(k): int(v) for k, v in per_year.items()},
        "published_range": [df["published_date"].min(), df["published_date"].max()],
        "procedure_types": {k: int(v) for k, v in
                            df["OJEU Procedure Type"].str.strip().value_counts().items()},
        "spend_window": [window_start.isoformat(), window_end.isoformat()],
        "active_definition": "contract end on or after the spend window start (blank = active) "
                             "and contract start on or before the window end",
    })
    med = float(per_year.median())
    inner = per_year.iloc[1:-1] if len(per_year) > 2 else per_year.iloc[0:0]
    thin = [str(y) for y, n in inner.items() if n < 0.5 * med]
    if thin:
        c["warnings"].append(
            f"publication years {thin} (between the first and last year) hold fewer than half "
            f"the median yearly notice count; check the export for truncation")
    if per_year.iloc[0] < 0.5 * med or per_year.iloc[-1] < 0.5 * med:
        c["notes"] = ["the first and/or last publication year is thin; these may be part-years"]
    nc.to_csv(FULL / "notices-clean.csv", index=False)
    return nc


def main():
    load_rules()  # stop early if rules.json is missing
    FULL.mkdir(parents=True, exist_ok=True)
    for name in ("spend-clean.csv", "spend-excluded.csv", "notices-clean.csv", "cleaning-log.json"):
        p = FULL / name
        if p.exists():
            p.unlink()
    log = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "script": "scripts/clean.py", "files": []}
    df = load_spend(log)
    log["rows_raw"] = len(df)
    log["gbp_raw"] = gbp(int(df["amount_pence"].sum()))
    log["date_min"] = min(df["pay_date"]).isoformat()
    log["date_max"] = max(df["pay_date"]).isoformat()
    months = sorted({(d.year, d.month) for d in df["pay_date"]})
    log["months_covered"] = len(months)
    log["months"] = [f"{y}-{m:02d}" for y, m in months]
    log["distinct_timestamps"] = int(df["Date"].nunique())
    log["distinct_pay_dates"] = int(df["pay_date"].nunique())
    ym = df["Date"].dt.strftime("%Y-%m")
    modal = ym.groupby(df["source_file"]).agg(lambda s: s.value_counts().index[0])
    off = df[ym != df["source_file"].map(modal)]
    log["rows_dated_outside_file_month"] = {"rows": len(off), "row_ids": off["row_id"].head(20).tolist()}
    log["min_amount"] = gbp(int(df["amount_pence"].min()))

    clean, excl = exclude_and_tag(df, log)
    log["rows_after_exclusions"] = len(clean)
    log["gbp_after_exclusions"] = gbp(int(clean["amount_pence"].sum()))
    log["distinct_suppliers_raw_names"] = int(clean["Supplier name"].nunique())
    log["distinct_suppliers_normalised"] = int(clean["supplier_norm"].nunique())

    for d_ in (clean, excl):
        d_["Date"] = d_["Date"].dt.strftime("%Y-%m-%dT%H:%M:%S.%f").str[:-3]
    base = ["row_id", "source_file", "sheet_row"] + EXPECTED_COLS + ["pay_date", "amount_pence"]
    clean[base + ["supplier_norm", "tag"]].to_csv(FULL / "spend-clean.csv", index=False)
    excl[base + ["exclusion"]].to_csv(FULL / "spend-excluded.csv", index=False)

    load_notices(min(df["pay_date"]), max(df["pay_date"]), log)
    (FULL / "cleaning-log.json").write_text(json.dumps(log, indent=1, default=str))

    print("clean.py done")
    print(" rows raw", log["rows_raw"], "after exclusions", log["rows_after_exclusions"],
          "months", log["months"])
    print(" excluded", {k: (v["rows"], v["gbp"]) for k, v in log["excluded"].items()})
    print(" tags", {k: (v["rows"], v["gbp"]) for k, v in log["tags"].items()})
    c = log["contracts"]
    print(" contracts", {k: c.get(k) for k in ("contracts_present", "rows_in_file", "rows_for_council",
                                                 "notice_supplier_pairs", "distinct_suppliers",
                                                 "active_in_window", "ended_before_window",
                                                 "not_yet_started")})
    print(" warnings", c["warnings"])


if __name__ == "__main__":
    main()
