---
name: risk-assessment
description: The method for rating procurement risks from outputs/rules.json, outputs/analytics.json and outputs/history.json into outputs/risk-register.md, and for revising the register after the auditor's decisions. Load this before writing or changing outputs/risk-ratings.json, rating a risk's likelihood or impact, or running build_register.py.
---

# risk-assessment

You write judgments to `outputs/risk-ratings.json`. `build_register.py` (next
to this file) turns them into `outputs/risk-register.md`. The split is strict:

| You | The builder |
| --- | --- |
| choose the risks, pick the rubric row and impact level, write the justifications, cite the evidence | resolves every citation, fills every figure, looks up the score, matrix label and band, drops what is unsupported, writes the register and the auditor's decision template |

You never type a number taken from the data, never multiply likelihood by
impact, never name a band, and never edit `risk-register.md`,
`auditor-comments.md` or `risk-register.state.json`. If the register is
wrong, fix `risk-ratings.json` and rebuild.

Everything you write describes **risk indicators to investigate**. Real
council, real suppliers: never state or imply that a rule was broken, that a
payment was improper, or that anyone acted wrongly. Do not name a supplier
in a title or description.

## 1. Read the inputs

Stop and report if any is missing. Never open the CSVs in
`outputs/analytics-full/`.

- `outputs/rules.json`: `rules[]` (each with `rule_id`, `clause`, `type`),
  `parameters` (named thresholds, value `null` until the auditor supplies
  them), `notes` (gaps and contradictions in the Rules).
- `outputs/analytics.json`: `population`, `thresholds`, `skipped`,
  `contracts`, `matching`, and `tests.<name>` for `threshold_clustering`,
  `split_purchases`, `high_value_suppliers`, `off_contract`, `duplicates`,
  `expired_notice_spend`, `spend_vs_award`. Tests keyed by threshold use
  `per_threshold['25000.00']`; `duplicates` uses `per_tier.<tier>`. Most
  tests carry `headline_general_procurement` and
  `placement_reported_separately`, a `caveat`, and `rule_ids`. Read the
  structure with a short Python snippet that prints keys and scalar values;
  do not print the `top20` lists in full.
- `outputs/history.json`: items with IDs: `AUD-` audits and opinions, `OPB-`
  how opinions are reached, `ACT-` agreed actions, `THM-` risk themes, `DIS-`
  discrepancies in the papers, and inside `scoring_method`: `LIK-`, `IMP-`
  scale levels, `BND-` bands, `APP-` appetite, `STG-` rating stages, plus
  `matrix`. `gaps` says what the papers do not contain.

## 2. Choose the risks

One risk per distinct way procurement could go wrong that the Rules address.
Work through, in this order, and merge duplicates:

1. every `anti-avoidance` rule;
2. every test in `analytics.json` that ran (one risk per test unless two
   tests bear on the same failure, then one risk citing both);
3. every test or tier in `skipped`: the risk still exists, the data cannot
   speak to it;
4. rule types with no test (`waiver`, `exclusion`, `approval`,
   `contract-form`, `record`): one risk per type where a prior audit, a
   risk theme or a note in rules.json bears on it. If nothing bears on it,
   leave it out.

Do not add a risk because it is common elsewhere. A risk with nothing to
cite does not survive the builder.

## 3. `outputs/risk-ratings.json`

```json
{
  "method": {
    "conflicts": [
      {"discrepancy": "DIS-00", "used": "which reading is applied", "not_used": "the other reading",
       "effect": "what difference the choice makes to the ratings, or that it makes none"}
    ]
  },
  "risks": [
    {
      "risk_id": "R-01",
      "title": "plain text, no figures, no citations",
      "description": "what could go wrong and which rule addresses it [rule:CPR-00]",
      "likelihood": {
        "score": 3,
        "rubric_row": "L3",
        "signals": ["$.tests.<test>...<count>"],
        "repeat_finding": null,
        "justification": "one or two sentences with [metric:$...] and {{$...}}"
      },
      "impact": {
        "score": 3,
        "category": "the column of the council's impact table you rated against",
        "justification": "one or two sentences citing [history:IMP-00]"
      },
      "evidence": ["one line per piece of evidence, each with its citation"],
      "proposed_focus": "what the audit should look at"
    }
  ],
  "revision": null
}
```

