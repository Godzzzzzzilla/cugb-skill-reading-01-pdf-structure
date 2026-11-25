#!/usr/bin/env python3
"""Self-test: the invariants this skill relies on, checked without the network.

    python scripts/selftest.py

Every check prints one line and the run ends with a count.  A failure here is
a defect in the skill, not in the input.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import armkit as ak  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  ✗ {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    here = os.path.dirname(HERE)
    demo = os.path.join(here, "examples", "input")
    pdf = os.path.join(demo, "paper.pdf")
    truth = os.path.join(demo, "ground_truth.json")

    print("armkit selftest")
    check("armkit version is pinned", bool(ak.VERSION), ak.VERSION)

    # 1. case reader tolerates missing and aliased fields
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "case.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"id": "c-1", "materials": [{"path": "paper.pdf"}], "question": "summarise"}, fh)
        case = ak.CaseInput.load(p)
        check("case_id alias", case.case_id == "c-1", case.case_id)
        check("task alias", case.task_text == "summarise", case.task_text)
        check("missing key returns None", case.get("does_not_exist") is None)
        check("empty case does not raise", ak.CaseInput.load(os.path.join(td, "nope.json")).case_id is not None)

    # 2. anchors are exact slices
    with tempfile.TemporaryDirectory() as td:
        text = "第一段。\n\nSecond paragraph."
        ak.write_text(os.path.join(td, "pages/p0001.txt"), text)
        anc = {"source": "pages/p0001.txt", "char_start": 0, "char_end": 4, "quote": text[0:4]}
        ok, why = ak.verify_anchor(td, anc)
        check("anchor re-slices exactly", ok, why)
        bad = dict(anc, quote="wrong")
        ok2, _ = ak.verify_anchor(td, bad)
        check("tampered anchor is rejected", not ok2)

    # 3. PDF pipeline on the bundled demo
    if os.path.isfile(pdf):
        pages, meta = ak.pdf_pages(pdf)
        check("pdf pages extracted", len(pages) == 3, f"{len(pages)} pages, backend={meta.get('backend')}")
        lay = ak.layout_blocks(pages)
        blocks = [b for p in lay["pages"] for b in p["blocks"]]
        check("blocks reconstructed", len(blocks) >= 20, f"{len(blocks)} blocks")
        leak = [b for b in blocks if "chen et al" in b["text"].casefold()]
        check("running head removed", not leak, f"{len(leak)} leaked")
        ordered = [(b["page"], b["char_start"]) for b in blocks]
        check("blocks are in page/offset order", ordered == sorted(ordered))
        two_col = any(
            min(b["bbox"][0] for b in p["blocks"]) < 200 < max(b["bbox"][0] for b in p["blocks"])
            for p in lay["pages"] if p["blocks"])
        check("two-column page detected", two_col)
        secs = ak.detect_sections(lay["pages"])
        check("sections detected", len(secs) >= 5, f"{len(secs)}: " + ", ".join(s["title"] for s in secs[:4]))
        tabs = ak.detect_tables(lay["pages"], {p.number: p.words for p in pages})
        check("table reconstructed", bool(tabs) and tabs[0]["n_cols"] >= 4,
              f"{tabs[0]['n_rows']}x{tabs[0]['n_cols']}" if tabs else "none")
        if os.path.isfile(truth):
            gt = json.load(open(truth, encoding="utf-8"))
            cells = set()
            for row in [gt["table"]["header"]] + gt["table"]["rows"]:
                cells |= {c for c in row}
            got = {c for row in (tabs[0]["rows"] if tabs else []) for c in row}
            check("table cells match ground truth", cells <= got, f"{len(cells & got)}/{len(cells)}")
    else:
        check("demo pdf present", False, pdf)

    # 4. status derivation is monotone
    a = ak.Audit()
    a.check("x", True, "ok", critical=True)
    check("all-pass -> success", ak.derive_status(a, True) == "success")
    a.check("y", False, "bad", critical=True)
    check("failed critical -> partial", ak.derive_status(a, True) == "partial")

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
