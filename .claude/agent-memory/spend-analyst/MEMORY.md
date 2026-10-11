# spend-analyst memory

How-to lessons only. No figures, findings or supplier names. Never evidence.
If an entry contradicts the current inputs, the inputs win: fix or delete it.

## Input formats

- **Spend header row and row_id** (2026-10-10). The header row is sheet row 1
  in some workbooks and sheet row 2 (after a blank row) in others. pandas with
  `header=None` keeps the blank leading row, so with the header at 0-based
  index `h`, Excel row = dataframe index + h + 2 after re-reading with
  `header=h`. Compute the sheet row before dropping blank rows. Confirm with
  openpyxl `ws[n]` in selfcheck.py.
- **Net amount dtype** (2026-10-10). It is `object` when read with
  `header=None` (header text in the column) and numeric once re-read with the
  right header. Test the dtype only after the second read.
- **Published Date has two ISO forms** (2026-10-10): with a `+01:00` offset
  and a shorter form ending in `Z`. Replace `Z` with `+00:00` before
  `datetime.fromisoformat`.
- **Notice supplier field** (2026-10-10). Splitting on `][` after stripping
  the outer brackets gave six pipe fields for every block; keep the hard stop
  if that ever fails rather than padding.

## Normalisation and matching

- **Trading-name variants in spend supplier names** (2026-10-10): `T/A`,
  `t/a:`, `T/AS`, `Trading as`, and `( T/A ...)` inside brackets, plus
  place qualifiers in brackets and unbalanced opening brackets. Remove
  bracketed text first, then the trading suffix. Where the legal name is an
  individual and the trading name is the business, the normalised name is the
  individual's, so such suppliers cannot match a notice by name.
- **Inter-authority regex needs `&` turned into `AND` first**, or
  `FIRE AND RESCUE` cannot match names written with an ampersand (2026-10-10).

## Tagging

- **Premises regex over-matches** (2026-10-10). `RENT|RATES|LEASE` also
  catches narratives about equipment rental and employee lease cars. The
  instructions fix the regex, so it was applied as written and the affected
  narratives reported. Check `narratives_by_tag` in cleaning-log.json each
  run and report again unless the instructions change.

## Thresholds from rules.json

- **Same boundary printed two ways** (2026-10-10). Merge an exclusive lower
  bound with an inclusive lower bound one penny above it; carry both rule ID
  sets and both printed forms.
- **Conflicting inclusivity on one value** (2026-10-10). Rules can disagree
  on whether an amount equal to the threshold is under or over it (rules.json
  `notes` records the gap). Take the lower bounds of the rules that start at
  the value, set `inclusivity_conflict`, and tell the auditor.
- **Publication floor** (2026-10-10) is the `record` rule whose
  `required_action` says to publish the expenditure. The lowest competition
  threshold can equal exactly twice that floor: the `low_information` test is
  "less than twice", so the tier is not marked even though every pair of
  visible payments crosses it. Report this each time.
- **Publication threshold** must be restricted to advertising rules whose
  clause starts `App B`; an advertising rule elsewhere carries a lower figure
  that is not a publication threshold (2026-10-10).

## Outputs

- **Keep analytics.json small** (2026-10-10). Split windows and duplicate
  groups can carry very long row_id lists. Cap the lists in top-20 rows, add
  `row_ids_total`, and leave the full list in the CSV.
- **Split-purchase de-duplication** keeps one window per supplier per
  threshold, so windows always equal distinct suppliers. Say so in the block.

## Running

- **Launched without the agent file** (2026-10-10): the memory directory did
  not exist and had to be created. Delete `scripts/__pycache__` after runs.
