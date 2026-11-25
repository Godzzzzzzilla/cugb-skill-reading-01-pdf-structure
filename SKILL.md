---
name: pdf-structure
description: Recover reading order, section hierarchy, table cells, equation numbers and a character range for every block of a research PDF, including two-column layouts and files whose glyphs are stored row-major (interleaved). Use when a task asks to parse a PDF, quote it, locate a claim, or check whether extracted text follows the printed page.
---

# PDF structure extraction

A PDF's text layer stores glyphs in the order the producer wrote them, which is
often not the order a reader reads them. This skill turns a PDF into blocks in
reading order, gives every block a character range into an emitted page file,
and reports what it could not recover instead of guessing.

## When to use

- a task hands you a PDF and asks for its text, sections, tables or figures;
- an answer must cite a page, a paragraph or a table cell of a PDF;
- extracted text looks interleaved ("the last line of the left column runs into
  the first line of the right column") and you need it repaired;
- you need to know whether a PDF is a scan with no text layer.

Do not use it to understand figures, to OCR a scan, or to judge scientific
correctness — it reports structure, not meaning.

## One command

**Where to run it.** The scripts resolve their own paths, so they work from
any working directory. If your shell starts in `/app/work` (the contract's work
directory), call the absolute path of the script —
`python3 /skills/weekly-skill/scripts/run.py --input /input/case.json --output /app/output`
— or `cd` into the folder holding this `SKILL.md` first and use the relative form
below.

```bash
python3 scripts/run.py --input /input/case.json --output /app/output
```

Defaults are exactly those paths, so `python3 scripts/run.py` also works.
The process exits 0 for every case it can read, including a partial one.

## What it writes

| file | what it is |
|---|---|
| `pages/pNNNN.txt` | page text in reading order, blocks separated by a blank line. **This file is the anchor substrate**: every character range in the result indexes into it. |
| `document.json` | pages, blocks (with `char_start`/`char_end`/`bbox`), sections, captions, equations, tables, reading order |
| `structured.md` | the same content as markdown, headings promoted from detected levels |
| `evidence.jsonl` | one line per anchored claim: `{id, claim, anchor{source, char_start, char_end, quote}, verified}` |
| `result.json` | the case deliverable: status, result payload, evidence, uncertainty, limits, audit, artifacts, declared-contract echo |
| `audit.json` | every named check with pass/fail and a weight |
| `report.md` | human summary with the evidence table |

## The anchor contract

A claim is only as good as its locator. For a claim you want to make about the
document:

1. find the block in `document.json` that contains the words;
2. copy its `source`, `char_start`, `char_end`;
3. quote `pages/…txt[char_start:char_end]` verbatim.

Anyone can then re-slice the file and compare. `scripts/verify.py` does exactly
that for every recorded anchor and exits non-zero if one no longer matches:

```bash
python3 scripts/verify.py --result /app/output/result.json
```

If you write your own claims into `result.json`, add them in the same shape and
run `verify.py` again before you hand the case in. A claim without a range is
marked `verified: false` and reported under `uncertainty` — that is the honest
outcome, not a failure.

## Decision rules

| situation | what the skill does | what you should do |
|---|---|---|
| no `pdftotext`, no `pdfminer` | falls back to `pypdf`, then to a raw stream reader; records `pdf_backend` | check `result.run.pdf_backend`; if it is `raw-stream`, order is approximate — say so |
| page has no glyphs (scan) | status `cannot_determine`, names OCR as the fix | do not paste an imagined transcription; report the scan |
| columns separated by a rule, not whitespace | cut test fails; blocks stay merged | report the merged block and the reason; do not split by eye |
| table spans a page break | each half is reported separately | say "continued on p.N" and cite both halves |
| PDF is encrypted | backend raises; caught; status `partial` with the exception text | report it; do not attempt to decrypt |
| case.json names no file | file discovery under the input directory | if still empty, status `cannot_determine` |

## Reading the result

`result.result.document` is the whole structure. The three fields most tasks
need:

- `sections[]` — `{title, level, page, char_start, char_end, evidence}` where
  `evidence` says whether the heading was found by font size, by numbering or
  by keyword;
- `blocks[]` — `{block_id, page, source, char_start, char_end, text, bbox}` in
  reading order; `reading_order` is the list of `block_id` in that order;
- `tables[]` — `{page, rows, n_rows, n_cols, bbox}` with cells reconstructed by
  recurring column starts, so a cell that nearly fills its column is still
  assigned correctly.

## Limits

- Text is recovered, not interpreted: captions are recognised by their leading
  label, not by understanding the figure.
- Superscripts and subscripts survive as characters only if the producer stored
  them as characters; a formula that is an image is reported as a missing block.
- A two-column page whose gutter is narrower than 3% of the page width will not
  be split. The failure is visible: one block holds both columns.
- Rotated pages are read as if upright.
