---
name: audit-program
description: The method for turning the auditor-approved risks into the audit planning pack (planning memo, risk and control matrix, audit program with targeted samples and a PBC list) by writing outputs/audit-plan.json and running build_pack.py. Load this before writing or changing audit-plan.json, designing a control, test step or sample, or running the gate check or the pack builder.
---

# audit-program

You write judgments to `outputs/audit-plan.json`. `build_pack.py` (next to
this file) turns them into the pack.

| You | The builder |
| --- | --- |
| state the expected control for each approved risk and the rule it comes from; write the test steps; say which flagged items to pull and in what order; say what to ask the council for; write the memo's prose | decides the scope from the auditor's decisions; resolves every citation; fills every figure; draws every sample and checks each transaction exists; checks the chain risk → control → test and the coverage of every rule; renders the three documents; records every figure in `pack-figures.json` |

You never type a number taken from the data, never pick transactions by
hand, never edit a file the builder writes (`planning-memo.md`,
`risk-control-matrix.md`, `audit-program.md`, `samples/`,
`pack-figures.json`), and never change `risk-ratings.json`,
`auditor-comments.md` or the register. If the pack is wrong, fix
`audit-plan.json` and rebuild.

Everything you write plans work on **risk indicators to investigate**. A
flag is a reason to look at a record, never a conclusion. Do not name a
supplier anywhere in `audit-plan.json`; supplier names appear only in the
sample files, which are working papers. Write test steps as "obtain …,
confirm whether …", never "identify the breach" or "prove".

## 1. Gate first

```bash
.venv/bin/python .claude/skills/audit-program/build_pack.py --gate
```

`GATE CLOSED` lists the risks in scope and the risks the auditor rejected.
If it prints `GATE OPEN` / `BLOCKED`, stop and report the reasons: a risk
is undecided, the register is not yet a revision, or a decision changed
after the register was built. You cannot close the gate; the auditor and
the risk-assessor do.

Scope is exactly what the gate prints. Plan every risk in scope and no
other. A rejected risk gets no control, test or sample; the builder lists
it as out of scope with the auditor's comment. Read each in-scope risk in
`outputs/risk-register.md` (its evidence, proposed focus and the auditor's
comment, which may direct where to start) before planning it. For a risk
the auditor overrode, plan to the auditor's rating and reason.

## 2. `outputs/audit-plan.json`

```json
{
  "memo": {
    "objective": "…", "scope": "…", "approach": "…", "limitations": "…"
  },
  "risks": [
    {
      "risk_id": "R-01",
      "controls": [
        {"control_id": "C-01.1", "control": "what the Rules expect to be in place", "rules": ["CPR-00"]}
      ],
      "tests": [
        {
          "test_id": "T-01.1",
          "controls": ["C-01.1"],
          "step": "what the auditor does, citing [rule:CPR-00] or [metric:$.path]",
          "sample": {
            "file": "split-purchases.csv",
            "filter": [{"column": "threshold", "op": "==", "value": 25000.0}],
            "sort": [{"column": "total_gbp", "order": "desc"}],
            "size": "by_score",
            "keep": ["window_start", "window_end", "total_gbp"]
          },
          "no_sample_reason": null,
          "pbc": ["P-01"]
        }
      ]
    }
  ],
  "pbc": [{"pbc_id": "P-01", "request": "what the council is asked to provide"}],
  "rules_not_tested": [{"rule_ids": ["CPR-00"], "reason": "why no approved risk covers these rules"}]
}
```

IDs: controls `C-<risk number>.<n>`, tests `T-<risk number>.<n>` (so R-03
has `C-03.1`, `T-03.1`), requests `P-01`, `P-02`, ….

### Citations and figures

Same syntax as the risk register: `[rule:CPR-16]`,
`[metric:$.tests.<test>…]`, `[history:AUD-01]`, and `{{$.path}}` for any
figure from analytics.json, with paths written `$.a.b['key.with.dots'][0]`.
In the memo only, these counts the builder computes are also available:
`{{pack.risks_in_scope}}`, `{{pack.risks_rejected}}`,
`{{pack.risks_in_register}}`, `{{pack.controls}}`, `{{pack.tests}}`,
`{{pack.tests_with_sample}}`, `{{pack.sample_items}}`,
`{{pack.sample_transactions}}`, `{{pack.sample_gbp}}`,
`{{pack.pbc_items}}`, `{{pack.rules_total}}`, `{{pack.rules_cited}}`,
`{{pack.rules_not_tested}}`.

