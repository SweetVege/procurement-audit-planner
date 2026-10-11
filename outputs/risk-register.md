# Procurement risk register — Revision 2

> These are **risk indicators to investigate**, drawn from public data. None of them is a finding of wrongdoing by the council, a service, an officer or a supplier.

## Header

- **Status:** Revision 2, built 2026-10-10 18:31. Every risk has an auditor decision.
- **Inputs:** `outputs/rules.json`, `outputs/analytics.json`, `outputs/history.json`.
- **Scoring method:** the council's own, as recorded in history.json: 5×5 matrix, score and label read from the matrix cell, band from the band table.
- **Risks:** 11 rated, 0 excluded by the builder, 0 warning(s).
- **Every figure** below was filled from analytics.json by `build_register.py`; none was typed.

### Scoring-method conflicts

The papers disagree with themselves in the places below. One reading is used, the other is marked, and neither has been corrected.

- IMP-06 records the impact level 'Medium' at 2, which disagrees with the matrix axis (Negligible = 1, Minor = 2, Medium = 3, Major = 4, Critical = 5). **Used:** the matrix axis. **Marked, not used:** IMP-06.
- The matrix prints **High** in the cells scoring 8, 9, 10, 12; the band table prints **Medium - High** for that range (BND-02). **Used:** the matrix label, shown as printed. **Marked, not used as the label:** the band-table name, shown beside it.
- DIS-05: **Used:** The score and label printed in the matrix cell, with the band looked up only where a printed band-table range contains that score. **Marked, not used:** Any assumed band for the scores that fall between the printed ranges; none is inferred. **Effect:** None on this draft: no rated risk has a score that falls between the printed ranges. If one did, the register would show the matrix label and no band.
- DIS-06: **Used:** The band table (Table 4), which attaches 'Add to Corporate Risk Register' to the Extreme band only. It is preferred because it is the table printed with the matrix. **Marked, not used:** The lower entry score for the Corporate Risk Register printed in Figure 4, and the wording of the escalation paragraph in running text. **Effect:** None on any likelihood, impact, score, matrix label or band. It matters only to escalation: this register does not say whether any risk would go to the Corporate Risk Register, and under the Figure 4 reading some risks banded Medium - High would also be candidates. That is for the auditor to weigh.
- DIS-07: **Used:** Neither reading. The Financial loss column of the impact table is not used for any rating in this register, because the percentage ranges printed for Medium and Major overlap and history.json also records the money ranges of that column as incompletely printed. **Marked, not used:** Both printed percentage ranges for the adjoining Medium and Major levels; neither is interpreted. **Effect:** The one risk that might have been rated in the financial column (R-05, repeated payments) is rated in the Reputation column instead. No other rating is affected; every other risk is rated in the Compliance column.

### What changed in this revision

- **R-09** (AUDITOR OVERRIDE): likelihood 2 → 3. Likelihood set to the score the auditor gave by override; the rubric row, justification, impact, evidence and focus are left as drafted. Auditor: “Raise likelihood to 3: two split-purchase windows totalling £3.5m sit at the £500,000 Key Decision band, and that exact value falls in no Appendix A band.”
- Rejected by the auditor (out of scope): R-10.
- Approved unchanged: R-01, R-02, R-03, R-05, R-06, R-04, R-07, R-08, R-11.

## Summary

| Risk | Title | Likelihood | Impact | Score | Matrix label | Band | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | Purchases divided or repeated so that the requirements of a higher value band do not apply | Likely (3) | Medium (3) | 9 | High | Medium - High (Amber) | Approved |
| R-02 | Spend at or above the publication value with no matching contract notice | Likely (3) | Medium (3) | 9 | High | Medium - High (Amber) | Approved |
| R-03 | Spend continuing after the matching contract notice has ended | Likely (3) | Medium (3) | 9 | High | Medium - High (Amber) | Approved |
| R-05 | Repeated payments of the same amount to the same supplier | Likely (3) | Medium (3) | 9 | High | Medium - High (Amber) | Approved |
| R-06 | Contracts above the procurement-legislation Threshold handled under a lower value band | Unlikely (2) | Major (4) | 8 | High | Medium - High (Amber) | Approved |
| R-04 | Spend running ahead of the awarded contract value | Likely (3) | Minor (2) | 6 | Moderate | Moderate | Approved |
| R-07 | Competition waived or excepted without the required grounds, approval or record | Unlikely (2) | Medium (3) | 6 | Moderate | Moderate | Approved |
| R-08 | Appendix C exclusions from competition applied without the required approval or record | Unlikely (2) | Medium (3) | 6 | Moderate | Moderate | Approved |
| R-09 | Contracts awarded without the approval their value requires | Likely (3) | Minor (2) | 6 | Moderate | Moderate | Auditor override |
| R-10 | Contracts not in the required written form or without the required terms and safeguards | Unlikely (2) | Minor (2) | 4 | Moderate | Moderate | Rejected |
| R-11 | Procurement records and published information incomplete | Unlikely (2) | Minor (2) | 4 | Moderate | Moderate | Approved |

## R-01 Purchases divided or repeated so that the requirements of a higher value band do not apply

**Risk.** One requirement could be met through several smaller purchases, or through repeat purchases of a similar type, so that each stays under a value band at which the Rules require quotations, a notice, a tender or a Key Decision. The Rules say a contract must not be artificially split or disaggregated [CPR-15, cl. 6.16], require advice to be sought where repeat purchases are envisaged [CPR-16, cl. 6.17], and require value to be estimated over the full potential duration of the contract [CPR-14, cl. 6.15].