IDs run `R-01`, `R-02`, … and never change once the auditor has seen them.

### Citations and figures

| Write | Meaning | Resolves when |
| --- | --- | --- |
| `[rule:CPR-16]` | a rule | the `rule_id` is in rules.json |
| `[metric:$.tests.duplicates.per_tier.different_time.headline_general_procurement.groups]` | a named metric | the path exists in analytics.json |
| `[history:AUD-01]` | an item in history.json | the `id` exists |
| `{{$.tests.split_purchases.per_threshold['25000.00'].headline_general_procurement.gbp}}` | a figure, filled by the builder | the path resolves to a number or text |

- Paths start `$`, use `.key`, `['key with dots']` and `[0]`. Use single
  quotes inside brackets so the JSON needs no escaping.
- The builder formats figures: counts with thousands separators, money as £
  where the key says so. Force a format with `{{$.path|gbp}}`,
  `{{…|pct}}`, `{{…|int}}` or `{{…|raw}}`.
- **Every figure is a placeholder**: counts, £, ratios, percentages, the
  threshold itself, window lengths, dates, months covered. A number typed in
  prose draws a warning and must be replaced. Clause numbers, rule IDs and
  the 1–5 scores are not figures.
- Each likelihood justification and each impact justification needs at
  least one citation that resolves, or the risk is dropped.
- Carry the test's own caveat into the evidence in your words: "no notice
  found" is an indicator to check against the council's contract register;
  award values may be estimates; payments of the publication floor or less
  are invisible.

## 4. Likelihood rubric

The council's scale rates how probable it is that a risk occurs within
twelve months. Public data cannot measure that, so likelihood is read from
the strength of the evidence, by this ladder and nothing else. Two runs on
the same evidence must land on the same row.

| Row | Score | Use when | `signals` |
| --- | --- | --- | --- |
| L1 | 1 | a test bearing on the risk ran and found nothing | one or more paths, every one equal to zero |
| L2 | 2 | the public data cannot speak to the risk: no test exists, or the test or tier was skipped | empty; cite the rule, and the `skipped` entry or history item |
| L3 | 3 | the pattern is present in **one** test | one or more paths above zero, all under the same `$.tests.<name>` |
| L4 | 4 | the pattern is present in **two or more different** tests bearing on the same risk | paths above zero from at least two different `$.tests.<name>` |

Rules for signals:

- A signal is the path to a **count** (windows, groups, suppliers, payments).
- Where a test splits by tag, use the `headline_general_procurement` count.
  A pattern present only under the placement, grant, agency or premises tags
  is L2, with the metric cited in the justification and the reason stated
  (periodic care fees recur; Appendix C excludes individual placements from
  competition).
- Do not use a tier marked `low_information`, or the £1,000 tier of
  `split_purchases` or `threshold_clustering`, as a signal: with a £500
  publication floor nearly every pair of payments crosses it.
- `threshold_clustering` is a signal only where the band count is above the
  comparator count (`band_to_comparator_ratio` above one); otherwise cite it
  as evidence against clustering and use L1 for a clustering-only risk.
- Every signal must also appear in the justification as `[metric:…]`,
  written exactly the same way.

**Repeat finding (+1).** If history.json records an audit of the same
subject with an adverse opinion (Limited, Weak, Unsatisfactory or No
assurance, in either opinion column), add one point, to a maximum of 5:
set `"repeat_finding": {"audit": "AUD-00"}`, cite `[history:AUD-00]` in the
justification and say in words that one point was added and why the audit
is the same subject. "Same subject" means the audit title covers the
activity the risk is about. An adverse opinion on an unrelated area, or a
Reasonable or Substantial opinion, never raises a score; cite a positive
opinion on the same subject as context in `evidence` instead. Score 5 is
reached only this way, or by the auditor.

`score` must equal the row's score plus the uplift. The builder checks the
row against the signals and the score against the row.

## 5. Impact

Rate the effect **if the risk happened**, against one column of the
council's impact table in history.json (`IMP-` items; each has `criteria`
by column). Choose the column that fits the risk, name it in `category`,
pick the level whose printed criteria fit, and cite that level's
`[history:IMP-00]`. The builder rejects an impact whose score does not
match the level cited.