Every figure is a placeholder: counts, £, thresholds, dates, months, sample
sizes. A citation or placeholder that does not resolve fails the build. A
number typed in prose draws a warning. Clause numbers and IDs are not
figures.

## 3. Expected controls

A control is what the Rules require to be in place, stated so that it
either exists or does not: "three invitations to quote are issued through
the Procurement Portal for …", "the S151 Officer approves the extension
before …". One control per distinct requirement; two to four per risk is
typical.

- `rules` lists the `rule_id`s the control comes from: at least one. Take
  the requirement from that rule's `required_action` and `approver` in
  rules.json; do not import a control from general audit practice. If no
  rule requires it, it is not an expected control here.
- Where a rule's threshold is a named parameter with a null value, say in
  the control that the figure is to be confirmed with the council, and add
  a PBC item for it. Never supply the figure.
- Where rules.json `notes` records a gap or contradiction that affects the
  control (a value that falls in no band; VAT included in one place and
  excluded in another), say so in the control or the test, citing the rules
  involved, and plan a step that establishes which reading the council
  applies.

## 4. Test steps

Each test says what the auditor obtains, what it is compared with, and what
is recorded: one action per test.

- `controls`: the control(s) of the same risk the test covers. Every
  control needs at least one test.
- `step` cites at least one rule or one metric. Cite the rule the evidence
  is compared with, and the metric that produced the items being pulled.
- Carry the test's caveat into the step: for a "no notice found" item the
  first step is to look the supplier up in the council's contract register;
  for an award-value comparison, to confirm what the award value
  represents; for repeated payments, to confirm whether each was separately
  due.
- Keep placements separate. Where a risk's signal comes from general
  procurement, filter the sample to that tag. Plan placement-tagged items
  only under a risk that is about them, against the Appendix C rule.
- A risk with no data signal (rubric L2 in the register) still needs tests:
  walkthroughs and document tests on a selection the auditor draws in the
  field from a list the council provides. Set `"sample": null`, give
  `no_sample_reason` (what the selection will be drawn from and why the
  data cannot supply it), and add the PBC item for that list.

## 5. Sample recipes

You describe the selection; the builder draws it. A recipe is a file, a
filter, an order and a size rule. Read only the header and first rows of a
file (`head -3`) to learn its columns; never print or load a full list.

| File in `outputs/analytics-full/` | One row is | Transactions come from |
| --- | --- | --- |
| `split-purchases.csv` | a supplier window (`threshold`, `window_start`, `window_end`, `n_payments`, `total_gbp`, `tag`) | `row_ids` |
| `duplicate-groups.csv` | a group of same-amount payments (`tier`, `amount`, `n_rows`, `gbp_beyond_first`, `tag`) | `row_ids` |
| `threshold-clustering.csv` | a payment just under a threshold (`threshold`, `Net amount`, `tag`) | `row_id` |
| `high-value-suppliers.csv` | a supplier at or above the publication value (`annualised_estimate`, `total_gbp`, `dominant_tag`, `match_class`) | `largest_payment_row_ids`, or all the supplier's payments |
| `expired-notice-spend.csv` | a supplier whose matching notices have ended (`latest_end_date`, `notice_id`, `annualised_estimate`) | `largest_payment_row_ids`, or all the supplier's payments |
| `spend-vs-award.csv` | a supplier compared with its award (`ratio`, `flag`, `awarded_value`, `notice_id`) | `largest_payment_row_ids`, or all the supplier's payments |
| `near-matches.csv`, `supplier-match.csv` | a supplier and its name-match class | none: not a sample source (use as a lookup in the step) |
| `duplicates.csv` | one payment inside a duplicate group | `row_id` (prefer `duplicate-groups.csv`) |

Do not sample from `spend-clean.csv`, `spend-excluded.csv` or
`notices-clean.csv`: a sample is drawn from flagged items.

Recipe fields:

- `file`: one of the files above.
- `filter`: a list of `{column, op, value}`; `op` is one of `==`, `!=`,
  `>=`, `<=`, `>`, `<`, `in`, `contains`. All conditions must hold. Take a
  threshold value from analytics.json (`$.thresholds`); the builder compares
  numbers as numbers. Typical filters: the threshold tier, `tag` (or
  `dominant_tag`) `==` `general_procurement`, `tier` `==` `different_time`,
  `match_class` `!=` `exact`, `flag` `==` `true`.
- `sort`: a list of `{column, order}` with `order` `asc` or `desc`. Required.
  Order by what makes an item matter most for the risk (largest total,
  highest ratio, most payments), then add a second key that is unique
  (`supplier_norm`, `group_id`, `row_id`) so ties always break the same way.
- `size`: `"by_score"`: the builder takes the first items in that order, up
  to the number set for the risk's score (it prints the table in the memo);
  a smaller population is taken whole. `"all"`: every item, allowed only
  for a small population (the builder states the limit). Use `"all"` where
  the auditor's comment asks for a whole band, or the flagged set is a
  handful.
- `transactions`: `"listed"` (default) pulls the payments listed against
  each item; `"supplier_all"` pulls every payment to that supplier in the
  period. `per_item_limit` keeps the largest N payments per item; use it
  with `supplier_all` for suppliers paid many times.
- `keep`: columns of the item to copy into the sample file so the auditor
  can see why the item was flagged (window dates, totals, ratio, notice id).

The builder fails if the filter leaves nothing, if any sampled transaction
is not in `spend-clean.csv`, or if `"all"` exceeds the limit. Samples are
targeted, not statistical: never write that a result will be projected to
the population.

## 6. PBC list

One entry per thing the council must provide, worded as a request a
finance or procurement officer could act on: the document, the population
or period, and the form ("contract register extract showing supplier,
start, end and value for …"). Requests refer to "the suppliers and
transactions in the sample file", not to names. Every test lists the
entries it needs, at least one; every entry must be needed by a test.
Always include: the contract register; the figures for any null threshold
parameter a test depends on; and, for each no-sample test, the list the
selection will be drawn from.

## 7. Every rule accounted for

Each rule in rules.json must be cited by an in-scope risk (in the
register), by a control, or by a test step, or be listed in
`rules_not_tested` with a reason. Group rules that share a reason. Good
reasons are specific: "covered by the risk the auditor rejected (R-10);
contract form is to be reviewed separately", "sealing and legal-proceedings
signature: no approved risk concerns execution of documents". "Not
relevant" is not a reason. A rule cannot be both cited and listed. Do not
cite a rule in a control just to account for it; if no approved risk covers
it, list it.

## 8. Memo

Four short sections, plain prose, every figure a placeholder:

- `objective`: what the audit will give assurance on, tied to the Rules.
- `scope`: the period and population analysed, what is in and what the data
  excluded (redacted payees, statutory and inter-authority payments), and
  that scope follows the auditor's decisions.
- `approach`: how flagged items become tests: reconcile to the council's
  records first, then document tests; how placements, grants and named
  thresholds are handled.
- `limitations`: what public data cannot show (the publication floor, a
  three-month window annualised, notices are not a contract register, null
  threshold parameters, no findings behind prior audits).

The builder adds the scope table, the rejected risks, the sample table and
totals, and the rule-coverage counts. Do not repeat them in your prose.

## 9. Build

```bash
.venv/bin/python .claude/skills/audit-program/build_pack.py
```

- `FAIL` / `FAILED`: nothing was written. Fix `audit-plan.json` and rebuild.
  Fix a failed citation by citing what the evidence supports, a failed
  sample by correcting the recipe against the file's real columns, an
  unaccounted rule by covering it or listing it with a true reason. Never
  weaken a test to make the build pass.
- `WARNING`: replace typed figures with placeholders and reword anything
  flagged as not indicator language, then rebuild.
- `PACK BUILT`: read the three documents once. Check each test's sample
  line (population, items, transactions) is what you intended, that no
  sentence reads as a finding, and that no supplier is named outside
  `samples/`.

## 10. Report

Under 300 words, quoting the pack: the builder's last line; risks in scope
and rejected, as the gate printed them; controls, tests and sample files
with the totals from the memo; tests with no data sample and why; rules
listed as not tested, grouped by reason; warnings left and why; and
anything in the inputs you believe is wrong, by path or ID.