**Likelihood: 3 Likely** (rubric L3). Rubric row L3: the pattern is present in one test. The split-purchase test found 41 general-procurement suppliers [analytics `tests.split_purchases.per_threshold['25000.00'].headline_general_procurement.windows`] with two or more payments inside a 30-day window, each under £25,000 and together reaching it, and 2 at the £500,000 band [analytics `tests.split_purchases.per_threshold['500000.00'].headline_general_procurement.windows`]. Threshold clustering is not a second signal: its band-to-comparator ratio at £25,000 is 0.8846, which is not above one [analytics `tests.threshold_clustering.per_threshold['25000.00'].band_to_comparator_ratio`]. No point is added for a repeat finding: the one audit of this subject on record, Contract Letting, carries a positive opinion [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)].

**Impact: 3 Medium** (Compliance (litigation, regulatory, contract)). If one requirement had been divided across purchases, a contract would have been let without the invited quotations and notice its full value calls for [CPR-57, cl. App B row B1] [CPR-59, cl. App B row B2], and a supplier who was given no opportunity to quote could contest it. That fits the Compliance column at Medium: a reasonable possibility of successful legal challenge or of regulatory interest [IMP-03: Medium (3)]. The combined value of the windows is spend, not a loss, so the financial column is not used.

**Rating: 9** — matrix label **High**, band **Medium - High (Amber)**.

**Evidence.**

- Split-purchase test at the £25,000 band: 41 general-procurement windows with a combined value of £2,310,961.19 [analytics `tests.split_purchases.per_threshold['25000.00'].headline_general_procurement.gbp`]. The 130 placement-tagged windows are reported separately and are not counted, because periodic care fees recur [analytics `tests.split_purchases.per_threshold['25000.00'].placement_reported_separately.windows`].
- Split-purchase test at the £500,000 band, above which an award is a Key Decision [CPR-04, cl. 4.3]: 2 general-procurement windows with a combined value of £3,509,528.75 [analytics `tests.split_purchases.per_threshold['500000.00'].headline_general_procurement.gbp`].
- Evidence against clustering: 46 payments sit in the band just under £25,000 against 52 in the equal band just above it [analytics `tests.threshold_clustering.per_threshold['25000.00'].band_count`], and 0 sit in the band just under £500,000 [analytics `tests.threshold_clustering.per_threshold['500000.00'].band_count`].
- Caveat carried from the test: payments of £500 or less are not published, so the counts are lower bounds [analytics `tests.split_purchases.parameters.lower_bound_note`]. The date is a payment-run timestamp, not an order or invoice date. Several payments to one supplier inside a window can be instalments or separate orders under one properly let contract, so each window is a prompt to look at the orders behind it and nothing more.
- Not used as a signal: the £1,000 band of either test. With a publication floor of £500 nearly every pair of payments reaches that band [analytics `tests.split_purchases.per_threshold['1000.00'].threshold_to_floor_ratio`].
- Not tested: windows measured against the procurement-legislation Threshold, because that figure is not in rules.json [analytics `skipped`]; see R-06.
- Context: Contract Letting was audited and given a positive opinion [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)]; the papers print no findings for it. The Risk Management Strategy lists competition and markets as a source of risk [THM-03: Competition & Markets].

**Proposed focus.** For the general-procurement windows in the split-purchase list, obtain the orders, quotations and contract behind the payments and establish whether they belong to one requirement or to several. Start with the windows at the £500,000 band, then the largest at the £25,000 band. Ask how services add up repeat purchases when they estimate contract value [CPR-16, cl. 6.17].

## R-02 Spend at or above the publication value with no matching contract notice

**Risk.** A supplier could be paid amounts that, over a year, reach the value at which the Rules require at least three invited quotations [CPR-57, cl. App B row B1] [CPR-59, cl. App B row B2] and a published contract notice [CPR-58, cl. App B row B1] [CPR-60, cl. App B row B2], without that competition or notice having taken place.

**Likelihood: 3 Likely** (rubric L3). Rubric row L3: the pattern is present in one test. 186 general-procurement suppliers whose annualised estimate is at or above £25,000 have no exact name match to a supplier on a Contracts Finder notice active in the spend window [analytics `tests.off_contract.headline_general_procurement.suppliers`]. The high-value supplier count [analytics `tests.high_value_suppliers.headline_general_procurement.suppliers`] is the population this test starts from, not a pattern in its own right, so it is not counted as a second test. No point is added for a repeat finding: Contract Letting carries a positive opinion [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)].

**Impact: 3 Medium** (Compliance (litigation, regulatory, contract)). If a contract of this value had been let with no invitation to quote and no notice, a supplier who had no opportunity to bid could contest it, and the duty to publish the notice would be unmet [CPR-58, cl. App B row B1]. That fits the Compliance column at Medium: a reasonable possibility of successful legal challenge or of regulatory interest [IMP-03: Medium (3)]. Spend for which no notice was found is not a loss, so the financial column is not used.

**Rating: 9** — matrix label **High**, band **Medium - High (Amber)**.

**Evidence.**

- Off-contract test: of 674 suppliers at or above the publication value, 40 match a notice exactly and 634 do not [analytics `tests.off_contract.unmatched.suppliers`]. The general-procurement headline is 186 suppliers paid £24,716,801.62 in the window [analytics `tests.off_contract.headline_general_procurement.gbp`], of which 6 are near-name matches for the auditor to confirm.
- Reported separately and not counted: 309 placement-tagged suppliers [analytics `tests.off_contract.placement_reported_separately.suppliers`]. Appendix C excludes individual placements and packages from competition [CPR-71, cl. App C row F]; see R-08.
- Caveat carried from the test: 'no notice found' is an indicator to check against the council's own contract register and nothing more. The export holds published notices, not a register; a contract awarded before the period it covers, advertised only elsewhere, called off under another buyer's framework, or exempt, has no notice in it, and only a small share of high-value suppliers is expected to match by name [analytics `tests.off_contract.caveat`]. No contract register was available to the test [analytics `contracts.register_note`].
- Caveat: the annualised estimate scales 3 months of spend to a year and may not be typical [analytics `tests.high_value_suppliers.parameters.annualised_estimate`]. Matching is by name only, because the spend data carries no company number [analytics `tests.off_contract.parameters.companies_house_key`]. The test says nothing about suppliers under the publication value, who would never appear on Contracts Finder.
- Context: Contract Letting was audited and given a positive opinion [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)]; the papers print no findings for it.

