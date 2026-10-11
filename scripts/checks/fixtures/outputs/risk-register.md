# Procurement risk register — Revision 1

> These are **risk indicators to investigate**, drawn from public data. None of them is a finding of wrongdoing by the council, a service, an officer or a supplier.

## Header

- **Status:** Revision 1, built 2026-10-10 18:39. Every risk has an auditor decision.
- **Inputs:** `/Users/gaoyuming/Desktop/procurement-audit-planner/scripts/checks/fixtures/outputs/rules.json`, `/Users/gaoyuming/Desktop/procurement-audit-planner/scripts/checks/fixtures/outputs/analytics.json`, `/Users/gaoyuming/Desktop/procurement-audit-planner/scripts/checks/fixtures/outputs/history.json`.
- **Scoring method:** the council's own, as recorded in history.json: 5×5 matrix, score and label read from the matrix cell, band from the band table.
- **Risks:** 2 rated, 0 excluded by the builder, 0 warning(s).
- **Every figure** below was filled from analytics.json by `build_register.py`; none was typed.

### Scoring-method conflicts

The papers disagree with themselves in the places below. One reading is used, the other is marked, and neither has been corrected.

- IMP-06 records the impact level 'Medium' at 2, which disagrees with the matrix axis (Negligible = 1, Minor = 2, Medium = 3, Major = 4, Critical = 5). **Used:** the matrix axis. **Marked, not used:** IMP-06.
- The matrix prints **High** in the cells scoring 8, 9, 10, 12; the band table prints **Medium - High** for that range (BND-02). **Used:** the matrix label, shown as printed. **Marked, not used as the label:** the band-table name, shown beside it.
- DIS-01: **Used:** Medium = 3. **Marked, not used:** 'Medium (2)'. **Effect:** None.
- DIS-02: **Used:** The band table. **Marked, not used:** 'Score 9 or above'. **Effect:** None on scores.

### What changed in this revision

- No risk was changed.
- Approved unchanged: R-01, R-02.

## Summary

| Risk | Title | Likelihood | Impact | Score | Matrix label | Band | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | Purchases may be divided below a value band | Likely (3) | Medium (3) | 9 | High | Medium - High (Amber) | Approved |
| R-02 | Repeated payments of the same amount | Likely (3) | Minor (2) | 6 | Moderate | Moderate | Approved |

## R-01 Purchases may be divided below a value band

**Risk.** The Rules prohibit artificial splitting [CPR-02, cl. 2.2].

**Likelihood: 3 Likely** (rubric L3). Present in one test: 41 windows [analytics `tests.split_purchases.per_threshold['25000.00'].headline_general_procurement.windows`].

**Impact: 3 Medium** (Compliance). Reasonable possibility of challenge [IMP-03: Medium (3)].

**Rating: 9** — matrix label **High**, band **Medium - High (Amber)**.

**Evidence.**

- Anti-splitting rule [CPR-02, cl. 2.2].

**Proposed focus.** Test the flagged windows against quotation records.

## R-02 Repeated payments of the same amount

**Risk.** The same amount paid more than once to one supplier within days is an indicator to check [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.groups`].

**Likelihood: 3 Likely** (rubric L3). Present in one test: 35 groups [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.groups`].

**Impact: 2 Minor** (Reputation). A complaint could be upheld [IMP-04: Minor (2)].

**Rating: 6** — matrix label **Moderate**, band **Moderate**.

**Evidence.**

- Groups: 35 [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.groups`].

**Proposed focus.** Confirm each repeated payment was due.

## Rules cited

The start of each cited rule's verbatim quote, copied from rules.json by the builder.

| Rule | Clause | Page | Quote from the Contract Rules (excerpt) |
| --- | --- | --- | --- |
| CPR-02 | 2.2 | 1 | There shall be no artificial splitting of a contract to avoid these Rules. |

## Auditor decisions

| Risk | Rating | Decision | Auditor comment |
| --- | --- | --- | --- |
| R-01 | Likely (3) × Medium (3) = 9 High | approve | Start with the largest windows, above £25,000. |
| R-02 | Likely (3) × Minor (2) = 6 Moderate | approve |  |
