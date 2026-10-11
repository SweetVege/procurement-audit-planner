# QA review of the audit planning pack

Pack version: v2. Final check run: 2026-10-10 18:53:23. Register: Revision 2.

## Verdict: READY FOR SIGN-OFF

## Check results, as printed

```
PASS quotes: 0 item(s) | verifier: PASS: 0 errors, 2 warnings; 51 rules cited in the register, 51 excerpts compared

PASS numbers: 0 item(s) | 123 figures checked in 3 documents against 2,487 evidence values

PASS trace: 0 item(s) | 72 rules (58 cited, 22 listed as not tested); 10 risks in scope; 5 rated High or above; 6 challenges

PASS samples: 0 item(s) | 754 distinct transactions from 14 sample file(s) and 95 row IDs in audit-program.md, each traced to spend-clean.csv and the workbook

| Check | Result | Items | What was checked |
| --- | --- | --- | --- |
| quotes | PASS | 0 | verifier: PASS: 0 errors, 2 warnings; 51 rules cited in the register, 51 excerpts compared |
| numbers | PASS | 0 | 123 figures checked in 3 documents against 2,487 evidence values |
| trace | PASS | 0 | 72 rules (58 cited, 22 listed as not tested); 10 risks in scope; 5 rated High or above; 6 challenges |
| samples | PASS | 0 | 754 distinct transactions from 14 sample file(s) and 95 row IDs in audit-program.md, each traced to spend-clean.csv and the workbook |

VERDICT: ALL 4 CHECKS PASS
```

## Runs

| Pack version | Time | quotes | numbers | trace | samples | Items |
| --- | --- | --- | --- | --- | --- | --- |
| v1 | 2026-10-10 18:48:28 | PASS | PASS | FAIL (could not complete) | PASS | 1 |
| v1 | 2026-10-10 18:49:05 | PASS | PASS | FAIL | PASS | 1 |
| v2 | 2026-10-10 18:52:14 | PASS | PASS | FAIL | PASS | 6 |
| v2 (final) | 2026-10-10 18:53:23 | PASS | PASS | PASS | PASS | 0 |

The first v1 run stopped inside the trace check when `outputs/challenges.md` was not found, so it printed no result for the other parts of that check. The lead corrected `scripts/checks/check_trace.py` and the checks were run again on v1 (second row). The failed items in the first three runs were: `outputs/challenges.md not found` (both v1 runs) and `challenge #1 is still open` to `challenge #6 is still open` (v2).

## Challenges for the auditor

**Challenge 1 (rating, R-01).** The register rates the likelihood of R-01 at 3 because the pattern is present in one test, the split-purchase test. It sets the £1,000 band of both tests aside for a reason that applies to the split-purchase test only: with a £500 publication floor, nearly every pair of payments reaches £1,000. That reason does not bear on the clustering test, which compares single payments just under £1,000 with those just above it. At that band the clustering ratio is 1.4749, above one [metric:$.tests.threshold_clustering.per_threshold['1000.00'].band_to_comparator_ratio]; for general procurement, 86 payments sit just under £1,000 and 58 just above. £1,000 is the value above which the Rules require at least one quote [rule:CPR-56]. A price set just under a round figure is an ordinary explanation, so this is a reason to look and nothing more. Within the rating as it stands, the planner added control C-01.5 and test T-01.4, which examines 15 of the 86 payments for the quote the Rules require (verified in pack v2). **Decision asked:** whether clustering just under £1,000 counts as a second test bearing on R-01, which under the rubric's row for two or more different tests would raise the likelihood, or whether it is set aside, with the reason recorded.

**Challenge 5 (scope, R-01 and R-02).** Every data sample on competition is limited to items tagged general procurement. Items tagged agency staff are in no sample and no risk in the register counts them. The analysis shows two such items: one window of payments at the £500,000 band, worth £546,495.30 [metric:$.tests.split_purchases.per_threshold['500000.00'].by_tag.agency_staff.gbp], and one supplier at or above the publication value with no matching contract notice, paid £1,275,552.15 in the period [metric:$.tests.off_contract.unmatched_by_tag.agency_staff.gbp]. The reasons the register gives for setting placements aside are not stated for agency staff. A staffing framework called off under another buyer is an ordinary explanation. Within current scope, the planner now says in the memo's Approach that agency-staff-tagged items are in no sample and gives both figures (verified in pack v2). **Decision asked:** whether the agency-staff window at the £500,000 band is to be examined under R-01, and the agency-staff supplier with no matching notice under R-02, or whether both stay out of scope.

## What the checks do not cover

The checks prove the pack is consistent with its evidence. They do not judge whether the
ratings, the scope or the tests are the right ones; that is the auditor's decision, informed
by `challenges.md`.

## Auditor sign-off

| | |
| --- | --- |
| Decision (Approve the pack / Return it to the team) | Approve the pack (signed off) |
| Auditor | Yuming |
| Date | 2026-10-10 |
| Comments | Sign-off entered by the lead session on the auditor's instruction, against pack v2 and the final check run of 2026-10-10 18:53:23. No decision was given on challenges 1 and 5 above. |