- Procurement-rule risks usually sit in the compliance or reputation
  columns. Use the financial column only when analytics.json has a figure
  that stands for money that could be lost (for example `gbp_beyond_first`
  for duplicates), cite it by placeholder, and say that it is an upper
  indicator, not a loss.
- Spend that merely has no notice, or annualised estimates, are not losses.
- Where the printed criteria are ambiguous (history.json `gaps` and
  `discrepancies` say where), do not interpret them: use another column.
- Do not rate impact by appetite; cite an `APP-` item only as context.

**Fallback.** If `scoring_method.usable` is false, rate likelihood by the
same rubric and impact 1–5 (Very low … Very high) with a rule, metric or
history citation; the builder states the fallback in the register header.

## 6. Conflicts in the scoring method

The papers contradict themselves in places. Never pick a reading silently.

- The builder handles two kinds itself and reports them in the header: a
  scale level that disagrees with the matrix axis (the axis is used, the
  item is marked and cannot be cited), and a matrix cell label that differs
  from the band table's name (both are shown).
- **You** declare every other discrepancy in history.json that touches a
  scale, the matrix, a band or an escalation score, in `method.conflicts`:
  the `DIS-` id, the reading used, the reading not used, and the effect on
  the ratings. Prefer the reading printed in the matrix or its table over
  one printed only in running text, and say so. Discrepancies that are
  wording only (names of committees, cross-references) need no entry.

## 7. Build

```bash
.venv/bin/python .claude/skills/risk-assessment/build_register.py
```

Read every line it prints.

- `DROPPED`: the risk is out of the register. Fix the cause (add the
  citation the evidence supports, correct the path, re-read the rubric) and
  rebuild. If the evidence does not exist, delete the risk; never invent a
  citation to keep it.
- `WARNING`: fix every typed figure and every word flagged as not indicator
  language, then rebuild. A warning you believe is a false alarm (a year in
  a document title, a quoted phrase) may stay; say so in your report.
- `FAIL` / `FAILED`: nothing was written. See section 8.

The first build is a **Draft**. It writes `risk-register.md`,
`auditor-comments.md` (one row per rated risk, blank Decision and Comment)
and `risk-register.state.json` (the builder's record of the draft the
auditor is deciding on). Then stop: the auditor decides.

## 8. Revising after the auditor's decisions

When you are re-run after the auditor has filled in `auditor-comments.md`,
read it first. For each risk:

| Decision | You |
| --- | --- |
| `approve` | change nothing in that risk |
| `reject` | change nothing; leave the risk in the file. The builder marks it rejected |
| `revise` | do what the comment says and nothing more. A re-rating still follows the rubric |
| `override` | set the score(s) the auditor gave, add `"auditor_override": true` to that `likelihood` or `impact`, and leave your justification as the record of the evidence. The rubric no longer binds that score |
| blank | change nothing; the builder reports it as undecided |

Then set the `revision` block:

```json
"revision": {
  "number": 1,
  "changes": [{"risk_id": "R-02", "summary": "what you changed, in one sentence"}],
  "added": []
}
```

- One `changes` entry for every `revise` and `override`, and for no other
  risk. Increase `number` on each later revision.
- Add a risk only if "General comments" asks for one; list its id in
  `added`.
- If a comment is unclear, or asks for something the evidence cannot
  support (a rating with no citation, a figure not in analytics.json), do
  not guess: leave the risk unchanged, and report the comment and why it
  could not be applied. The build will fail on that risk until the auditor
  clarifies; that is the intended outcome.

Rebuild. The builder compares every risk with the draft the auditor saw and
fails, writing nothing, if a `revise` or `override` was not applied, if a
risk changed without being asked, or if a risk appeared or disappeared. On
success the register is headed **Revision N**, lists what changed, and marks
each override.

## 9. Report

Under 300 words, quoting the register, not your memory: draft or revision
number; risks rated, each with its rating as printed in the Summary table;
risks dropped and why; warnings left and why; the scoring-method conflicts
in the header; what could not be rated because a parameter is null or a
test was skipped; and what the auditor needs to do next (decide every risk
in `auditor-comments.md`, or clarify a comment).
