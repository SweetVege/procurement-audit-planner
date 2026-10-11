# Audit program

> This pack plans work on **risk indicators to investigate**, drawn from public data. Nothing in it is a finding of wrongdoing by the council, a service, an officer or a supplier.

Built 2026-10-10 18:51 from the risk register **Revision 2** and the auditor's decisions in `auditor-comments.md`.

## R-01 Purchases divided or repeated so that the requirements of a higher value band do not apply

Rating: Likely (3) × Medium (3) = 9 High. Auditor decision: approve — “Evidence and caveats are sound; start with the £500,000-band windows.”.

- **C-01.1** Before a value band is chosen, the value of the requirement is estimated over the full potential duration of the contract, including planned extensions and options [CPR-14, cl. 6.15], and one requirement is not divided into several contracts or orders [CPR-15, cl. 6.16]. The Rules state the basis for Value Added Tax in two ways (included in the estimate in one clause, excluded in the Appendix B heading), so the basis the council applies is to be confirmed. (CPR-14, CPR-15)
- **C-01.2** Where repeat purchases or purchases of a similar type are envisaged, each below the relevant Threshold, advice on the application of the Procurement Legislation is sought before purchasing [CPR-16, cl. 6.17]. The Threshold figure is not printed in the Rules and is to be confirmed with the council. (CPR-16)
- **C-01.3** Where the whole value of a requirement is £25,000 or more, invitations to quote are sent through the Procurement Portal to at least three appropriate sources and a contract notice is published [CPR-57, cl. App B row B1] [CPR-58, cl. App B row B1] [CPR-59, cl. App B row B2] [CPR-60, cl. App B row B2]. (CPR-57, CPR-58, CPR-59, CPR-60)
- **C-01.4** Where the whole value of a works, concession or light touch requirement is above £500,000 and less than the Threshold, a full competitive tender is run with at least five written tenders sought through the Procurement Portal, and an advert is placed [CPR-61, cl. App B row C] [CPR-62, cl. App B row C]. The Threshold figure is to be confirmed with the council; the Rules leave a value of exactly £500,000 in no band, and this band is empty if the Threshold for the category is lower than that figure. (CPR-61, CPR-62)
- **C-01.5** For a requirement with a total value above £1,000 and less than £25,000, at least one quote is sought from an appropriate source [CPR-56, cl. App B row A]. The Rules state no award procedure at or below £1,000, so what the council expects for such a purchase is to be confirmed. (CPR-56)

### T-01.1

**Controls tested:** C-01.1, C-01.3, C-01.4

**Test step.** Taken first, as the auditor directed. For each general-procurement window at the £500,000 band [analytics `tests.split_purchases.per_threshold['500000.00'].headline_general_procurement.windows`], look the supplier up in the contract register, then obtain the orders, invoices and contract behind every payment in the window. Confirm whether the payments are instalments or call-offs under one contract let for its whole value, or belong to separate orders; where they belong to separate orders, confirm whether the orders meet one requirement and how its value was estimated [CPR-14, cl. 6.15] [CPR-15, cl. 6.16]. Obtain the tender or quotation record and the notice or advert for the contract or contracts, and compare them with the requirement for the whole value [CPR-59, cl. App B row B2] [CPR-61, cl. App B row C] [CPR-62, cl. App B row C]. Record, for each window, the contract reference, its let value, the procedure used and whether the payments fall under it.

**Sample.** From `analytics-full/split-purchases.csv`; filter: `threshold` == `500000.0`; `tag` == `general_procurement`; order: `total_gbp` desc, `supplier_norm` asc; size: all items (census). 2 of 2 flagged items, giving 58 transactions worth £3,509,528.75 (the payments listed against each item).

**Transactions to pull.** `samples/T-01.1.csv`. First rows: `Over500_2026_P02_-_published.xlsx:727`, `Over500_2026_P02_-_published.xlsx:696`, `Over500_2026_P02_-_published.xlsx:700`, `Over500_2026_P02_-_published.xlsx:701`, `Over500_2026_P02_-_published.xlsx:710`, `Over500_2026_P02_-_published.xlsx:714`, `Over500_2026_P02_-_published.xlsx:720`, `Over500_2026_P02_-_published.xlsx:724` ….

**Requests needed:** P-01, P-03, P-04

### T-01.2

**Controls tested:** C-01.1, C-01.3

**Test step.** For every general-procurement window at the £25,000 band [analytics `tests.split_purchases.per_threshold['25000.00'].headline_general_procurement.windows`], look the supplier up in the contract register, then obtain the orders and invoices behind the payments in the window. Confirm whether the payments fall under one contract let for its whole value, or are separate orders; for separate orders, confirm whether they meet one requirement, bearing in mind that the published date is a payment-run date and that several payments inside 30 days can be instalments. Where one requirement was met by several orders, obtain the quotation record and the notice and compare them with the requirement for the combined value [CPR-57, cl. App B row B1] [CPR-58, cl. App B row B1] [CPR-59, cl. App B row B2] [CPR-60, cl. App B row B2]. Record the contract or order references and the procedure used for each window.

**Sample.** From `analytics-full/split-purchases.csv`; filter: `threshold` == `25000.0`; `tag` == `general_procurement`; order: `total_gbp` desc, `supplier_norm` asc; size: all items (census). 41 of 41 flagged items, giving 461 transactions worth £2,310,961.19 (the payments listed against each item).

**Transactions to pull.** `samples/T-01.2.csv`. First rows: `Over500_2026_P02_-_published.xlsx:695`, `Over500_2026_P02_-_published.xlsx:713`, `Over500_2026_P02_-_published.xlsx:723`, `Over500_2026_P02_-_published.xlsx:2174`, `Over500_2026_P02_-_published.xlsx:2177`, `Over500_2026_P02_-_published.xlsx:2178`, `Over500_2026_P02_-_published.xlsx:2181`, `Over500_2026_P02_-_published.xlsx:727` ….

**Requests needed:** P-01, P-03, P-04

### T-01.3

**Controls tested:** C-01.1, C-01.2

**Test step.** Walk through, with the procurement lead and the services that own the windows sampled in T-01.1 and T-01.2, how the value of a requirement is estimated and how repeat purchases from one supplier are added up before a value band is chosen [CPR-14, cl. 6.15] [CPR-16, cl. 6.17]. Obtain the written guidance, confirm whether Value Added Tax is included when a contract is placed in a band, and obtain the record of any advice sought on repeat purchases for those services in the period. Record the method described and compare it with what the files in T-01.1 and T-01.2 show.

**Sample.** No data sample: No separate draw: the walkthrough covers the services that own the windows already sampled in T-01.1 and T-01.2. Payments do not show how a value was estimated or whether advice was sought, so the evidence is the guidance and advice records requested from the council.

**Requests needed:** P-05

### T-01.4

**Controls tested:** C-01.1, C-01.5

