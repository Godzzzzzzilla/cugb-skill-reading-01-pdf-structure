# Limits and what is reported instead

| condition | detection | what the result says |
|---|---|---|
| no text layer (scan) | every backend returns zero words | `status: cannot_determine`, `uncertainty` names OCR |
| encrypted PDF | backend raises | `status: partial`, exception text in `uncertainty`, `audit` marks `pdf-opened` false |
| gutter narrower than 3% of page width | no admissible vertical cut | one block holds both columns; `audit.multi-column-handled` false |
| rule-drawn column separator | a line, not whitespace, crosses the cut | same as above |
| table continued across pages | two tables, adjacent pages | reported separately; cite both halves |
| formula stored as an image | block text empty on that line region | missing block, listed under `uncertainty` |
| rotated page | text runs vertically | read as upright; order wrong for that page only |
| producer wrote row-major | baseline window recall collapses | repaired by the XY-cut pass; `bench.py` measures it |
| font carries no Unicode mapping | backends return `?` or conjoining garbage | `audit.block-offsets-exact` still passes (the text is what it is); the garbling is visible in `report.md` |

The rule behind the table: **degrade a field, never the case.** A missing table
is `tables: []` plus an uncertainty entry, not a rejected run.