**Proposed focus.** Reconcile the general-procurement suppliers in the list to the council's contract register [CPR-08, cl. 5.2.1], taking the near-name matches first. For those with no register entry, ask for the quotation or tender record and the notice, or for the waiver or Appendix C approval that was relied on.

## R-03 Spend continuing after the matching contract notice has ended

**Risk.** Purchasing from a supplier could continue after the contract's end date without an extension that the contract provides for having been approved by the S151 Officer [CPR-68, cl. App C row D], and without a new competition.

**Likelihood: 3 Likely** (rubric L3). Rubric row L3: the pattern is present in one test. 5 suppliers at or above the publication value were paid in the spend window although every notice matched to them ended before the window opened [analytics `tests.expired_notice_spend.count`]. No other test bears on extensions, and no audit of this subject with an adverse opinion is recorded; the extension rule is [CPR-68, cl. App C row D].

**Impact: 3 Medium** (Compliance (litigation, regulatory, contract)). If spend continued with no contract in force and no approved extension [CPR-68, cl. App C row D], it would be spend that had not been through the competition its value calls for, which another supplier could contest. That fits the Compliance column at Medium: a reasonable possibility of successful legal challenge or of regulatory interest [IMP-03: Medium (3)]. The amounts paid are spend, not a loss, so the financial column is not used.

**Rating: 9** — matrix label **High**, band **Medium - High (Amber)**.

**Evidence.**

- Expired-notice test: 5 suppliers, paid £240,780.48 in the window, an annualised estimate of £963,121.92 [analytics `tests.expired_notice_spend.gbp`]. All of them carry the general-procurement tag [analytics `tests.expired_notice_spend.by_tag.general_procurement.suppliers`].
- The window opened on 2026-05-01; a notice counts as ended if its end date falls before that date [analytics `tests.expired_notice_spend.parameters.window_start`].
- Caveat carried from the test: a newer contract may exist with no notice on Contracts Finder, and an extension may have been approved under Appendix C without a new notice. The export holds published notices, not a contract register, so each case is an indicator to check against the council's register [analytics `tests.expired_notice_spend.caveat`].
- Caveat: the match is by exact normalised name only, and the annualised estimate scales 3 months of spend to a year [analytics `tests.expired_notice_spend.parameters.match`].

**Proposed focus.** For each supplier in the expired-notice list, ask for the contract currently in force: a later award, or the extension clause relied on together with the S151 Officer's approval of the extension [CPR-68, cl. App C row D].

## R-05 Repeated payments of the same amount to the same supplier

**Risk.** An invoice could be paid more than once. No clause of the Contract Rules sets a duplicate-payment test [analytics `tests.duplicates.rule_note`]: this is a payment-control indicator. The nearest rule is that written evidence must be held for every purchase [CPR-35, cl. 10.1], which is what a repeated payment would be checked against.

**Likelihood: 3 Likely** (rubric L3). Rubric row L3: the pattern is present in one test. The duplicates test found 35 general-procurement groups of same-supplier, same-amount payments made at different times within 7 days [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.groups`], and 28 groups sharing one timestamp [analytics `tests.duplicates.per_tier.same_timestamp.headline_general_procurement.groups`]. Both tiers belong to the same test. No point is added for a repeat finding: Accounts Payable carries a positive opinion [AUD-15: Accounts Payable — Reasonable Assurance (End of December 2025)].

**Impact: 3 Medium** (Reputation). If payments had been repeated in error on the scale the indicator allows, criticism of payment controls by an external agency such as the external auditor could be expected: the Reputation column at Medium [IMP-03: Medium (3)]. The amount paid beyond the first payment in the general-procurement groups at different times, £299,374.24, is an upper indicator and not a loss [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.gbp_beyond_first`]. The financial column is not used, because the ranges printed for its adjoining levels overlap [DIS-07: In Table 1 the financial percentage ranges printed for two adjacent…].

**Rating: 9** — matrix label **High**, band **Medium - High (Amber)**.

**Evidence.**

- Different-time tier: 35 general-procurement groups covering 86 payments [analytics `tests.duplicates.per_tier.different_time.headline_general_procurement.rows`].
- Same-timestamp tier: 28 general-procurement groups covering 62 payments, with £49,821.92 beyond the first payment in each group [analytics `tests.duplicates.per_tier.same_timestamp.headline_general_procurement.gbp_beyond_first`]. Because the date is a payment-run timestamp, a same-timestamp group may be several lines of one run.
- Reported separately and not counted: 204 placement-tagged groups at different times and 400 sharing a timestamp [analytics `tests.duplicates.per_tier.different_time.placement_reported_separately.groups`]. Periodic care fees of a fixed amount recur.
- Caveat: an identical amount paid twice to one supplier can equally be two periodic charges, two orders at a list price, or one invoice per site. The published data carries no invoice number, so the test cannot tell these apart; and payments of £500 or less are not published, so the counts are lower bounds [analytics `threshold_source.publication_floor.value`].
- Context: Accounts Payable was audited and given a positive opinion [AUD-15: Accounts Payable — Reasonable Assurance (End of December 2025)]; the papers print no findings for it.

**Proposed focus.** For the general-procurement groups at different times, match each payment to its invoice number and order to establish whether the payments are for separate supplies. Then ask what duplicate-invoice check the payment system applies and whether it was in operation throughout the period.

## R-06 Contracts above the procurement-legislation Threshold handled under a lower value band

