# findings-analyst memory

How-to lessons only. Never evidence; the current PDFs are the only authority.

## 2026-10-10

- **Plain mode drops dashes at line ends inside table cells.** Where a range
  wraps inside a narrow cell (number, dash, line break, number), `pdftotext`
  plain text loses the dash; the `-layout` text keeps it. Read every range,
  and every label containing a dash, from layout, and compare with plain
  before recording it.
- **Wide five-column tables: quote the layout line run.** The cells of one row
  are interleaved line by line in layout. Slice the row's lines from the
  layout page in Python and collapse whitespace to get an exact quote, rather
  than retyping it. Plain text prints each cell contiguously (column by
  column), so use plain to check the wording of a reconstructed cell, never
  to pair cells.
- **Matrix figure:** in layout each matrix row is a line of band names, the
  row's axis label on the next lines, then a line of scores. Quote
  "bands + label + scores" as one run per row. Plain separates the axis
  labels from the cells and cannot be used for pairing.
- **A table cell can continue over a page break** (the last words land at the
  top of the next page). Cite two sources, one per page.
- **Printed-value rule in the verifier** works token by token on the item's
  own quotes: a lone dash, a range such as "N -M" and a "%" value all pass if
  the quote holds them exactly as printed. When a level/column name is only
  in the table heading, add the heading line as a second source on the item.
- **Workflow that passed first time:** build the JSON with a Python script in
  the scratchpad, write a draft there, run
  `scripts/verify_history.py --history <draft>`, then write
  `outputs/history.json` and run the verifier again with no arguments.
- **Page splitting:** `text.split("\f")` and drop a trailing empty page; a
  paged copy with `=====PAGE N=====` markers makes long papers readable.
- If launched as a general agent (agent file not loaded as a named type),
  this memory directory may not exist yet: create it.