**Test step.** For each sampled general-procurement payment in the band just under £1,000 [analytics `tests.threshold_clustering.per_threshold['1000.00'].band_by_tag.general_procurement.rows`], obtain the order and invoice and confirm the value of the whole requirement the payment belongs to, taking in any other orders for the same requirement [CPR-14, cl. 6.15]. Where the whole requirement was above £1,000, confirm whether a quote from an appropriate source is on file [CPR-56, cl. App B row A]. A price set just under a round figure is an ordinary explanation, and the register does not use this band as a signal for the rating; this is a document test of the one-quote requirement on the payments nearest the boundary. Record the value of the requirement and the quote seen.

**Sample.** From `analytics-full/threshold-clustering.csv`; filter: `threshold` == `1000.0`; `tag` == `general_procurement`; order: `Net amount` desc, `row_id` asc; size: by score (9): up to 15. 15 of 86 flagged items, giving 15 transactions worth £14,995.75 (the payments listed against each item).

**Transactions to pull.** `samples/T-01.4.csv`. First rows: `Over500_2026_P02_-_published.xlsx:34`, `Over500_2026_P02_-_published.xlsx:449`, `Over500_2026_P02_-_published.xlsx:538`, `Over500_2026_P02_-_published.xlsx:662`, `Over500_2026_P03_-_published.xlsx:280`, `Over500_2026_P03_-_published.xlsx:50`, `Over500_2026_P03_-_published.xlsx:651`, `Over500_2026_P04_-_published.xlsx:1006` ….

**Requests needed:** P-03, P-04

## R-02 Spend at or above the publication value with no matching contract notice

Rating: Likely (3) × Medium (3) = 9 High. Auditor decision: approve.

- **C-02.1** For a contract of £25,000 or more, invitations to quote are sent through the Procurement Portal to at least three appropriate sources [CPR-57, cl. App B row B1] [CPR-59, cl. App B row B2]. (CPR-57, CPR-59)
- **C-02.2** For a contract of £25,000 or more, a contract notice is published [CPR-58, cl. App B row B1] [CPR-60, cl. App B row B2], approved and issued by the Service Lead for Procurement and Commissioning or their delegate [CPR-13, cl. 6.14]. (CPR-58, CPR-60, CPR-13)
- **C-02.3** Each contract in progress or awarded is entered in the council's register of contracts with its value, duration and supplier [CPR-08, cl. 5.2.1]. (CPR-08)

### T-02.1

**Controls tested:** C-02.2, C-02.3

**Test step.** Taken first: the near-name matches among the general-procurement suppliers with no exact notice match [analytics `tests.off_contract.headline_general_procurement.of_which_near_match_candidates`]. For each, use the candidate recorded in the near-matches list as a lookup and confirm from the contract register whether the supplier paid and the supplier on the candidate notice are the same body [CPR-08, cl. 5.2.1]. Where they are, record the notice and the register entry against the supplier and confirm whether the notice covers the period of the payments [CPR-58, cl. App B row B1] [CPR-60, cl. App B row B2]; where they are not, carry the supplier into T-02.3.

**Sample.** From `analytics-full/high-value-suppliers.csv`; filter: `dominant_tag` == `general_procurement`; `match_class` in `['near_ratio', 'near_contain']`; order: `annualised_estimate` desc, `supplier_norm` asc; size: all items (census). 6 of 6 flagged items, giving 18 transactions worth £239,360.31 (the payments listed against each item).

**Transactions to pull.** `samples/T-02.1.csv`. First rows: `Over500_2026_P03_-_published.xlsx:661`, `Over500_2026_P04_-_published.xlsx:1283`, `Over500_2026_P02_-_published.xlsx:670`, `Over500_2026_P04_-_published.xlsx:148`, `Over500_2026_P04_-_published.xlsx:399`, `Over500_2026_P02_-_published.xlsx:173`, `Over500_2026_P04_-_published.xlsx:247`, `Over500_2026_P04_-_published.xlsx:186` ….

**Requests needed:** P-01

### T-02.2

**Controls tested:** C-02.3

**Test step.** For each sampled general-procurement supplier with no exact notice match [analytics `tests.off_contract.headline_general_procurement.suppliers`], leaving aside the near-name matches taken in T-02.1 and taken largest first from those with an annualised estimate below £500,000 (those at or above that figure are all taken in T-02.4), look the supplier up in the council's contract register before anything else: no notice found is a prompt to check the register, because a contract may have been awarded before the period the export covers, advertised elsewhere, called off under another buyer's framework, or excluded [CPR-08, cl. 5.2.1]. Record for each supplier whether a register entry covers the payments, and its reference, value, dates and procedure; confirm whether the annualised estimate, which scales 3 months to a year, is a fair picture of the yearly spend.

**Sample.** From `analytics-full/high-value-suppliers.csv`; filter: `dominant_tag` == `general_procurement`; `match_class` == `none`; `annualised_estimate` < `500000.0`; order: `annualised_estimate` desc, `supplier_norm` asc; size: by score (9): up to 15. 15 of 167 flagged items, giving 36 transactions worth £1,143,039.44 (the payments listed against each item).

**Transactions to pull.** `samples/T-02.2.csv`. First rows: `Over500_2026_P03_-_published.xlsx:2143`, `Over500_2026_P02_-_published.xlsx:2201`, `Over500_2026_P03_-_published.xlsx:479`, `Over500_2026_P02_-_published.xlsx:655`, `Over500_2026_P02_-_published.xlsx:568`, `Over500_2026_P03_-_published.xlsx:730`, `Over500_2026_P04_-_published.xlsx:1282`, `Over500_2026_P02_-_published.xlsx:478` ….

**Requests needed:** P-01

### T-02.4

**Controls tested:** C-02.3

**Test step.** For every general-procurement supplier with no notice match whose annualised estimate is £500,000 or more [analytics `tests.off_contract.headline_general_procurement.suppliers`], look the supplier up in the council's contract register before anything else: no notice found is a prompt to check the register, because a contract of this size may have been awarded before the period the export covers, advertised elsewhere, called off under another buyer's framework, or excluded [CPR-08, cl. 5.2.1]. Record for each supplier whether a register entry covers the payments, and its reference, value, dates and procedure; confirm whether the annualised estimate, which scales 3 months to a year, is a fair picture of the yearly spend. Where a supplier is also drawn in T-06.2, the register lookup is done once and used for both tests.

**Sample.** From `analytics-full/high-value-suppliers.csv`; filter: `dominant_tag` == `general_procurement`; `match_class` == `none`; `annualised_estimate` >= `500000.0`; order: `annualised_estimate` desc, `supplier_norm` asc; size: all items (census). 13 of 13 flagged items, giving 35 transactions worth £13,855,626.42 (the payments listed against each item).