**Risk.** A contract whose value is above the Threshold set by the Procurement Legislation could be let, or repeat purchases could add up to that value, without the tender procedure and advert the Rules require above it [CPR-17, cl. 6.19] [CPR-63, cl. App B row D] [CPR-64, cl. App B row D] [CPR-16, cl. 6.17]. The Threshold figures are not printed in the Rules, which refer the reader to the council's intranet.

**Likelihood: 2 Unlikely** (rubric L2). Rubric row L2: the public data cannot speak to this risk. Every tier of the clustering, split-purchase and high-value supplier tests that depends on the Threshold was skipped [analytics `skipped`], for the reason the analysis gives: parameter RELEVANT_THRESHOLD is null in rules.json. The rules that turn on the Threshold include [CPR-16, cl. 6.17] and [CPR-63, cl. App B row D].

**Impact: 4 Major** (Compliance (litigation, regulatory, contract)). Above the Threshold the Rules apply the procedures of the Procurement Legislation itself [CPR-63, cl. App B row D], so a contract let outside them would be exposed to challenge under that legislation and not only under the council's own Rules. That fits the Compliance column at Major: a high possibility of legal challenge or of regulatory intervention [IMP-02: Major (4)].

**Rating: 8** — matrix label **High**, band **Medium - High (Amber)**.

**Evidence.**

- Skipped tiers: threshold_clustering, split_purchases and high_value_suppliers, each at the tiers RELEVANT_THRESHOLD and THRESHOLD_GOODS_SERVICES [analytics `skipped`].
- All four Threshold parameters in rules.json are null [analytics `threshold_source.null_parameters`]. rules.json records this as a gap: the figures that drive most value bands are not printed in the document.
- Rules that cannot be tested until the figures are supplied include the repeat-purchase rule [CPR-16, cl. 6.17], the tender and advert requirements above the Threshold [CPR-17, cl. 6.19] [CPR-63, cl. App B row D] [CPR-64, cl. App B row D], the quotation band that ends at the Threshold [CPR-57, cl. App B row B1] and the approval bands that start or end at it [CPR-52, cl. App A row 1] [CPR-53, cl. App A row 2].
- rules.json also records that a value exactly equal to the Threshold falls in no band of Appendix B, and that the Rules count four categories of Threshold in one clause and three in another.
- The tests that did run used only the bands printed in the Rules [analytics `threshold_source.rule_types_used`]; their results are in R-01 and R-02.

**Proposed focus.** Supply the Threshold figures in force for the period so that the three tests can be re-run at those tiers. In fieldwork, take the largest general-procurement suppliers by annualised estimate and trace each to its tender record and advert [CPR-63, cl. App B row D] [CPR-64, cl. App B row D].

## R-04 Spend running ahead of the awarded contract value

**Risk.** Spend under a contract could grow beyond the value awarded without the variation having been approved as the Rules require: by the Monitoring Officer and S151 Officer [CPR-69, cl. App C row E], or by the relevant board for larger variations [CPR-70, cl. App C row E].

**Likelihood: 3 Likely** (rubric L3). Rubric row L3: the pattern is present in one test. Of the 19 suppliers that could be compared with a single active award, 8 have an annualised estimate of at least 1.25 times the yearly rate of the award [analytics `tests.spend_vs_award.count`]. No other test bears on variations, and no audit of this subject with an adverse opinion is recorded; the variation rule is [CPR-69, cl. App C row E].

**Impact: 2 Minor** (Compliance (litigation, regulatory, contract)). In these cases a contract was awarded and is still in force, so if spend had outrun the award the consequence would be a variation without its approval and report [CPR-69, cl. App C row E], not an award made without competition. That fits the Compliance column at Minor: a low possibility of legal challenge or of regulatory interest [IMP-04: Minor (2)]. Award values may be estimates or maxima, so the excess over the award is not a loss and the financial column is not used.

**Rating: 6** — matrix label **Moderate**, band **Moderate**.

**Evidence.**

- Spend-versus-award test: 8 of 19 comparable suppliers, paid £736,650.97 in the window [analytics `tests.spend_vs_award.gbp`]. All of them carry the general-procurement tag [analytics `tests.spend_vs_award.by_tag.general_procurement.suppliers`].
- The comparison is narrow by design: it covers only suppliers with an exact match to exactly one active single-supplier notice whose awarded value is above zero [analytics `tests.spend_vs_award.suppliers_eligible`].
- Caveat carried from the test: award values may be estimates or maxima, and 3 months of spend may not be typical of the year; payments in the window may also relate to work outside the matched contract [analytics `tests.spend_vs_award.caveat`].
- rules.json records as a drafting point that the variation row of Appendix C asks for 'an extension report', wording that fits the extension row; the rule is recorded as printed [CPR-70, cl. App C row E].

**Proposed focus.** For each supplier in the spend-versus-award list, compare spend to date with the contract value on the council's register and ask for the approved variation where spend exceeds it [CPR-69, cl. App C row E] [CPR-70, cl. App C row E]. Confirm first whether the published award value was an estimate, a maximum or an annual figure.

## R-07 Competition waived or excepted without the required grounds, approval or record

**Risk.** An exception or waiver could be relied on outside the grounds the Rules allow [CPR-23, cl. 7.2], sought after the event or approved by someone other than the officers named [CPR-24, cl. 7.3] [CPR-25, cl. 7.4.1] [CPR-26, cl. 7.4.2] [CPR-27, cl. 7.4.3], or left without the documentation and exception report the Rules require [CPR-28, cl. 7.5.1] [CPR-29, cl. 7.5.2] [CPR-30, cl. 7.5.3].

**Likelihood: 2 Unlikely** (rubric L2). Rubric row L2: the public data cannot speak to this risk and no test exists. A waiver leaves no trace in published payments or notices, so the waiver rules [CPR-23, cl. 7.2] [CPR-24, cl. 7.3] can be tested only from the council's own exception reports. The one audit on record that covers letting contracts carries a positive opinion, and the papers print no findings for it [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)].

