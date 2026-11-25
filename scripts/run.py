#!/usr/bin/env python3
"""reading-01-pdf-structure — turn a research PDF into an auditable structure.

Contract
    python scripts/run.py --input /input/case.json --output /app/output

Writes into --output:
    pages/pNNNN.txt      page text in reading order (the anchor substrate)
    document.json        sections, blocks, captions, equations, tables, offsets
    evidence.jsonl       one anchored claim per line
    result.json          the case deliverable (status, sources, uncertainty)
    report.md            human-readable summary
    audit.json           which checks passed

Exit code is 0 for every case this script can read, including a partial one.
A non-zero exit means the process itself failed, not that the document is bad.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import armkit as ak  # noqa: E402

SKILL = "reading-01-pdf-structure"
VERSION = "1.0.0"


def solve(case: ak.CaseInput, out: str, audit: ak.Audit, res: ak.Result) -> bool:
    layer = ak.TextLayer(out, "pages")
    pdfs = case.pdfs
    texts = [p for p in case.discover() if p.lower().endswith((".txt", ".md")) and
             os.path.basename(p) not in ("task.md",)]

    audit.check("input-found", bool(pdfs or texts),
                f"{len(pdfs)} pdf, {len(texts)} text file(s) under {case.dir}", critical=True)
    if not pdfs and not texts:
        res.set("document", None)
        res.add_uncertainty("no readable input", "case.json names no file and the input directory is empty",
                            "point the case at a PDF or text file")
        return False

    pages_struct, meta, notes = [], {}, []
    if pdfs:
        raw_pages, meta = ak.pdf_pages(pdfs[0])
        res.meta["pdf_backend"] = meta.get("backend")
        res.meta["pdf_bytes"] = os.path.getsize(pdfs[0])
        audit.check("pdf-opened", bool(raw_pages), f"backend={meta.get('backend')}, pages={len(raw_pages)}",
                    critical=True)
        if meta.get("warn"):
            notes.append(meta["warn"])
        if not raw_pages:
            res.add_uncertainty("PDF produced no text layer",
                                "every backend failed or the page has no glyphs (likely a scan)",
                                "run OCR (tesseract/paddleocr) and feed the text back in")
            res.limits.append("scanned PDF without a text layer is reported, not guessed")
            return False
        layout = ak.layout_blocks(raw_pages)
        pages_struct = layout["pages"]
        words_by_page = {p.number: p.words for p in raw_pages}
        res.meta["dropped_lines"] = sum(len(p["dropped"]) for p in pages_struct)
    else:
        text, tmeta = ak.read_text(texts[0])
        audit.check("text-readable", bool(text.strip()), f"{len(text)} chars, encoding={tmeta.get('encoding')}",
                    critical=True)
        pages_struct = _text_to_pages(text)
        words_by_page = {}

    if not any(p["blocks"] for p in pages_struct):
        audit.check("blocks-found", False, "no blocks reconstructed", critical=True)
        return False
    audit.check("blocks-found", True, f"{sum(len(p['blocks']) for p in pages_struct)} blocks")

    # emit the anchor substrate first: every claim below is a slice of these files
    for pg in pages_struct:
        layer.add_page(pg["page"], pg["text"], {"blocks": len(pg["blocks"]), "method": pg.get("method", "")})
    for pg in pages_struct:
        rel = f"pages/p{pg['page']:04d}.txt"
        for b in pg["blocks"]:
            b["source"] = rel
            if pg["text"][b["char_start"]:b["char_end"]] != b["text"]:
                b["offset_ok"] = False
            else:
                b["offset_ok"] = True

    sections = ak.detect_sections(pages_struct)
    captions = ak.detect_captions(pages_struct)
    equations = ak.detect_equations(pages_struct)
    tables = ak.detect_tables(pages_struct, words_by_page, captions)

    # anchors: sections, captions, equations, tables
    for i, s in enumerate(sections, start=1):
        src = f"pages/p{s['page']:04d}.txt"
        pg = next(p for p in pages_struct if p["page"] == s["page"])
        anchor = ak.Anchor(src, s["char_start"], s["char_end"], pg["text"][s["char_start"]:s["char_end"]],
                           page=s["page"], block_id=s["block_id"])
        ok, why = ak.verify_anchor(out, anchor.as_dict())
        s["evidence_id"] = f"sec{i}"
        res.add_evidence(f"sec{i}", f"section heading: {s['title']}", anchor, ok, why)

    for i, c in enumerate(captions, start=1):
        src = f"pages/p{c['page']:04d}.txt"
        anchor = ak.Anchor(src, c["char_start"], c["char_end"], c["text"], page=c["page"], block_id=c["block_id"])
        ok, why = ak.verify_anchor(out, anchor.as_dict())
        c["evidence_id"] = f"cap{i}"
        res.add_evidence(f"cap{i}", f"{c['kind']} caption", anchor, ok, why)

    for i, e in enumerate(equations, start=1):
        src = f"pages/p{e['page']:04d}.txt"
        anchor = ak.Anchor(src, e["char_start"], e["char_end"], e["text"], page=e["page"], block_id=e["block_id"])
        ok, why = ak.verify_anchor(out, anchor.as_dict())
        e["evidence_id"] = f"eq{i}"
        res.add_evidence(f"eq{i}", f"equation ({e['number']})", anchor, ok, why)

    for i, t in enumerate(tables, start=1):
        t["evidence_id"] = f"tab{i}"
        src = f"pages/p{t['page']:04d}.txt"
        pg = next(p for p in pages_struct if p["page"] == t["page"])
        first = next((c for row in t["rows"] for c in row if c.strip()), "")
        cut = first[:60]
        at = pg["text"].find(cut) if cut else -1
        if at >= 0:
            anchor = ak.Anchor(src, at, at + len(cut), cut, page=t["page"])
            ok, why = ak.verify_anchor(out, anchor.as_dict())
            res.add_evidence(f"tab{i}", f"table on page {t['page']}, {t['n_rows']}x{t['n_cols']} cells, "
                                        f"first cell {cut!r}", anchor, ok, why)
        else:
            res.add_evidence(f"tab{i}", f"table on page {t['page']}, {t['n_rows']}x{t['n_cols']} cells",
                             ak.Anchor(src, 0, 0, ""), False,
                             "cells were located by x-position; no contiguous range to quote")
            res.add_uncertainty(f"table {i} has no quotable range",
                                "cells are separated by wide gaps, so the table is not one contiguous slice",
                                "compare the cell matrix against the page image")

    # audit
    total_blocks = sum(len(p["blocks"]) for p in pages_struct)
    bad_offsets = sum(1 for p in pages_struct for b in p["blocks"] if not b.get("offset_ok"))
    audit.check("block-offsets-exact", bad_offsets == 0,
                f"{total_blocks - bad_offsets}/{total_blocks} blocks re-slice to their own text", critical=True)
    verified = sum(1 for e in res.evidence if e["verified"])
    audit.check("anchors-verified", verified == len(res.evidence) and verified > 0,
                f"{verified}/{len(res.evidence)} anchors re-sliced", critical=True)
    audit.check("running-heads-removed", not any("et al." in b["text"][:40] and len(b["text"]) < 90
                                                 for p in pages_struct for b in p["blocks"]),
                "no repeated running-head line survived into the body")
    audit.check("sections-ordered", _sections_ordered(sections),
                f"{len(sections)} headings in page/offset order", weight=1.0)
    audit.check("sections-found", len(sections) >= 3, f"{len(sections)} headings", weight=0.6)
    audit.check("multi-column-handled", _columns_ok(pages_struct), "blocks on at least one page occupy two x-bands",
                weight=0.5)
    audit.check("captions-detected", len(captions) >= 1, f"{len(captions)} captions", weight=0.6)
    audit.check("tables-detected", len(tables) >= 1, f"{len(tables)} tables", weight=0.6)
    audit.check("equations-detected", len(equations) >= 1, f"{len(equations)} numbered equations", weight=0.4)
    coverage = _structure_coverage(sections, captions, tables, equations)
    audit.check("structure-coverage", coverage >= 0.5, f"{coverage:.0%} of the four structural classes present",
                weight=0.8)

    doc = {
        "pages": [{"page": p["page"], "source": f"pages/p{p['page']:04d}.txt",
                   "chars": p["chars"], "blocks": len(p["blocks"]),
                   "width": p.get("width"), "height": p.get("height")} for p in pages_struct],
        "sections": sections,
        "captions": captions,
        "equations": equations,
        "tables": tables,
        "blocks": [{"block_id": b["block_id"], "page": b["page"], "source": b["source"],
                    "char_start": b["char_start"], "char_end": b["char_end"],
                    "text": b["text"], "bbox": b.get("bbox"), "size": b.get("size")}
                   for p in pages_struct for b in p["blocks"]],
        "reading_order": [b["block_id"] for p in pages_struct for b in p["blocks"]],
    }
    res.set("document", doc)
    res.set("page_count", len(pages_struct))
    res.set("block_count", total_blocks)
    res.set("section_count", len(sections))
    res.set("table_count", len(tables))
    res.set("caption_count", len(captions))
    res.set("equation_count", len(equations))
    res.set("markdown", _to_markdown(pages_struct, sections))

    res.add_artifact("document.json", "data", "full structure")
    ak.write_json(os.path.join(out, "document.json"), doc)
    md = _to_markdown(pages_struct, sections)
    ak.write_text(os.path.join(out, "structured.md"), md)
    res.add_artifact("structured.md", "data", "reading-order markdown")
    for note in notes:
        res.limits.append(note)
    if meta.get("backend") and meta["backend"] != "pdftotext-bbox":
        res.limits.append(f"layout backend was {meta['backend']}; glyph coordinates are approximate")
    return True


def _text_to_pages(text: str):
    chunks = [c for c in text.split("\f") if c.strip()]
    pages = []
    for i, chunk in enumerate(chunks or [text], start=1):
        paras = [p.strip() for p in chunk.replace("\r\n", "\n").split("\n\n") if p.strip()]
        cursor, blocks = 0, []
        for j, para in enumerate(paras, start=1):
            if blocks:
                cursor += 2
            blocks.append({"page": i, "block_id": f"p{i:03d}b{j:02d}", "text": para,
                           "char_start": cursor, "char_end": cursor + len(para),
                           "bbox": None, "size": 0.0, "lines": para.count("\n") + 1})
            cursor += len(para)
        pages.append({"page": i, "blocks": blocks, "text": "\n\n".join(b["text"] for b in blocks),
                      "chars": cursor, "dropped": [], "width": None, "height": None, "method": "text"})
    return pages


def _to_markdown(pages, sections) -> str:
    out = []
    titles = {s["block_id"]: s for s in sections}
    for pg in pages:
        out.append(f"<!-- page {pg['page']} -->")
        for b in pg["blocks"]:
            if b["block_id"] in titles:
                s = titles[b["block_id"]]
                out.append(f"\n{'#' * min(6, max(1, s['level'] + 1))} {b['text']}\n")
            else:
                out.append(b["text"])
        out.append("")
    return "\n\n".join(out)


def _sections_ordered(sections) -> bool:
    keys = [(s["page"], s["char_start"]) for s in sections]
    return keys == sorted(keys)


def _columns_ok(pages) -> bool:
    for pg in pages:
        xs = [b["bbox"][0] for b in pg["blocks"] if b.get("bbox")]
        if not xs:
            continue
        left = [x for x in xs if x < (pg.get("width") or 600) / 2]
        right = [x for x in xs if x >= (pg.get("width") or 600) / 2]
        if left and right:
            return True
    return False


def _structure_coverage(sections, captions, tables, equations) -> float:
    return sum(1 for x in (sections, captions, tables, equations) if len(x) > 0) / 4.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input/case.json")
    ap.add_argument("--output", default="/app/output")
    args = ap.parse_args()

    ak.safe_stdout()
    started = ak.utc_now()
    os.makedirs(args.output, exist_ok=True)
    case = ak.CaseInput.load(args.input, work_dir=args.output)
    audit = ak.Audit("reading-01")
    res = ak.Result(args.output, SKILL, VERSION)

    try:
        required_ok = solve(case, args.output, audit, res)
    except Exception as exc:  # the contract says: still write a complete result
        import traceback
        traceback.print_exc()
        required_ok = False
        audit.check("pipeline-completed", False, f"{type(exc).__name__}: {exc}", critical=True)
        res.add_uncertainty("pipeline exception", f"{type(exc).__name__}: {exc}",
                            "inspect audit.json before trusting any field")
        res.set("document", None)

    res.meta["case_notes"] = case.notes
    res.meta["input"] = case.describe()
    status = ak.derive_status(audit, required_ok)
    if not required_ok and status == "success":
        status = "partial"
    reason = {
        "success": "all mandatory checks passed; every anchor re-slices exactly",
        "partial": "some structure was recovered; see audit.failed_critical",
        "cannot_determine": "no usable text layer or input could be read",
    }.get(status, status)
    res.write(case, audit, status, reason, started, sys.argv)
    print(f"wrote result.json status={status} checks={audit.as_dict()['passed']}/{audit.as_dict()['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