**Transactions to pull.** `samples/T-02.4.csv`. First rows: `Over500_2026_P04_-_published.xlsx:793`, `Over500_2026_P04_-_published.xlsx:603`, `Over500_2026_P03_-_published.xlsx:684`, `Over500_2026_P02_-_published.xlsx:2196`, `Over500_2026_P03_-_published.xlsx:2146`, `Over500_2026_P04_-_published.xlsx:3194`, `Over500_2026_P03_-_published.xlsx:2144`, `Over500_2026_P03_-_published.xlsx:2216` ….

**Requests needed:** P-01

### T-02.3

**Controls tested:** C-02.1, C-02.2

**Test step.** For each supplier in T-02.1, T-02.2 and T-02.4, obtain the quotation or tender record and the contract notice for the contract the register shows, and confirm whether at least three invitations were issued through the Procurement Portal and whether the notice was issued by the Service Lead or their delegate [CPR-57, cl. App B row B1] [CPR-59, cl. App B row B2] [CPR-58, cl. App B row B1] [CPR-60, cl. App B row B2] [CPR-13, cl. 6.14]. Where no register entry was found, or no invitation or notice is held, ask which route was relied on and obtain the record of it: the approved waiver or exception (tested under R-07), the Appendix C approval (tested under R-08), or the call-off under a purchasing scheme [CPR-67, cl. App C row C]. Record the route and the document seen for each supplier.

**Sample.** No data sample: No separate draw: this step is carried out on the suppliers already drawn for T-02.1, T-02.2 and T-02.4, and the published data holds no quotation, tender or approval record to select from.

**Requests needed:** P-03, P-04, P-06, P-07

## R-03 Spend continuing after the matching contract notice has ended

Rating: Likely (3) × Medium (3) = 9 High. Auditor decision: approve.

- **C-03.1** Where an existing contract provides for extension, the extension is approved by the S151 Officer [CPR-68, cl. App C row D]. The Rules name the approver for an extension but no report, so the form the approval takes is to be confirmed with the council. (CPR-68)
- **C-03.2** Where a contract has ended and is not extended under a clause that provides for it, further purchasing of £25,000 or more follows a new invitation to quote to at least three sources and a contract notice [CPR-57, cl. App B row B1] [CPR-58, cl. App B row B1] [CPR-59, cl. App B row B2] [CPR-60, cl. App B row B2]. (CPR-57, CPR-58, CPR-59, CPR-60)

### T-03.1

**Controls tested:** C-03.1

**Test step.** For every supplier whose matching notices all ended before 2026-05-01 [analytics `tests.expired_notice_spend.count`], look the supplier up in the contract register and obtain the contract in force when the sampled payments were made: a later award may exist with no notice on Contracts Finder. Where the earlier contract was extended, obtain the extension clause relied on and the S151 Officer's approval, and confirm whether the approval was given before the earlier end date [CPR-68, cl. App C row D]. Confirm from the order or invoice whether each sampled payment relates to the contract on the notice or to other work. Record the contract in force, its end date and the approval seen.