**Impact: 3 Medium** (Compliance (litigation, regulatory, contract)). If a waiver had been relied on without the grounds or approval the Rules require [CPR-23, cl. 7.2], the result would be a contract let without competition, which another supplier could contest. That fits the Compliance column at Medium: a reasonable possibility of successful legal challenge or of regulatory interest [IMP-03: Medium (3)].

**Rating: 6** — matrix label **Moderate**, band **Moderate**.

**Evidence.**

- No test in analytics.json bears on waivers; the rule types the analysis drew thresholds from are listed at [analytics `threshold_source.rule_types_used`], and a waiver band was used only to locate a value boundary.
- rules.json records drafting points in the waiver clauses: words appear to be missing from the clause on exceptions in the middle value band, and its cross-reference on urgency may point to the wrong clause [CPR-26, cl. 7.4.2].
- rules.json records that the exception route is stated only above the lower value boundary [CPR-23, cl. 7.2]; none is stated for the band in which a single quote is required [CPR-56, cl. App B row A].
- Link to R-02: an approved waiver is one explanation for a high-value supplier with no matching notice [analytics `tests.off_contract.headline_general_procurement.suppliers`].
- Context: the Risk Management Strategy lists competition and markets as a source of risk [THM-03: Competition & Markets].

**Proposed focus.** Obtain the register of exceptions and waivers for the period. For a sample, confirm the ground relied on, that approval was given in advance by the officers named for that value band, and that an exception report went to the relevant board [CPR-29, cl. 7.5.2]. Compare the register with the unmatched suppliers under R-02.

## R-08 Appendix C exclusions from competition applied without the required approval or record

**Risk.** A contract could be treated as excluded from competition without the prior written approval the Rules require [CPR-65, cl. App C row A] [CPR-67, cl. App C row C], without the Provider Selection Regime process being followed and recorded [CPR-66, cl. App C row B], without the reasons for the choice of provider being recorded on the individual's case notes for a placement [CPR-71, cl. App C row F], or without board approval where the value is above the Threshold [CPR-72, cl. App C closing].

**Likelihood: 2 Unlikely** (rubric L2). Rubric row L2: the public data cannot speak to this risk. Patterns that appear only under the placement tag are not signals: 130 split-purchase windows [analytics `tests.split_purchases.per_threshold['25000.00'].placement_reported_separately.windows`] and 309 suppliers with no matching notice [analytics `tests.off_contract.placement_reported_separately.suppliers`] carry that tag, but periodic care fees recur and Appendix C excludes individual placements from competition [CPR-71, cl. App C row F]. Whether an approval was given or a reason recorded cannot be seen in payments or notices. The audit on record that covers buying care carries a positive opinion [AUD-18: Purchase of Residential and Nursing Care Provision — Reasonable Assurance (End of December 2025)].

**Impact: 3 Medium** (Compliance (litigation, regulatory, contract)). If an exclusion had been relied on without the approval the Rules require [CPR-65, cl. App C row A], the result would be a contract awarded directly with nothing on file to show the exclusion applied, which another provider could contest. That fits the Compliance column at Medium: a reasonable possibility of successful legal challenge or of regulatory interest [IMP-03: Medium (3)].

**Rating: 6** — matrix label **Moderate**, band **Moderate**.

**Evidence.**

- Placement-tagged spend in the population: 5,885 payments to 369 suppliers, £30,705,712.58 in the window [analytics `population.tags.care_or_education_placement.gbp`]. This is the size of the area the exclusion covers, not an indicator.
- Placement-tagged results reported separately by the tests: 130 split-purchase windows, 309 high-value suppliers with no matching notice and 204 same-amount groups at different times [analytics `tests.duplicates.per_tier.different_time.placement_reported_separately.groups`]. Periodic fees for an individual's care are expected to produce all three.
- Context: Purchase of Residential and Nursing Care Provision was audited and given a positive opinion [AUD-18: Purchase of Residential and Nursing Care Provision — Reasonable Assurance (End of December 2025)]. Personal Budgets (Direct Payments) carries an adverse opinion [AUD-16: Personal Budgets (Direct Payments) — Limited Assurance (End of December 2025)]; it is a different subject from letting contracts under Appendix C, so no point is added.
- rules.json records drafting points in Appendix C: words appear to be missing from the row on purchasing schemes [CPR-67, cl. App C row C], and the extension row names an approver but no report [CPR-68, cl. App C row D].
- The extension and variation rows of Appendix C have their own tests and are rated separately as R-03 and R-04.

**Proposed focus.** For a sample of placement-tagged suppliers, confirm that the reasons for the choice of provider are on the individual's case notes [CPR-71, cl. App C row F]. For a sample of awards under a purchasing scheme or a claimed legislative exclusion, confirm the Monitoring Officer's prior written approval [CPR-65, cl. App C row A] [CPR-67, cl. App C row C] and, above the Threshold, the board's approval [CPR-72, cl. App C closing].

## R-09 Contracts awarded without the approval their value requires

**Risk.** A contract could be entered into without a decision or delegation that covers it [CPR-02, cl. 4.1], without budget provision [CPR-03, cl. 4.2], without being treated as a Key Decision where its value requires that [CPR-04, cl. 4.3] [CPR-54, cl. App A row 3], or without the board or Executive approval set for its value band in Appendix A [CPR-05, cl. 4.4] [CPR-53, cl. App A row 2] [CPR-55, cl. App A row 4].

**Likelihood: 3 Likely** (set by the auditor). Rubric row L2: the public data cannot speak to this risk and no test exists. Payments and notices do not show who approved an award, so the approval rules [CPR-04, cl. 4.3] [CPR-05, cl. 4.4] can be tested only from decision records. The audit on record that covers letting contracts carries a positive opinion, and the papers print no findings for it [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)].

