# result.json — field by field

Top level, always present even when the case fails:

| field | type | meaning |
|---|---|---|
| `schema` | string | `arm-skill-result/1.1` |
| `skill` | object | `{name, version, armkit}` — which code produced this |
| `case_id` | string | from `case.json` (`case_id`/`id`/`task_id`, else the directory name) |
| `status` | enum | `success` \| `partial` \| `cannot_determine` — derived from the audit, never asserted |
| `status_reason` | string | one sentence naming what decided the status |
| `result` | object | the payload; for this skill: `document`, `page_count`, `block_count`, `section_count`, `table_count`, `caption_count`, `equation_count`, `markdown` |
| `evidence` | array | `{id, claim, anchor{source, char_start, char_end, quote, page, block_id}, verified}` |
| `uncertainty` | array | `{item, why, resolved_by}` — what is unknown and what would settle it |
| `limits` | array | statements that bound the result (backend used, scans, merged columns) |
| `audit` | object | `{checks[], passed, total, ratio, failed_critical}` |
| `artifacts` | array | every emitted file with size and sha256 |
| `contract` | object | declared contract fields, mapped values, and `unmapped` with a reason per field |
| `run` | object | started/finished, argv, python, backend, input description, case notes |

## status rules

- `success` — no critical check failed **and** `audit.ratio == 1.0`.
- `partial` — a critical check failed, or the ratio is below 1.0, but something
  usable was produced.
- `cannot_determine` — the audit ratio is 0, or no text layer exists.

A missing field is never a reason to fail the whole case: it becomes `null` in
`contract.unmapped` with `reason: not_produced_by_this_case`.

## anchor rules

`anchor.source` is a path **relative to the output directory**. `quote` must
equal `read_text(source)[char_start:char_end]` exactly (whitespace-normalised
comparison is accepted and reported as `whitespace-normalised`). `verified` is
the outcome of that check at write time; `scripts/verify.py` recomputes it.
