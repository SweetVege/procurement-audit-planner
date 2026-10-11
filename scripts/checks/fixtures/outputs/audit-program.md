# Audit program

> This pack plans work on **risk indicators to investigate**, drawn from public data. Nothing in it is a finding of wrongdoing by the council, a service, an officer or a supplier.

Built 2026-10-10 18:39 from the risk register **Revision 1** and the auditor's decisions in `auditor-comments.md`.

## R-01 Purchases may be divided below a value band

Rating: Likely (3) × Medium (3) = 9 High. Auditor decision: approve — “Start with the largest windows, above £25,000.”.

- **C-01.1** Related purchases are aggregated before the value band is chosen. (CPR-02)
- **C-01.2** Three quotes are sought at or above the publication value. (CPR-05)

### T-01.1

**Controls tested:** C-01.1, C-01.2

**Test step.** For each sampled window, obtain the orders and quotation record and confirm how the value band was decided [CPR-02, cl. 2.2] [analytics `tests.split_purchases.per_threshold['25000.00'].headline_general_procurement.windows`].

**Sample.** From `analytics-full/split-purchases.csv`; filter: `tag` == `general_procurement`; order: `total_gbp` desc; size: by score (9): up to 15. 2 of 2 flagged items, giving 5 transactions worth £64,500.00 (the payments listed against each item).

**Transactions to pull.** `samples/T-01.1.csv`. First rows: `P02.xlsx:3`, `P02.xlsx:4`, `P02.xlsx:5`, `P02.xlsx:6`, `P02.xlsx:7`.

**Requests needed:** P-01, P-02

## R-02 Repeated payments of the same amount

Rating: Likely (3) × Minor (2) = 6 Moderate. Auditor decision: approve.

- **C-02.1** A register of contracts is kept. (CPR-04)

### T-02.1

**Controls tested:** C-02.1

**Test step.** For each sampled group, obtain the invoices and confirm each payment was separately due [CPR-04, cl. 3.1] [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.groups`].

**Sample.** From `analytics-full/duplicate-groups.csv`; filter: `tag` == `general_procurement`; order: `amount` desc, `group_id` asc; size: all items (census). 2 of 2 flagged items, giving 5 transactions worth £7,081.50 (the payments listed against each item).

**Transactions to pull.** `samples/T-02.1.csv`. First rows: `P02.xlsx:10`, `P02.xlsx:11`, `P02.xlsx:12`, `P02.xlsx:13`, `P02.xlsx:14`.

**Requests needed:** P-02

## PBC list (requests to the council)

| Ref | Request | Needed for |
| --- | --- | --- |
| P-01 | Quotation records and purchase orders for the suppliers and dates in the sample. | T-01.1 |
| P-02 | Invoices for every sampled transaction. | T-01.1, T-02.1 |