**Impact: 2 Minor** (Compliance (litigation, regulatory, contract)). If an award had been made without the approval set for its value [CPR-05, cl. 4.4], the consequence would be a decision taken outside the council's own scheme of authority, to be regularised internally, with the competition itself unaffected. That fits the Compliance column at Minor: a low possibility of legal challenge or of regulatory interest [IMP-04: Minor (2)].

**Rating: 6** — matrix label **Moderate**, band **Moderate**. **AUDITOR OVERRIDE**: “Raise likelihood to 3: two split-purchase windows totalling £3.5m sit at the £500,000 Key Decision band, and that exact value falls in no Appendix A band.”.

**Evidence.**

- No test in analytics.json bears on approvals. Approval bands were used only to locate value boundaries [analytics `threshold_source.rule_types_used`].
- rules.json records that a value of exactly £500,000 falls in no band of Appendix A, while the waiver clause includes it; analytics.json marks that boundary as printed inconsistently [analytics `thresholds[2].inclusivity_conflict`].
- rules.json records a contradiction at the top band of Appendix A: the heading reads £2,500,000 'or more' and the text beside it reads 'in excess of' that figure [CPR-55, cl. App A row 4]. It also records that the cross-references to the Call-In and Forward Plan parts are left blank in the Key Decision row [CPR-54, cl. App A row 3].
- Link to R-01: the split-purchase windows at the £500,000 band sit at the value above which an award is a Key Decision [analytics `tests.split_purchases.per_threshold['500000.00'].headline_general_procurement.windows`].
- The Risk Management Strategy lists compliance, including contract compliance, as an impact category [THM-04: Compliance (litigation, regulatory, contract)].

**Proposed focus.** For a sample of awards in each Appendix A band, trace the approval: the Service Director's delegation, the board report, the Key Decision entry and, at the top band, the Executive's approval [CPR-52, cl. App A row 1] [CPR-53, cl. App A row 2] [CPR-54, cl. App A row 3] [CPR-55, cl. App A row 4]. Ask how awards at the exact boundary values are treated.

## R-10 Contracts not in the required written form or without the required terms and safeguards

**Rejected by the auditor: out of scope.** “Contract form and terms will be covered by a separate contract-management review.”

**Risk.** A contract could be entered into without being in writing in an approved form [CPR-36, cl. 10.2], without the standard clauses and minimum terms [CPR-39, cl. 10.5] [CPR-41, cl. 10.7], without a Data Protection Impact Assessment [CPR-42, cl. 10.7.7], without the risk assessment, insurance or performance-bond consideration the Rules require [CPR-44, cl. 11.2] [CPR-46, cl. 11.4] [CPR-47, cl. 11.5], or without being sealed where its value requires it [CPR-50, cl. 11.11].

**Likelihood: 2 Unlikely** (rubric L2). Rubric row L2: the public data cannot speak to this risk and no test exists. The form and content of a contract cannot be seen in payments or notices, so the contract-form rules [CPR-36, cl. 10.2] [CPR-41, cl. 10.7] can be tested only from contract files. The Risk Management Strategy lists contracts and partnerships as a source of risk [THM-01: Contracts & Partnerships]; no audit of contract documentation is recorded.

**Impact: 2 Minor** (Compliance (litigation, regulatory, contract)). If a contract lacked the written form, terms or insurance the Rules require [CPR-41, cl. 10.7], the council's position in any later dispute with the contractor would be weaker, case by case. That fits the Compliance column, which covers contract, at Minor: a low possibility of legal challenge or of regulatory interest [IMP-04: Minor (2)].

**Rating: 4** — matrix label **Moderate**, band **Moderate**.

**Evidence.**

- No test in analytics.json bears on contract form [analytics `threshold_source.rule_types_used`].
- rules.json records a gap: no award procedure, and so no requirement for writing, is stated for the smallest purchases, because Appendix B starts above £1,000 [CPR-36, cl. 10.2] [CPR-56, cl. App B row A].
- rules.json records drafting points: the sub-clause on the contractor's tax status under the insurance and risk clause is not a complete sentence [CPR-47, cl. 11.5], and one item in the list of minimum contract clauses is a free-standing requirement about specifications [CPR-41, cl. 10.7].
- The sealing rule turns on the Threshold [CPR-50, cl. 11.11], which is not in rules.json [analytics `threshold_source.null_parameters`]; see R-06.
- Context: contracts and partnerships, including procurement contract management, are listed as a source of risk [THM-01: Contracts & Partnerships].

**Proposed focus.** For a sample of contracts across the value bands, inspect the contract file for a signed or sealed agreement in an approved form, the minimum clauses, evidence of insurance, the Data Protection Impact Assessment, and the bond or the written risk assessment where no bond was taken [CPR-44, cl. 11.2] [CPR-46, cl. 11.4].

## R-11 Procurement records and published information incomplete

**Risk.** The records the Rules require could be incomplete: published expenditure [CPR-06, cl. 5.1.1], the published register of contracts [CPR-08, cl. 5.2.1], monthly contract information to the relevant board [CPR-09, cl. 5.3], the written report on awards above the Threshold and its retention [CPR-32, cl. 9.1] [CPR-33, cl. 9.2], documentation of each procurement procedure [CPR-34, cl. 9.3], written evidence of each purchase [CPR-35, cl. 10.1] and notification of each award to the procurement lead [CPR-38, cl. 10.4].

**Likelihood: 2 Unlikely** (rubric L2). Rubric row L2: the public data cannot speak to this risk and no test exists. Features of the published spend file are cited as context only: 2,015 rows name the supplier as 'Redacted' [analytics `population.excluded.redacted_supplier.rows`], which may be a proper use of redaction and is not a test result. Whether the internal records exist [CPR-34, cl. 9.3] [CPR-35, cl. 10.1] can be established only from the files. No audit of procurement records is recorded, and the papers print no findings for the audits that are [AUD-01: Contract Letting — Reasonable Assurance (End of March 2025)].