**Sample.** From `analytics-full/expired-notice-spend.csv`; filter: `dominant_tag` == `general_procurement`; order: `annualised_estimate` desc, `supplier_norm` asc; size: all items (census). 5 of 5 flagged items, giving 22 transactions worth £210,960.48 (every payment to the item's supplier in the period, largest 10 per item).

**Transactions to pull.** `samples/T-03.1.csv`. First rows: `Over500_2026_P03_-_published.xlsx:704`, `Over500_2026_P03_-_published.xlsx:58`, `Over500_2026_P03_-_published.xlsx:42`, `Over500_2026_P03_-_published.xlsx:279`, `Over500_2026_P03_-_published.xlsx:52`, `Over500_2026_P04_-_published.xlsx:374`, `Over500_2026_P04_-_published.xlsx:369`, `Over500_2026_P04_-_published.xlsx:59` ….

**Requests needed:** P-01, P-03, P-08

### T-03.2

**Controls tested:** C-03.2

**Test step.** For each supplier in T-03.1 where neither a later contract nor an approved extension is shown, obtain the quotation record and the notice for the purchasing that followed the end date and compare them with the requirement for its value [CPR-57, cl. App B row B1] [CPR-58, cl. App B row B1] [CPR-59, cl. App B row B2] [CPR-60, cl. App B row B2]; where none is held, ask which route was relied on and obtain the record of it. Record the route and the document seen.

**Sample.** No data sample: No separate draw: this step is carried out on the suppliers in T-03.1 for which no contract in force is shown, a set that is known only once the contract register has been checked.

**Requests needed:** P-04, P-06

## R-05 Repeated payments of the same amount to the same supplier

Rating: Likely (3) × Medium (3) = 9 High. Auditor decision: approve.

- **C-05.1** Written evidence, which may be electronic, is held for every purchase [CPR-35, cl. 10.1], so that each payment can be traced to its own order and invoice. The Contract Rules set no duplicate-payment check of their own; this is the rule a repeated payment is compared with. (CPR-35)

### T-05.1

**Controls tested:** C-05.1

**Test step.** For every general-procurement group of same-supplier, same-amount payments made at different times within 7 days [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.groups`], obtain the invoice and order for each payment in the group [CPR-35, cl. 10.1]. Confirm first whether each payment was separately due: an identical amount can be two periodic charges, two orders at a list price, or one invoice per site. Compare invoice numbers, invoice dates, order numbers and the goods or service described, and record for each group whether each payment has its own invoice and order.

**Sample.** From `analytics-full/duplicate-groups.csv`; filter: `tier` == `different_time`; `tag` == `general_procurement`; order: `gbp_beyond_first` desc, `group_id` asc; size: all items (census). 35 of 35 flagged items, giving 86 transactions worth £566,187.75 (the payments listed against each item).

**Transactions to pull.** `samples/T-05.1.csv`. First rows: `Over500_2026_P04_-_published.xlsx:3308`, `Over500_2026_P04_-_published.xlsx:618`, `Over500_2026_P04_-_published.xlsx:3210`, `Over500_2026_P04_-_published.xlsx:3302`, `Over500_2026_P02_-_published.xlsx:2160`, `Over500_2026_P02_-_published.xlsx:2161`, `Over500_2026_P04_-_published.xlsx:3184`, `Over500_2026_P04_-_published.xlsx:3185` ….

**Requests needed:** P-03

### T-05.2

**Controls tested:** C-05.1

**Test step.** For each sampled general-procurement group of same-supplier, same-amount payments sharing one timestamp [analytics `tests.duplicates.per_tier.same_timestamp.headline_general_procurement.groups`], obtain the invoices and the payment-run record [CPR-35, cl. 10.1]. Confirm first whether the lines are several lines of one invoice or one run, each separately due, and record for each group whether each line has its own invoice or invoice line.

**Sample.** From `analytics-full/duplicate-groups.csv`; filter: `tier` == `same_timestamp`; `tag` == `general_procurement`; order: `gbp_beyond_first` desc, `group_id` asc; size: by score (9): up to 15. 15 of 28 flagged items, giving 35 transactions worth £70,423.86 (the payments listed against each item).

**Transactions to pull.** `samples/T-05.2.csv`. First rows: `Over500_2026_P04_-_published.xlsx:601`, `Over500_2026_P04_-_published.xlsx:740`, `Over500_2026_P03_-_published.xlsx:2134`, `Over500_2026_P03_-_published.xlsx:2141`, `Over500_2026_P04_-_published.xlsx:162`, `Over500_2026_P04_-_published.xlsx:171`, `Over500_2026_P03_-_published.xlsx:165`, `Over500_2026_P03_-_published.xlsx:334` ….

**Requests needed:** P-03

### T-05.3

**Controls tested:** C-05.1

**Test step.** Ask the accounts payable lead what check the payment system applies to a second invoice with the same supplier, amount or invoice number, and obtain evidence of whether it was in operation throughout the period. The Contract Rules set no such check [analytics `tests.duplicates.rule_note`], so record the answer as context for T-05.1 and T-05.2 and compare it with what those tests show about the evidence held for each payment [CPR-35, cl. 10.1].

**Sample.** No data sample: No selection is drawn: this is an enquiry about how the payment system works, which published payments cannot show. It is read alongside the groups sampled in T-05.1 and T-05.2.

**Requests needed:** P-10

## R-06 Contracts above the procurement-legislation Threshold handled under a lower value band

Rating: Unlikely (2) × Major (4) = 8 High. Auditor decision: approve.

- **C-06.1** For a contract with an estimated value above the relevant Threshold, an electronic Invitation to Tender is issued and tenders are received through the Procurement Portal [CPR-17, cl. 6.19], under the procedures of the Procurement Legislation: a full competitive tender with at least five written tenders sought where appropriate [CPR-63, cl. App B row D]. The Threshold figures are not printed in the Rules and are to be confirmed with the council; the Rules leave a value exactly equal to the Threshold in no band. (CPR-17, CPR-63)
- **C-06.2** For a contract above the Threshold, an advert is placed on the Central Digital Platform [CPR-64, cl. App B row D] before the opportunity is advertised in any other medium [CPR-12, cl. 6.10], and the opportunity is advertised electronically on the Procurement Portal [CPR-11, cl. 6.8]. The Threshold figures are to be confirmed with the council. (CPR-64, CPR-12, CPR-11)
- **C-06.3** Where repeat purchases or purchases of a similar type, each below the relevant Threshold, are envisaged, advice on the application of the Procurement Legislation is sought [CPR-16, cl. 6.17]. The Threshold figures are to be confirmed with the council. (CPR-16)

### T-06.1

**Controls tested:** C-06.1, C-06.2, C-06.3

**Test step.** Taken first under this risk. Obtain the Threshold figures in force for each contract category on each date in the period, as published on the Procurement intranet page, and confirm whether they are stated inclusive or exclusive of Value Added Tax [CPR-63, cl. App B row D] [CPR-16, cl. 6.17]. The figures are null in the rules file [analytics `threshold_source.null_parameters`]. Confirm how many categories the council applies, since the Rules count them in two ways, and how a contract valued exactly at a Threshold is treated. Record the figures, their source and their effective dates; the figures go to the auditor, who decides whether the tests skipped for want of them are re-run.

**Sample.** No data sample: No selection is drawn: the step obtains the Threshold figures themselves, which are not printed in the Rules and so are not in the data. They are requested from the council.

**Requests needed:** P-02, P-14

### T-06.2

**Controls tested:** C-06.1, C-06.2

**Test step.** For each sampled general-procurement supplier, taken largest first from the suppliers at or above the publication value [analytics `tests.high_value_suppliers.headline_general_procurement.suppliers`], look the supplier up in the contract register and record the value, dates and category of the contract or contracts the payments fall under. Compare each contract value with the Threshold figure obtained in T-06.1. For each contract above its Threshold, obtain the Invitation to Tender, the record of tenders received through the Procurement Portal and the advert, and confirm whether the tender procedure and advert the Rules require above the Threshold are on file [CPR-17, cl. 6.19] [CPR-63, cl. App B row D] [CPR-64, cl. App B row D] [CPR-12, cl. 6.10] [CPR-11, cl. 6.8]. The annualised estimate that orders this sample is not a contract value; it only directs where to look first.

**Sample.** From `analytics-full/high-value-suppliers.csv`; filter: `dominant_tag` == `general_procurement`; order: `annualised_estimate` desc, `supplier_norm` asc; size: by score (8): up to 15. 15 of 223 flagged items, giving 41 transactions worth £14,522,207.85 (the payments listed against each item).

**Transactions to pull.** `samples/T-06.2.csv`. First rows: `Over500_2026_P04_-_published.xlsx:793`, `Over500_2026_P04_-_published.xlsx:603`, `Over500_2026_P03_-_published.xlsx:684`, `Over500_2026_P02_-_published.xlsx:2196`, `Over500_2026_P03_-_published.xlsx:2146`, `Over500_2026_P04_-_published.xlsx:3194`, `Over500_2026_P03_-_published.xlsx:2144`, `Over500_2026_P03_-_published.xlsx:2216` ….

**Requests needed:** P-01, P-02, P-04

### T-06.3

**Controls tested:** C-06.3

**Test step.** For the suppliers in T-06.2 whose payments fall under more than one contract or order, each below its Threshold, add up the contracts and orders of a similar type from the contract register and compare the total with the Threshold figure obtained in T-06.1. Where the total is above it, obtain the record of the advice sought on the application of the Procurement Legislation [CPR-16, cl. 6.17], and record whether advice is on file and what it said.

**Sample.** No data sample: No separate draw: this step is carried out on the suppliers drawn for T-06.2, and which of them have several contracts below a Threshold is known only once the register and the Threshold figures have been obtained.

**Requests needed:** P-01, P-02, P-05

## R-04 Spend running ahead of the awarded contract value

Rating: Likely (3) × Minor (2) = 6 Moderate. Auditor decision: approve.

- **C-04.1** A variation of scope to an existing contract with a value below the Threshold has the prior written approval of the Monitoring Officer and the S151 Officer [CPR-69, cl. App C row E]. The Threshold figure is to be confirmed with the council; the Rules leave a value exactly equal to the Threshold in neither band. (CPR-69)
- **C-04.2** A variation of scope to an existing contract with a value greater than the Threshold is approved by the relevant board, following a report to it with a recommendation from the Monitoring Officer and the S151 Officer [CPR-70, cl. App C row E]. The Threshold figure is to be confirmed with the council; the Rules call the report an extension report, so the report the council uses for a variation is to be confirmed. (CPR-70)

### T-04.1

**Controls tested:** C-04.1, C-04.2

**Test step.** For every supplier whose annualised estimate is at least 1.25 times the yearly rate of its one active award [analytics `tests.spend_vs_award.count`], confirm first what the published award value represents: an estimate, a maximum, an annual figure or a whole-life figure. Then obtain from the contract register the contract value and term, and from the finance system the spend to date under that contract, and confirm from the order or invoice whether each sampled payment relates to that contract or to other work. Record, for each supplier, the contract value, spend to date and whether spend to date is above the contract value [CPR-69, cl. App C row E] [CPR-70, cl. App C row E].

**Sample.** From `analytics-full/spend-vs-award.csv`; filter: `flag` == `True`; `dominant_tag` == `general_procurement`; order: `ratio` desc, `supplier_norm` asc; size: all items (census). 8 of 8 flagged items, giving 31 transactions worth £736,650.97 (every payment to the item's supplier in the period, largest 10 per item).

**Transactions to pull.** `samples/T-04.1.csv`. First rows: `Over500_2026_P04_-_published.xlsx:905`, `Over500_2026_P04_-_published.xlsx:492`, `Over500_2026_P04_-_published.xlsx:487`, `Over500_2026_P04_-_published.xlsx:494`, `Over500_2026_P04_-_published.xlsx:488`, `Over500_2026_P04_-_published.xlsx:906`, `Over500_2026_P04_-_published.xlsx:493`, `Over500_2026_P04_-_published.xlsx:489` ….

**Requests needed:** P-01, P-03, P-09

### T-04.2

**Controls tested:** C-04.1, C-04.2

**Test step.** For each supplier in T-04.1 where spend to date is above the contract value on the register, obtain the variation and its approval. Compare the contract value with the Threshold figure obtained in T-06.1 and confirm whether the approval is the one set for that value: the prior written approval of the Monitoring Officer and S151 Officer [CPR-69, cl. App C row E], or the relevant board's approval following a report with their recommendation [CPR-70, cl. App C row E]. Confirm whether the approval is dated before the spend passed the contract value, and record the approval seen.

**Sample.** No data sample: No separate draw: this step is carried out on the suppliers in T-04.1 whose spend to date is above the register value, a set that is known only once the register and the finance system have been checked.

**Requests needed:** P-02, P-08

## R-07 Competition waived or excepted without the required grounds, approval or record

Rating: Unlikely (2) × Medium (3) = 6 Moderate. Auditor decision: approve.

- **C-07.1** An exception or waiver is relied on only on a ground the Rules allow: urgency where delay would be likely to lead to financial loss, personal injury or damage to property, or the discretion of the relevant Executive Director or the Chief Executive with reasons recorded in writing [CPR-23, cl. 7.2]; and it is sought in advance and only in exceptional circumstances [CPR-24, cl. 7.3]. The Rules state this route only for contracts above the lower value boundary and none for the single-quote band [CPR-56, cl. App B row A], so the council's practice below that boundary is to be confirmed. (CPR-23, CPR-24)
- **C-07.2** The exception is approved at the level set for the contract's value: by the S151 Officer up to the Threshold [CPR-25, cl. 7.4.1]; by the S151 Officer in consultation with the Monitoring Officer and the appropriate Executive Director, with the exception report approved by the relevant board, above the Threshold and up to £500,000 [CPR-26, cl. 7.4.2]; and by the Executive on the recommendation of the S151 Officer and the Monitoring Officer above £500,000 [CPR-27, cl. 7.4.3]. The Threshold figure is to be confirmed with the council, and words appear to be missing from the middle band's clause, so the reading the council applies is to be confirmed. (CPR-25, CPR-26, CPR-27)
- **C-07.3** Every exception or waiver is fully documented [CPR-28, cl. 7.5.1], is the subject of a written exception report submitted to the relevant board in advance with the reasons for it [CPR-29, cl. 7.5.2], and is approved by the S151 Officer, who records that the reasons were considered and that the circumstances are exceptional [CPR-30, cl. 7.5.3]. (CPR-28, CPR-29, CPR-30)

### T-07.1

**Controls tested:** C-07.1, C-07.2

**Test step.** From the register of exceptions and waivers for the period, select items across each value band, taking every item above £500,000 and the largest in each lower band. For each, obtain the request and the approval, and confirm the ground relied on [CPR-23, cl. 7.2], whether the approval is dated before the contract was entered into [CPR-24, cl. 7.3], and whether the approver is the one set for the contract's value, using the Threshold figure obtained in T-06.1 [CPR-25, cl. 7.4.1] [CPR-26, cl. 7.4.2] [CPR-27, cl. 7.4.3]. Record the ground, the value, the approver and the two dates.

**Sample.** No data sample: The selection is drawn in the field from the council's register of exceptions and waivers (P-06). A waiver leaves no trace in published payments or notices, so the data holds no list to draw from.

**Requests needed:** P-02, P-06

### T-07.2

**Controls tested:** C-07.3

**Test step.** For the same selection as T-07.1, obtain the exception report and the minute of the relevant board that received it, and the S151 Officer's record. Confirm whether the report gives reasons, whether it went to the board before the contract was entered into or, where urgency was the ground, afterwards [CPR-29, cl. 7.5.2] [CPR-26, cl. 7.4.2], and whether the S151 Officer's record states that the reasons were considered [CPR-28, cl. 7.5.1] [CPR-30, cl. 7.5.3]. Record the report date, the board date and the record seen.

**Sample.** No data sample: The selection is the one drawn in the field for T-07.1 from the council's register of exceptions and waivers (P-06); the published data holds no exception report to draw from.

**Requests needed:** P-06

### T-07.3

**Controls tested:** C-07.1

**Test step.** Compare the register of exceptions and waivers with the suppliers drawn for T-02.1, T-02.2 and T-02.4 [analytics `tests.off_contract.headline_general_procurement.suppliers`]. For each of those suppliers for which the council names a waiver or exception as the route relied on, confirm whether the register holds an entry that covers the payments and predates them [CPR-24, cl. 7.3], and add that entry to the selection for T-07.1 and T-07.2. Record the entry reference against the supplier.

**Sample.** No data sample: No separate draw: the comparison is made for the suppliers already drawn for T-02.1, T-02.2 and T-02.4 against the council's register of exceptions and waivers (P-06), which is not in the data.

**Requests needed:** P-06

## R-08 Appendix C exclusions from competition applied without the required approval or record

Rating: Unlikely (2) × Medium (3) = 6 Moderate. Auditor decision: approve.

- **C-08.1** Where competition is excluded because the proposed contract is excluded under the Procurement Legislation, the Monitoring Officer gives prior written approval and, where applicable, the relevant board gives prior approval [CPR-65, cl. App C row A]. (CPR-65)
- **C-08.2** Where a contract is governed by the Provider Selection Regime, the key decisions are recorded and the relevant process under that regime is followed [CPR-66, cl. App C row B]. (CPR-66)
- **C-08.3** Where a contract is awarded under a purchasing scheme with no further competition, the Monitoring Officer gives prior written approval and, where applicable, the relevant board gives prior approval [CPR-67, cl. App C row C], and advice is sought confirming that the council is entitled to use the scheme and that the purchase falls within its coverage [CPR-31, cl. 8.2]. Words appear to be missing from the Appendix C row on purchasing schemes, so the circumstances the council treats as covered are to be confirmed. (CPR-67, CPR-31)
- **C-08.4** For an individual social care placement or package excluded from competition, a record of the reasons for the choice of provider is kept on the individual's case notes [CPR-71, cl. App C row F]. (CPR-71)
- **C-08.5** Where an Appendix C exemption is applied to a contract with an annual or total value of more than the Threshold, the relevant board approves it [CPR-72, cl. App C closing]. The Threshold figure is to be confirmed with the council. (CPR-72)

### T-08.1

**Controls tested:** C-08.4

**Test step.** For each sampled placement-tagged supplier whose main service is adult social care, taken largest first from those with no matching notice [analytics `tests.off_contract.placement_reported_separately.suppliers`], confirm with the service that the sampled payments are fees for individual placements or packages of the kind Appendix C excludes from competition. For the individuals those payments relate to, confirm whether a record of the reasons for the choice of provider is held on the case notes, inspecting the record under the council's arrangements for access to case files [CPR-71, cl. App C row F]. Record whether a reason is on file and its date against the date the placement began. Recurring fees to one provider are expected for placements and are not themselves an indicator.

**Sample.** From `analytics-full/high-value-suppliers.csv`; filter: `dominant_tag` == `care_or_education_placement`; `match_class` != `exact`; `main_service` == `Adult Social Care`; order: `annualised_estimate` desc, `supplier_norm` asc; size: by score (6): up to 10. 10 of 205 flagged items, giving 30 transactions worth £933,595.35 (the payments listed against each item).

**Transactions to pull.** `samples/T-08.1.csv`. First rows: `Over500_2026_P04_-_published.xlsx:1850`, `Over500_2026_P04_-_published.xlsx:1043`, `Over500_2026_P04_-_published.xlsx:2908`, `Over500_2026_P04_-_published.xlsx:2320`, `Over500_2026_P03_-_published.xlsx:1628`, `Over500_2026_P04_-_published.xlsx:2239`, `Over500_2026_P02_-_published.xlsx:823`, `Over500_2026_P02_-_published.xlsx:1822` ….

**Requests needed:** P-11

### T-08.2

**Controls tested:** C-08.1, C-08.2, C-08.3

**Test step.** From the council's list of contracts awarded in the period without competition under Appendix C, select items under each of three routes: a legislative exclusion, the Provider Selection Regime, and a purchasing scheme with no further competition. For each, obtain the approval and confirm whether the Monitoring Officer's written approval is dated before the award [CPR-65, cl. App C row A] [CPR-67, cl. App C row C]; for a Provider Selection Regime award, obtain the record of key decisions and of the process followed [CPR-66, cl. App C row B]; for a purchasing scheme, obtain the advice that the council was entitled to use the scheme and that the purchase fell within it [CPR-31, cl. 8.2]. Record the route, the approver and the dates.

**Sample.** No data sample: The selection is drawn in the field from the council's list of contracts awarded under an Appendix C exclusion (P-07). Whether an approval was given cannot be seen in payments or notices, and the data does not show which route a contract was awarded under.

**Requests needed:** P-07

### T-08.3

**Controls tested:** C-08.5

**Test step.** For the items selected in T-08.2, and for the contracts behind the suppliers sampled in T-08.1 and T-08.4 that the service says are let as a contract and not as individual placements, compare the annual and total contract value with the Threshold figure obtained in T-06.1. Where the value is more than the Threshold, obtain the relevant board's approval and confirm whether it is on file and when it was given [CPR-72, cl. App C closing]. Record the value, the Threshold applied and the approval seen.

**Sample.** No data sample: No separate draw: this step is carried out on the items selected for T-08.2 from the council's list (P-07) and on the contracts behind the T-08.1 and T-08.4 samples; which of them are above a Threshold is known only once the figures and contract values are obtained.

**Requests needed:** P-02, P-07

### T-08.4

**Controls tested:** C-08.4

**Test step.** For each sampled placement-tagged supplier whose main service is any other than adult social care (children's and education services), taken largest first from those with no matching notice [analytics `tests.off_contract.placement_reported_separately.suppliers`], confirm with the service that the sampled payments are fees for individual placements or packages of the kind Appendix C excludes from competition. For the individuals those payments relate to, confirm whether a record of the reasons for the choice of provider is held on the case notes, inspecting the record under the council's arrangements for access to case files [CPR-71, cl. App C row F]. Record whether a reason is on file and its date against the date the placement began. Recurring fees to one provider are expected for placements and are not themselves an indicator.

**Sample.** From `analytics-full/high-value-suppliers.csv`; filter: `dominant_tag` == `care_or_education_placement`; `match_class` != `exact`; `main_service` != `Adult Social Care`; order: `annualised_estimate` desc, `supplier_norm` asc; size: by score (6): up to 10. 10 of 104 flagged items, giving 30 transactions worth £1,385,369.21 (the payments listed against each item).

**Transactions to pull.** `samples/T-08.4.csv`. First rows: `Over500_2026_P03_-_published.xlsx:3116`, `Over500_2026_P03_-_published.xlsx:3108`, `Over500_2026_P03_-_published.xlsx:2314`, `Over500_2026_P04_-_published.xlsx:3080`, `Over500_2026_P02_-_published.xlsx:2095`, `Over500_2026_P02_-_published.xlsx:2088`, `Over500_2026_P02_-_published.xlsx:2046`, `Over500_2026_P02_-_published.xlsx:2043` ….

**Requests needed:** P-11

## R-09 Contracts awarded without the approval their value requires

Rating: Likely (3) × Minor (2) = 6 Moderate. Auditor decision: override — “Raise likelihood to 3: two split-purchase windows totalling £3.5m sit at the £500,000 Key Decision band, and that exact value falls in no Appendix A band.”.

- **C-09.1** Every contract is in accordance with a decision of the Council or the Executive, or one made within the Scheme of Delegation [CPR-02, cl. 4.1], and is entered into only where it is in accordance with an existing provision in the approved Budget [CPR-03, cl. 4.2]. (CPR-02, CPR-03)
- **C-09.2** Where a Service Director does not have delegated authority, approval under Appendix A is obtained before the contract is awarded [CPR-05, cl. 4.4]: up to the relevant Threshold the award is made under the Service Director's delegated authority or by officers they nominate in writing [CPR-52, cl. App A row 1]; above it and below £500,000 a written report is approved by the relevant board and the award follows the recommendation of the S151 Officer and Monitoring Officer [CPR-53, cl. App A row 2]. The Threshold figure is to be confirmed with the council. (CPR-05, CPR-52, CPR-53)
- **C-09.3** An award with a value over £500,000 is treated as a Key Decision [CPR-04, cl. 4.3]: a written report is approved by the relevant board and the decision is made by the Service Director in consultation with the Portfolio Holder, in accordance with the Call-In and Forward Plan provisions [CPR-54, cl. App A row 3]. A value of exactly £500,000 falls in no band of Appendix A, and the cross-references to those provisions are left blank in the Rules, so the treatment the council applies is to be confirmed. (CPR-04, CPR-54)
- **C-09.4** A contract with a value of £2,500,000 or more has Executive approval, which may be given by delegated authority sought through quarterly reports to the Executive [CPR-55, cl. App A row 4]. The band is headed as that figure or more while the text beside it reads in excess of it, so the treatment of a contract at exactly that value is to be confirmed. (CPR-55)

### T-09.1

**Controls tested:** C-09.1, C-09.3, C-09.4

**Test step.** Planned to the auditor's reason for the override. For each general-procurement window at the £500,000 band [analytics `tests.split_purchases.per_threshold['500000.00'].headline_general_procurement.windows`], identify from the contract register the contract or contracts the payments fall under, using the records obtained in T-01.1, and confirm the value at which each was awarded. For each contract, obtain the decision record: the board report, the Key Decision entry and Forward Plan notice where the value is over £500,000 [CPR-04, cl. 4.3] [CPR-54, cl. App A row 3], the Executive's approval or delegation where it is £2,500,000 or more [CPR-55, cl. App A row 4], and the budget provision relied on [CPR-02, cl. 4.1] [CPR-03, cl. 4.2]. Confirm whether each approval is dated before the award, and record the award value, the band applied and the approvals seen.

**Sample.** From `analytics-full/split-purchases.csv`; filter: `threshold` == `500000.0`; `tag` == `general_procurement`; order: `total_gbp` desc, `supplier_norm` asc; size: all items (census). 2 of 2 flagged items, giving 58 transactions worth £3,509,528.75 (the payments listed against each item).

**Transactions to pull.** `samples/T-09.1.csv`. First rows: `Over500_2026_P02_-_published.xlsx:727`, `Over500_2026_P02_-_published.xlsx:696`, `Over500_2026_P02_-_published.xlsx:700`, `Over500_2026_P02_-_published.xlsx:701`, `Over500_2026_P02_-_published.xlsx:710`, `Over500_2026_P02_-_published.xlsx:714`, `Over500_2026_P02_-_published.xlsx:720`, `Over500_2026_P02_-_published.xlsx:724` ….

**Requests needed:** P-01, P-09

### T-09.2

**Controls tested:** C-09.1, C-09.2, C-09.3, C-09.4

**Test step.** From the council's list of contracts awarded in the period, select awards in each Appendix A band, taking every award of £2,500,000 or more and the awards nearest to £500,000 on either side, then the largest in each remaining band. For each, trace the approval set for its value: the Service Director's delegation or written nomination [CPR-52, cl. App A row 1], the board report and recommendation [CPR-53, cl. App A row 2], the Key Decision record [CPR-04, cl. 4.3] [CPR-54, cl. App A row 3], or the Executive's approval [CPR-55, cl. App A row 4], together with the decision and budget provision the award rests on [CPR-02, cl. 4.1] [CPR-03, cl. 4.2] [CPR-05, cl. 4.4]. Use the Threshold figure obtained in T-06.1 to place each award in its band, confirm whether each approval is dated before the award, and record the value, band, approver and dates.

**Sample.** No data sample: The selection is drawn in the field from the council's list of contracts awarded in the period (P-09). Payments and notices do not show who approved an award, and no test in the data bears on approvals.

**Requests needed:** P-01, P-02, P-09

### T-09.3

**Controls tested:** C-09.3, C-09.4

**Test step.** Ask the Monitoring Officer's team how an award valued at exactly £500,000, and one at exactly £2,500,000, is treated, given that the first value falls in no band of Appendix A [CPR-53, cl. App A row 2] [CPR-54, cl. App A row 3] and the second is described in two ways [CPR-55, cl. App A row 4]; and which constitutional provisions stand behind the blank Call-In and Forward Plan cross-references. Obtain the written position or guidance, and record the reading applied so that T-09.1 and T-09.2 compare each award with it.

**Sample.** No data sample: No selection is drawn: this is an enquiry to establish which reading of the Appendix A boundaries the council applies, which no payment or notice can show.

**Requests needed:** P-14

## R-11 Procurement records and published information incomplete

Rating: Unlikely (2) × Minor (2) = 4 Moderate. Auditor decision: approve.

- **C-11.1** Expenditure exceeding £500, including payments to suppliers and contractors, is published [CPR-06, cl. 5.1.1], and details of every invitation to tender for a goods or services contract above the value the Rules set are published [CPR-07, cl. 5.2]. (CPR-06, CPR-07)
- **C-11.2** A register of contracts in progress and awarded is published with key information such as value, duration and supplier [CPR-08, cl. 5.2.1], and the relevant Service Director formally notifies the Service Lead for Commissioning and Procurement of each award so that it is recorded on the register [CPR-38, cl. 10.4]. (CPR-08, CPR-38)
- **C-11.3** Service areas report contract information to the relevant board every month in the required format [CPR-09, cl. 5.3]. (CPR-09)
- **C-11.4** The progress of every procurement procedure is documented with enough information to justify the decisions taken, and the documentation is kept for three years from the award [CPR-34, cl. 9.3]; written evidence is held for every purchase [CPR-35, cl. 10.1]. (CPR-34, CPR-35)
- **C-11.5** For each contract awarded above the Threshold and subject to the Procurement Legislation, the relevant Service Director produces a written report [CPR-32, cl. 9.1], which is kept for three years [CPR-33, cl. 9.2]. The Threshold figure is to be confirmed with the council. (CPR-32, CPR-33)

### T-11.1

**Controls tested:** C-11.2

**Test step.** Obtain the published register of contracts as it stood at the end of the period and compare it, supplier by supplier, with the council's Contracts Finder notices [analytics `contracts.rows_for_council`] and with the general-procurement suppliers drawn for T-02.1, T-02.2, T-02.4 and T-06.2 [CPR-08, cl. 5.2.1]. For the contracts found in one source and not the other, obtain the Service Director's notification of the award to the Service Lead [CPR-38, cl. 10.4] and confirm when the award was notified and entered. Record the contracts present in each source and the notification dates.

**Sample.** No data sample: No draw from the data: this is a comparison of whole lists (the published register against the notices), and the register was not among the inputs to the analysis. It is requested from the council (P-01, P-12).

**Requests needed:** P-01, P-12

### T-11.2

**Controls tested:** C-11.4, C-11.5

**Test step.** From the contract register, select procurements awarded in the last three years across the value bands and services, including each contract examined in T-01.1. For each, inspect the procurement file and confirm whether it documents the progress of the procedure with the information that supports the decisions taken and is still held [CPR-34, cl. 9.3], and whether written evidence of the purchase is held [CPR-35, cl. 10.1]. For each selected contract above the Threshold figure obtained in T-06.1, obtain the Service Director's written report and confirm that it is retained [CPR-32, cl. 9.1] [CPR-33, cl. 9.2]. Record what each file holds.

**Sample.** No data sample: The selection is drawn in the field from the council's contract register (P-01). Whether a file exists and what it holds cannot be seen in payments or notices.

**Requests needed:** P-01, P-02, P-13

### T-11.3

**Controls tested:** C-11.1

**Test step.** Ask who prepares the published spend file and what criteria govern replacing a payee's name with 'Redacted' [analytics `population.excluded.redacted_supplier.rows`]; redaction can be proper, for example for payments to individuals. Obtain the written criteria and, for a selection of redacted rows the council identifies from its own ledger, confirm whether each meets them [CPR-06, cl. 5.1.1]. Separately, obtain the list of invitations to tender issued in the period and confirm where the details of each were published [CPR-07, cl. 5.2]. Record the criteria, the selection examined and the place of publication.

**Sample.** No data sample: The selection is drawn in the field from the council's ledger extract of redacted rows and its list of invitations to tender (P-12). Redacted rows carry no payee in the published data and are excluded from every flagged list, so the data cannot supply a sample.

**Requests needed:** P-12

### T-11.4

**Controls tested:** C-11.3

**Test step.** Obtain the contract information reported to the relevant board for each month of the period and confirm, service area by service area, whether a report was made for each month and in the required format [CPR-09, cl. 5.3]. Record the months and service areas for which a report is held.

**Sample.** No data sample: No draw from the data: the test covers every month of the period for every service area, from the board's own papers (P-12), which are not in the data.

**Requests needed:** P-12

## PBC list (requests to the council)

| Ref | Request | Needed for |
| --- | --- | --- |
| P-01 | Contract register extract, as a spreadsheet, of every contract in force or awarded between 2026-05-01 and 2026-07-31 and in the three years before: reference, supplier, title, service, category (goods, services, works, concession, light touch), procedure or route used, start date, end date, extension options, awarded value and whether that value is annual or whole-life, and date entered on the register. Please mark the entries for the suppliers in the sample files. | T-01.1, T-01.2, T-02.1, T-02.2, T-02.4, T-03.1, T-06.2, T-06.3, T-04.1, T-09.1, T-09.2, T-11.1, T-11.2 |
| P-02 | The Threshold figures published on the Procurement intranet page for each contract category, with the dates each figure was in force during the period and the three years before, whether each is stated inclusive or exclusive of Value Added Tax, and a copy or screenshot of the page. | T-06.1, T-06.2, T-06.3, T-04.2, T-07.1, T-08.3, T-09.2, T-11.2 |
| P-03 | For the suppliers and transactions in the sample files: the purchase order, the invoice (showing invoice number and date) and the contract or order reference each payment was made under, and for each sampled supplier a finance-system report of spend to date by contract or order. | T-01.1, T-01.2, T-01.4, T-02.3, T-03.1, T-05.1, T-05.2, T-04.1 |
| P-04 | For the contracts behind the suppliers and transactions in the sample files: the quotation or tender record from the Procurement Portal (invitations issued and to whom, responses received, evaluation and award), the Invitation to Tender where one was issued, and the contract notice or advert with its publication date and the officer who issued it. | T-01.1, T-01.2, T-01.4, T-02.3, T-03.2, T-06.2 |
| P-05 | The council's written guidance on estimating Total Contract Value and on adding up repeat purchases, including whether Value Added Tax is included when a contract is placed in a value band, and the record of any advice sought in the period on the application of the Procurement Legislation to repeat purchases. | T-01.3, T-06.3 |
| P-06 | The register of exceptions and waivers granted or refused between 2026-05-01 and 2026-07-31 and in the year before: supplier, contract value, ground, date requested, approver and date approved, date the contract was entered into; with the exception reports, the minutes of the board that received them and the S151 Officer's record for the items the auditor selects. | T-02.3, T-03.2, T-07.1, T-07.2, T-07.3 |
| P-07 | A list of contracts awarded in the period without competition under Appendix C, showing for each the route (excluded under the Procurement Legislation, Provider Selection Regime, purchasing scheme with no further competition), supplier, annual and total value, approver and approval date; with, for the items the auditor selects, the Monitoring Officer's written approval, any board approval, the Provider Selection Regime decision record and the advice on use of the purchasing scheme. | T-02.3, T-08.2, T-08.3 |
| P-08 | For the suppliers in the sample files whose contract was extended or varied: the contract clause relied on, the S151 Officer's approval of the extension, the Monitoring Officer's and S151 Officer's written approval of the variation, and any report to the relevant board with its minute, each with its date. | T-03.1, T-04.2 |
| P-09 | A list of contracts awarded in the period with award value and date, and for the awards the auditor selects and the contracts behind the sample files: the decision record (Scheme of Delegation entry and any written nomination by the Service Director, board report and minute, Key Decision entry and Forward Plan notice, Executive approval or delegation) and the budget provision the award was made against. | T-04.1, T-09.1, T-09.2 |
| P-10 | A description of the check the payment system applies to a second invoice from the same supplier with the same amount or invoice number, the system settings or exception reports that show it in operation during the period, and any recovery of repeated payments recorded in the period. | T-05.3 |
| P-11 | For the suppliers and transactions in the two placement sample files: confirmation from the service of whether each payment is a fee for an individual placement or package, the contract or framework it is paid under where there is one, and access under the council's arrangements for case files to the record of the reasons for the choice of provider for the individuals concerned. | T-08.1, T-08.4 |
| P-12 | The published register of contracts as it stood at 2026-07-31 and where it is published; the written criteria for redacting payee names in the published spend file and a ledger extract of the redacted rows for the period; the list of invitations to tender issued in the period and where the details of each were published; and the contract information reported to the relevant board by each service area for each month of the period. | T-11.1, T-11.3, T-11.4 |
| P-13 | The procurement file for each procurement the auditor selects from the contract register, including the documentation of the procedure and, for contracts above the Threshold, the Service Director's written report. | T-11.2 |
| P-14 | The council's written position, or the Monitoring Officer's guidance, on how a contract valued exactly at a band boundary is treated (exactly £500,000, exactly £2,500,000 and exactly the Threshold), how many Threshold categories are applied, and which constitutional provisions the blank Call-In and Forward Plan cross-references in Appendix A refer to. | T-06.1, T-09.3 |
