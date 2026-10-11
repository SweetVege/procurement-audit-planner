---
name: extract-rules
description: Convert the council's Contract Rules PDF (data/contract-rules.pdf) into outputs/rules.json, one entry per testable rule with clause, page, thresholds as printed and a verbatim quote, then verify it. Use when the auditor runs /extract-rules or asks to extract, rebuild or re-verify the procurement rules.
---

# extract-rules

Turn `data/contract-rules.pdf` into `outputs/rules.json`, then prove it with
`verify_quotes.py`. You read and judge; you never supply a figure, a clause
number or a wording the PDF does not print.

## 1. Before you start

Run from the project root. Stop and report, writing nothing, if:

- `data/contract-rules.pdf` is missing, or
- `pdftotext` / `pdfinfo` are not on PATH, or
- either extraction below comes back empty (a scanned PDF has no text layer).

`data/` is read-only. Write extracted text to your scratchpad, not the project.

```bash
pdfinfo data/contract-rules.pdf                      # page count goes in source.pages
pdftotext data/contract-rules.pdf <scratch>/plain.txt
pdftotext -layout data/contract-rules.pdf <scratch>/layout.txt
```

Read both files in full. Pages are separated by a form feed; page N is the Nth
chunk, and it matches the number printed in the page footer.

## 2. How this document is built

The September 2025 edition is 15 pages: numbered sections 1–11, then three
appendix tables. If the PDF in `data/` is laid out differently (new sections,
new appendices, different row labels), follow the PDF and say so in your report.

- **Numbered clauses** run `N.M`, with sub-clauses `N.M.K` and occasionally
  `N.M.K.J`. Unnumbered sub-headings ("Advertising", "Sealing") and bullet lists
  belong to the clause above them.
- **Appendix A**: delegated authority to award, by Total Contract Value band.
  Rows have no labels; number them 1, 2, 3… from the top.
- **Appendix B**: value band → award procedure → advertising requirement.
  Rows are labelled (A, B1, B2, C, D). Footnotes `*` to `****` sit on the next page.
- **Appendix C**: circumstances where competition is excluded → the written
  record and approval needed. Rows are labelled A–F, with an intro sentence
  above the table and a closing paragraph below it.
- **Named thresholds**: the document says "the Threshold" / "the relevant
  Threshold" and tells the reader the figures are published on an intranet
  page. Those figures are not in the PDF.

The two extractions are good at different things:

| | plain | `-layout` |
| --- | --- | --- |
| Body clauses | number on its own line, text below | number and text on one line: use this to see which text belongs to which clause |
| Tables | one cell at a time, left to right along each row: **copy table quotes from here** | cells from different columns interleaved on one line: use only to see which cells share a row |

Other things that will trip you up:

- A clause or table row can run across a page break (the footer and a form feed
  land in the middle). A quote must sit entirely on one page: quote the part on
  one side of the break and give that page.
- Bullets come out as a private-use glyph. Do not paste it into a quote; the
  verifier ignores it and ignores line breaks and spacing. Nothing else is
  forgiven: keep curly quotes, dashes, `£`, capitals and the PDF's own typos.
- A word hyphenated at a line end in a table cell can lose its hyphen in plain
  mode. Quote around it.

## 3. What goes where

Walk the document top to bottom. Every numbered clause, every appendix row,
every footnote, and each appendix intro or closing paragraph ends up in exactly
one of `rules` or `excluded`.

**A rule is testable** when an auditor could look at a contract, a payment or a
file and say pass or fail: it sets a value band, a required action, or who must
approve. One entry per test:

- A table row that sets both a procedure and an advertising requirement is two
  rules (same clause, different `type`).
- A clause whose sub-clauses set different bands or approvers is one rule per
  sub-clause; the lead-in needs no entry of its own.
- A clause whose sub-clauses are one list (the contents every contract must
  have) is one rule at the parent clause.

**Excluded**, with a one-line reason: definitions, purpose and background,
statements of who interprets the Rules, pointers to other documents, permissions
("may"), advice ("should consider", "advice should be sought"), headings that
carry a clause number, and anything too vague or ambiguous to test. If you are
unsure whether a clause is testable, exclude it and say why; never guess a
threshold, action or approver to make it fit.

A sub-clause is covered by an entry for its parent, and a lead-in is covered by
entries for its sub-clauses. Appendix rows are not: give each row, footnote,
intro and closing paragraph its own entry.

## 4. Output: `outputs/rules.json`

One JSON object, UTF-8, these five keys and no others:

```json
{
  "source": { "file": "data/contract-rules.pdf", "pages": 15 },
  "parameters": {
    "THRESHOLD_EXAMPLE": {
      "value": null,
      "defined_in": "1.4",
      "page": 1,
      "description": "what the threshold is and where the PDF says it is published",
      "verbatim_quote": "the sentence that names it"
    }
  },
  "rules": [
    {
      "rule_id": "CPR-01",
      "clause": "App B row B1",
      "page": 12,
      "type": "procedure",
      "scope": ["goods", "services"],
      "condition": "short plain-English statement of when the rule applies",
      "threshold_low": 25000,
      "threshold_low_inclusive": true,
      "threshold_low_param": null,
      "threshold_high": null,
      "threshold_high_inclusive": false,
      "threshold_high_param": "THRESHOLD_EXAMPLE",
      "threshold_text": "the value band exactly as printed",
      "required_action": "what must be done",
      "approver": null,
      "evidence_source": ["contract_notices", "council_records"],
      "verbatim_quote": "exact text from that page"
    }
  ],
  "excluded": [
    { "clause": "2.1", "page": 2, "reason": "one line saying why it is not testable" }
  ],
  "notes": [
    { "kind": "contradiction", "clauses": ["6.15", "App B intro"], "description": "what conflicts, in one or two sentences" }
  ]
}
```

The example shows the shape only. Take every value from the PDF.

### Rule fields (all seventeen required; use `null`, never omit)

| Field | Rule |
| --- | --- |
| `rule_id` | `CPR-01`, `CPR-02`, … in document order, no gaps |
| `clause` | `6.16`, `7.4.2`, `App A row 2`, `App B row B1`, `App B note ***`, `App C intro`, `App C closing` |
| `page` | PDF page the quote is on |
| `type` | `procedure` (value band → quotes/tender), `advertising`, `approval` (who may award or decide), `waiver` (exceptions to competition), `exclusion` (Appendix C), `anti-avoidance` (the no-splitting / aggregation rule), `valuation` (how contract value is calculated), `record` (reports, registers, retention), `contract-form` (writing, clauses, bonds, insurance, sealing) |
| `scope` | `["all"]`, or any of `goods`, `services`, `works`, `concession`, `light_touch` exactly as the clause or row limits it |
| `condition` | when the rule applies, in your words |
| `threshold_low`, `threshold_high` | GBP integer as printed (`£2.5million` → `2500000`); `null` if that side is open or is a named threshold. Use pounds and pence (`24999.99`) only where the PDF prints pence |
| `threshold_low_inclusive`, `threshold_high_inclusive` | `true` / `false` whenever that bound is set, else `null`. "or more", "up to", "not exceeding" are inclusive; "above", "over", "exceeds", "more than", "less than", "below" are exclusive |
| `threshold_low_param`, `threshold_high_param` | name of a `parameters` entry when the bound is a named threshold, else `null`. A bound has an amount or a parameter, never both |
| `threshold_text` | the band as printed; `null` when the rule has no bound |
| `required_action` | what must be done, close to the PDF's wording |
| `approver` | the role as the PDF names it; `null` if none |
| `evidence_source` | where an auditor would test it, one or more of `spend_data` (the published payments), `contract_notices` (Contracts Finder export), `council_records` (files the council must be asked for) |
| `verbatim_quote` | copied character for character from one page, at least a full sentence or a full table row, and long enough to contain every amount in the threshold fields |

Record bounds as printed. Do not tidy them: if the PDF says "more than
£24,999.99", write `24999.99` exclusive, not `25000` inclusive. If two bands
leave a value uncovered or cover it twice, record both as printed and add a note.

### Parameters

One entry for each threshold the PDF names without printing, split by contract
category wherever the PDF says the figure differs by category. Names are
`UPPER_SNAKE_CASE`. `value` is always `null`: do not fill it in from memory,
from the legislation or from the web, however sure you are. The auditor
supplies the figures.

### Notes

Record what an auditor needs to know about the drafting, without resolving it:

- `contradiction`: two places say different things (a band defined one way in a
  clause and another way in a table; "or more" and "in excess of" for the same
  figure).
- `gap`: a value or case no rule covers (a figure that falls between two bands;
  no procedure below the lowest band).
- `drafting`: a placeholder left blank, a cross-reference that points at the
  wrong clause, a garbled sentence, a heading that carries a clause number,
  a count that disagrees with a list.

Cite every clause involved. State the indicator, not a conclusion about the
council.

## 5. Verify

```bash
.venv/bin/python .claude/skills/extract-rules/verify_quotes.py
```

It checks the schema, the rule ID sequence, that every parameter used is
declared and null, that every quote is on its stated page, that every amount is
printed in its rule's quote, and that every numbered clause and every appendix
in the PDF is placed. It cannot see individual appendix rows or footnotes:
check those yourself against the layout text before you report.

Fix every error by going back to the PDF, never by loosening a quote until it
matches or by editing the verifier. Re-run until it prints `PASS`. If you
cannot reach `PASS`, leave the file in place and report the remaining errors.

## 6. Report

In under 200 words: the verifier's last line; counts of rules by type, excluded
clauses, parameters and notes; the parameters the auditor must supply; the
notes, most serious first; anything about the PDF that differed from section 2.