**Impact: 2 Minor** (Compliance (litigation, regulatory, contract)). If records or published information were incomplete [CPR-34, cl. 9.3], the council would be less able to show that an award was properly made, and a publication duty could be unmet [CPR-08, cl. 5.2.1]; the awards themselves would be unaffected. That fits the Compliance column at Minor: a low possibility of legal challenge or of regulatory interest [IMP-04: Minor (2)].

**Rating: 4** — matrix label **Moderate**, band **Moderate**.

**Evidence.**

- Published spend, context only: 2,015 rows worth £2,746,746.71 name the supplier as 'Redacted' and are excluded from every test [analytics `population.excluded.redacted_supplier.gbp`]; 87 rows have a blank expenditure category [analytics `population.blank_expenditure_category_rows`]; 1 row is dated outside the month of its file [analytics `population.rows_dated_outside_file_month.rows`]. Redaction can be proper, for example for payments to individuals.
- The council's contract register was not among the inputs, so no test result has been checked against it [analytics `contracts.register_note`]. This describes the inputs to this plan and says nothing about whether the register is published [CPR-08, cl. 5.2.1].
- The Contracts Finder export holds 141 notices for the council [analytics `contracts.rows_for_council`], and only a small share of high-value suppliers is expected to match one by name [analytics `contracts.caveat`]; see R-02.
- rules.json records a drafting point: the list of what must be published numbers its second and third items as if they were separate clauses [CPR-08, cl. 5.2.1].
- The papers print no findings, recommendations or agreed actions for any audit, so nothing is known from them about record-keeping; the Strategy notes the monitoring of agreed audit recommendations as an Internal Audit output [THM-15: Monitoring of agreed audit recommendations].

**Proposed focus.** Compare the council's published contract register with the notices on Contracts Finder and with the high-value supplier list [CPR-08, cl. 5.2.1]. For a sample of procurements, confirm that the file documents the procedure and is retained [CPR-34, cl. 9.3], and that the award was notified to the procurement lead [CPR-38, cl. 10.4]. Ask what criteria govern redaction of supplier names in the published spend [CPR-06, cl. 5.1.1].

## Rules cited

The start of each cited rule's verbatim quote, copied from rules.json by the builder.

| Rule | Clause | Page | Quote from the Contract Rules (excerpt) |
| --- | --- | --- | --- |
| CPR-02 | 4.1 | 2 | All contracts must be in accordance with a decision: 4.1.1 of the Council; or 4.1.2 of the Executive; or 4.1.3 within the Council’s Scheme of Delegation by: |
| CPR-03 | 4.2 | 3 | No contract shall be entered into unless it is in accordance with an existing budgetary provision within the Budget approved by the Council. |
| CPR-04 | 4.3 | 3 | Any contract award with a value over £500,000 is a Key Decision of the Council. |
| CPR-05 | 4.4 | 3 | Where a Service Director does not have delegated authority to enter into a contract, approval in accordance with Appendix A is required before the contract can … |
| CPR-06 | 5.1.1 | 3 | Expenditure exceeding £500, including payments to suppliers and contractors. |
| CPR-08 | 5.2.1 | 3 | A register of contracts, including those in progress and those awarded, with key information such as the contract value, duration and supplier. |
| CPR-09 | 5.3 | 3 | Service areas are therefore responsible for reporting contract information to the relevant board on a monthly basis in a format as required by Procurement … |
| CPR-14 | 6.15 | 4 | Total Contract Value is a genuine estimate of the total value over the full potential duration of the contract, not just the initial term. |
| CPR-15 | 6.16 | 5 | There shall be no artificial splitting or disaggregation of a contract to avoid the application of the provisions of the Procurement Legislation and/or these … |
| CPR-16 | 6.17 | 5 | The Procurement Legislation can cover contracts which are initially below the stated relevant Threshold where they constitute repeat purchases and/or purchases … |
| CPR-17 | 6.19 | 5 | An electronic Invitation to Tender shall be issued by the Council for all contracts with an estimated value that is more than the appropriate Threshold and … |
| CPR-23 | 7.2 | 6 | Subject to 7.4 the requirement for the Council to conduct a competitive purchasing process, contracts with a value of more than £24,999.99, may be excepted or … |
| CPR-24 | 7.3 | 6 | Only the Monitoring Officer and/or the S.151 Officer may grant a waiver or an exception to these Rules, subject to exception values and delegation thresholds … |
| CPR-25 | 7.4.1 | 6 | for all contracts up to the Threshold, the S.151 Officer must approve the exception; |
| CPR-26 | 7.4.2 | 6 | for contracts above the relevant Threshold and up to £500,000, the S.151 Officer will consult with the Monitoring Officer and the appropriate Executive … |
| CPR-27 | 7.4.3 | 6 | for contracts over £500,000 the S.151 Officer and the Monitoring Officer will make a recommendation to the Executive provided an exception report has been … |
| CPR-28 | 7.5.1 | 6 | be fully documented; |
| CPR-29 | 7.5.2 | 6 | for any contract where the requirement to hold a competitive process is not excluded by the Procurement Legislation, be subject to a written exception report … |
| CPR-30 | 7.5.3 | 7 | be subject to approval by the S.151 Officer who shall record they have considered the reasons for the waiver and that they are satisfied that the circumstances … |
| CPR-32 | 9.1 | 7 | A written report in accordance with the Procurement Legislation shall be produced by the relevant Service Director for each contract that is awarded which is … |
| CPR-33 | 9.2 | 7 | This report may be requested by the Cabinet Office and shall be kept for three years. |
| CPR-34 | 9.3 | 8 | Such documentation must be kept for three years from the award of the contract. |
| CPR-35 | 10.1 | 8 | There should be written evidence of all purchases (which shall include electronic evidence). |
| CPR-36 | 10.2 | 8 | All contracts entered into by the Council as detailed in Appendix B must be in writing in a form approved by the Monitoring Officer or their delegated officer. |
| CPR-38 | 10.4 | 8 | The relevant Service Director must formally notify the Service Lead for Commissioning and Procurement (or nominated officer) of the award of all contracts for … |
| CPR-39 | 10.5 | 8 | Every contract shall include the standard clauses set out in the relevant Standard Form of Agreement issued and updated from time to time by the Monitoring … |
| CPR-41 | 10.7 | 8 | As a minimum, where appropriate, all contracts shall include clauses setting out: |
| CPR-42 | 10.7.7 | 8 | Service Directors must ensure that a Data Protection Impact Assessment is completed for all contracts to inform such clauses. |
| CPR-44 | 11.2 | 9 | Where a contract is estimated to exceed £500,000, in value or amount and is for the execution of works (or for the supplies or services by a particular date or … |
| CPR-46 | 11.4 | 9 | If a performance bond is not considered to be necessary, the relevant Service Director must: 11.4.1 undertake a risk assessment in writing; and 11.4.2 seek … |
| CPR-47 | 11.5 | 9 | Every contract should be assessed for risk. If the risk assessment identifies the need for insurance the Service Director must: |
| CPR-50 | 11.11 | 10 | All contracts whether for goods, services, works or concession contracts the value of which is above Threshold shall be sealed. |
| CPR-52 | App A row 1 | 11 | up to relevant Threshold Relevant Service Director (or such officers as nominated by the Service Director in writing) shall have delegated authority to award … |
| CPR-53 | App A row 2 | 11 | Above the relevant threshold and less than £500,000 Relevant Service Director (following recommendation of the S151 officer and Monitoring Officer) shall have … |
| CPR-54 | App A row 3 | 11 | Above £500,000 and less than £2.5million The award of these contracts shall be a Key Decision delegated to the relevant Service Director in consultation with … |
| CPR-55 | App A row 4 | 11 | £2.5million or more Contracts with a value in excess of £2.5million shall require Executive approval, which may be given as below. |
| CPR-56 | App B row A | 12 | Above £1,000 and less than £25,000 At least one quote must be sought from an appropriate source. |
| CPR-57 | App B row B1 | 12 | Goods and Services: £25,000 or more and less than the Threshold Invitations to quote must be sent via the Procurement Portal to at least three appropriate … |
| CPR-58 | App B row B1 | 12 | Goods and Services: £25,000 or more and less than the Threshold Invitations to quote must be sent via the Procurement Portal to at least three appropriate … |
| CPR-59 | App B row B2 | 12 | Works, Concession contracts and Light Touch contracts: £25,000 or more and less than £500,000 Invitations to quote must be sent via the Procurement Portal to … |
| CPR-60 | App B row B2 | 12 | Works, Concession contracts and Light Touch contracts: £25,000 or more and less than £500,000 Invitations to quote must be sent via the Procurement Portal to … |
| CPR-63 | App B row D | 12 | Goods and Services Works, Concession contracts and Light Touch contracts: Above Threshold Procurement Legislation Procedures apply– full competitive tender … |
| CPR-64 | App B row D | 12 | Goods and Services Works, Concession contracts and Light Touch contracts: Above Threshold Procurement Legislation Procedures apply– full competitive tender … |
| CPR-65 | App C row A | 14 | The proposed contract is excluded under the Procurement Legislation. Prior written approval from the Monitoring Officer is required and where applicable prior … |
| CPR-66 | App C row B | 14 | Where the contract is governed by the Provider Selection Regime (PSR) Key decisions must be recorded and the relevant process under PSR followed |
| CPR-67 | App C row C | 14 | The proposed contract is being awarded under a Purchasing Scheme (refer to 8 above) of a type where no further competition is being undertaken a competition … |
| CPR-68 | App C row D | 14 | The proposed contract is an extension to an existing contract where the existing contract provides for such extension. Approval of the S151 Officer |
| CPR-69 | App C row E | 14 | For contract value below the Threshold prior written approval from the Monitoring Officer and S151 Officer is required. |
| CPR-70 | App C row E | 14 | For contract value greater than the Threshold, approval of the relevant board, following the submission of an extension report to the relevant board with … |
| CPR-71 | App C row F | 15 | Service Directors must ensure that a record of the reasons for the choice of provider is maintained on the individual’s case notes. |
| CPR-72 | App C closing | 15 | In the interests of clarity where an exemption is applied all contracts with an annual or total value of more than the Threshold must be approved by the … |

## Auditor decisions

| Risk | Rating | Decision | Auditor comment |
| --- | --- | --- | --- |
| R-01 | Likely (3) × Medium (3) = 9 High | approve | Evidence and caveats are sound; start with the £500,000-band windows. |
| R-02 | Likely (3) × Medium (3) = 9 High | approve |  |
| R-03 | Likely (3) × Medium (3) = 9 High | approve |  |
| R-05 | Likely (3) × Medium (3) = 9 High | approve |  |
| R-06 | Unlikely (2) × Major (4) = 8 High | approve |  |
| R-04 | Likely (3) × Minor (2) = 6 Moderate | approve |  |
| R-07 | Unlikely (2) × Medium (3) = 6 Moderate | approve |  |
| R-08 | Unlikely (2) × Medium (3) = 6 Moderate | approve |  |
| R-09 | Likely (3) × Minor (2) = 6 Moderate | override | Raise likelihood to 3: two split-purchase windows totalling £3.5m sit at the £500,000 Key Decision band, and that exact value falls in no Appendix A band. |
| R-10 | Unlikely (2) × Minor (2) = 4 Moderate | reject | Contract form and terms will be covered by a separate contract-management review. |
| R-11 | Unlikely (2) × Minor (2) = 4 Moderate | approve |  |
