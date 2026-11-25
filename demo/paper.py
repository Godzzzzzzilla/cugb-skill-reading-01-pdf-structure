"""paper.py — build a small two-column demo paper as PDF + ground truth.

Why hand-write the PDF instead of using a library: the demo needs an exact
ground truth (true reading order, true block text, true table cells) to
measure extraction quality against.  Rendering it here means the ground
truth is the renderer's own layout, not a guess about someone else's.

Outputs (into the given directory):
    paper.pdf          two-column, 3 pages, running head, page numbers,
                       one table, two numbered equations, references
    paper.txt          the same text as a plain reading-order file
    ground_truth.json  pages -> blocks (text, bbox, order) + table + equations
"""
from __future__ import annotations

import json
import os
import re
import zlib

W, H = 595.0, 842.0
MARGIN_X, MARGIN_TOP, MARGIN_BOT = 52.0, 58.0, 56.0
GUTTER = 20.0
COL_W = (W - 2 * MARGIN_X - GUTTER) / 2
BODY = 8.6
LEAD = 11.2

TITLE = "Column-Aware Extraction of Structured Content from Two-Column Research Articles"
AUTHORS = "L. Chen, M. Okafor, R. Vasquez"
AFFIL = "Institute of Document Engineering, Example University, Beijing 100084, China"
ABSTRACT = (
    "We study whether layout-aware reading-order reconstruction improves downstream use of "
    "scientific PDFs. A three-page benchmark with a known ground truth is rendered from a "
    "controlled layout engine, so that block order, header and footer positions, table cells "
    "and equation numbers are all known exactly. A naive extractor that reads glyphs in "
    "content-stream order recovers 71.4% of body characters in the correct position; a "
    "column-aware extractor that segments pages by whitespace cuts recovers 98.1%, and its "
    "block order agrees with the ground truth at Kendall tau = 0.97."
)
KEYWORDS = "document layout analysis; reading order; two-column PDF; table extraction; reproducibility"

SECTIONS = [
    ("1  Introduction", [
        "Two-column typesetting is the default for most engineering and life-science journals, "
        "yet the text layer of a PDF stores glyphs in the order the producer wrote them, not in "
        "the order a reader consumes them. Extraction tools that ignore geometry therefore "
        "interleave the left and right columns and splice the last line of one paragraph onto "
        "the first line of its neighbour.",
        "The damage is quiet. A language model handed interleaved text still produces fluent "
        "answers, so the failure surfaces only when a claim is checked against the source. Our "
        "goal is narrower than full document understanding: recover blocks in reading order, "
        "keep a character range for every block, and report what could not be recovered.",
    ]),
    ("2  Method", [
        "The pipeline has three stages. Stage one obtains glyph bounding boxes from a layout "
        "backend. Stage two cuts each page recursively along the widest whitespace gap that no "
        "glyph crosses, which separates columns before it separates paragraphs. Stage three "
        "assembles lines into blocks, strips running heads by frequency, and records for each "
        "block a character range into the emitted page text.",
        "Formally, let R be the set of bounding boxes on a page and let g be a vertical gap. A "
        "cut at x = c is admissible when no box in R straddles c. We choose the admissible cut "
        "with maximal width, so that the column gutter is always taken before any intra-column "
        "gap, and recurse on both sides. The recursion stops when no gap exceeds tau = 3.5% of "
        "the page width.",
    ]),
    ("3  Experiments", [
        "The benchmark comprises three pages rendered at 8.6 pt with a 20 pt gutter, a running "
        "head, page numbers, one table with five columns and two numbered equations. Ground "
        "truth is emitted by the renderer, so text, order and table cells are exact rather than "
        "annotated by hand.",
        "We compare two extractors under identical inputs. The naive baseline concatenates text "
        "in content-stream order. The column-aware extractor is the pipeline of Section 2. Both "
        "are scored on character recall in the correct position, on block-order agreement, and "
        "on the number of running-head lines that leak into the body.",
    ]),
    ("4  Results", [
        "Table 1 reports the main comparison. The baseline recovers 71.4% of body characters in "
        "the correct position, leaks 2 running-head lines per page, and its block order "
        "correlates with the ground truth at tau = 0.41. The column-aware extractor reaches "
        "98.1%, leaks none, and reaches tau = 0.97.",
        "The residual 1.9% is concentrated in the table: cells whose text wraps across two lines "
        "are merged, because the current implementation joins lines by vertical proximity "
        "before it splits cells by horizontal gaps. Equation numbers are recovered exactly in "
        "both conditions because they sit at the right margin and survive content-stream order.",
    ]),
    ("5  Discussion", [
        "Reading order is a precondition for every downstream task, and it is cheap to verify: a "
        "character range either re-slices to the recorded text or it does not. We therefore "
        "report ranges rather than prose confidence, and we mark a block unresolved instead of "
        "guessing when its glyphs carry no usable position.",
        "Two limits deserve mention. Pages whose columns are separated by a rule rather than "
        "whitespace defeat the cut test, and scanned pages have no glyph positions at all until "
        "OCR runs. Both are reported as unresolved blocks with the reason attached.",
    ]),
    ("6  Conclusion", [
        "A whitespace-cut ordering pass, a frequency filter for running heads, and per-block "
        "character ranges together raise correct-position recall from 71.4% to 98.1% on a "
        "controlled two-column benchmark. The gain is measurable, the failure modes are named, "
        "and every reported block can be re-sliced from the emitted page text.",
    ]),
]

TABLE = {
    "caption": "Table 1. Extraction quality on the three-page benchmark (mean of 3 runs).",
    "header": ["Extractor", "Char. recall", "Order tau", "Head leak", "Table F1"],
    "rows": [
        ["Content-stream baseline", "71.4%", "0.41", "2.0", "0.55"],
        ["Column-aware (ours)", "98.1%", "0.97", "0.0", "0.88"],
    ],
}

EQUATIONS = [
    ("1", "tau = 0.035 * W", "page-width cut threshold"),
    ("2", "recall = |C_match| / |C_true|", "correct-position character recall"),
]

REFERENCES = [
    "[1] L. Chen and M. Okafor. Reading order recovery for two-column articles. Journal of "
    "Document Engineering, 12(3):201-219, 2023.",
    "[2] R. Vasquez, A. Petrov, and S. Iyer. Table structure recognition with weak supervision. "
    "In Proceedings of the Document Analysis Conference, pages 88-97, 2022.",
    "[3] M. Okafor. A note on running-head removal by frequency. Technical Report DE-2021-04, "
    "Example University, 2021.",
    "[4] H. Zhang and K. Nakamura. Evaluating PDF extractors against rendered ground truth. "
    "arXiv:2401.01234, 2024.",
    "[5] S. Iyer. Glyph geometry is not reading order. In Workshop on Scholarly Document "
    "Processing, pages 12-19, 2020.",
]

# page plan: list of (kind, payload)
PAGE_PLAN = [
    [("title", None), ("authors", None), ("abstract", None), ("section", 0), ("section", 1)],
    [("section", 2), ("table", None), ("section", 3)],
    [("section", 4), ("section", 5), ("references", None)],
]


# --------------------------------------------------------------------------- #
# PDF writing
# --------------------------------------------------------------------------- #


def _esc(text: str) -> bytes:
    out = []
    for ch in text:
        if ch in "()\\":
            out.append("\\" + ch)
        elif ord(ch) < 128:
            out.append(ch)
        elif ch == "\u00b5":
            out.append("\265")
        elif ch == "\u2013":
            out.append("\226")
        elif ch == "\u2014":
            out.append("\227")
        elif ch == "\u2019":
            out.append("\210")
        elif ch == "\u03c4":
            out.append("\164")  # handled by Symbol font switch upstream
        else:
            out.append("?")
    return "".join(out).encode("latin-1")


def _wrap(text: str, width_pt: float, size: float) -> list:
    """Greedy wrap on Helvetica widths (~0.5 em average); calibrated below."""
    max_chars = max(12, int(width_pt / (size * 0.495)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Page:
    def __init__(self, number: int):
        self.number = number
        self.ops: list = []
        self.blocks: list = []   # ground truth

    def text(self, x, y, s, size=BODY, font="F1"):
        self.ops.append(f"BT /{font} {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_esc(s).decode('latin-1')}) Tj ET")

    def line(self, x0, y0, x1, y1, w=0.6):
        self.ops.append(f"{w} w {x0:.2f} {y0:.2f} m {x1:.2f} {y1:.2f} l S")


def _column_flow(page: Page, items: list, gt: list, col: int, start_y: float) -> float:
    """Lay items down one column; records every rendered unit into `gt`."""
    x = MARGIN_X + col * (COL_W + GUTTER)
    y = start_y
    for kind, payload in items:
        if kind == "para":
            if y < MARGIN_BOT + 4:
                return y
            gt.append({"kind": "paragraph", "text": payload, "col": col,
                       "bbox": [x, y - LEAD * 0.8, x + COL_W, y + LEAD]})
            for line in _wrap(payload, COL_W, BODY):
                page.text(x, y, line)
                y -= LEAD
            y -= 3.0
        elif kind == "heading":
            if y < MARGIN_BOT + 18:
                return y
            page.text(x, y, payload, size=BODY + 2.2)
            gt.append({"kind": "heading", "text": payload, "col": col,
                       "bbox": [x, y - 2, x + COL_W, y + BODY + 2.2]})
            y -= LEAD * 1.35
        elif kind == "caption":
            if y < MARGIN_BOT + 30:
                return y
            gt.append({"kind": "caption", "text": payload, "col": col,
                       "bbox": [x, y - 2, x + COL_W, y + BODY]})
            for i, line in enumerate(_wrap(payload, COL_W, BODY - 0.6)):
                page.text(x, y, line, size=BODY - 0.6)
                y -= LEAD * 0.92
            y -= 4.0
        elif kind == "equation":
            num, body, _note = payload
            if y < MARGIN_BOT + 30:
                return y
            page.text(x + 10, y, body, size=BODY + 0.6)
            page.text(x + COL_W - 22, y, f"({num})", size=BODY)
            gt.append({"kind": "equation", "text": f"{body} ({num})", "col": col,
                       "bbox": [x, y - 2, x + COL_W, y + BODY]})
            y -= LEAD * 1.6
    return y


def build(out_dir: str, interleaved: bool = False, filename: str = "paper.pdf") -> dict:
    os.makedirs(out_dir, exist_ok=True)
    pages: list = []
    truth_pages: list = []
    page_texts: list = []

    # distribute sections across the three planned pages, two columns each
    for pno, layout in enumerate(PAGE_PLAN, start=1):
        page = Page(pno)
        gt: list = []
        text_runs: list = []

        # running head + page number (must be stripped by any serious extractor)
        head = f"Chen et al. / Column-Aware Extraction of Structured Content    {pno}"
        page.text(MARGIN_X, H - 40, head, size=7.6)
        page.line(MARGIN_X, H - 45, W - MARGIN_X, H - 45, 0.5)
        page.text(W / 2 - 4, 34, str(pno), size=8)

        front: list = []
        y_title = H - MARGIN_TOP - 14
        if pno == 1:
            for i, line in enumerate(_wrap(TITLE, W - 2 * MARGIN_X, 14.5)):
                page.text(MARGIN_X, y_title - i * 17.5, line, size=14.5)
                front.append({"kind": "title", "text": line, "bbox": [MARGIN_X, y_title - i * 17.5, W - MARGIN_X, y_title - i * 17.5 + 16]})
            y = y_title - len(_wrap(TITLE, W - 2 * MARGIN_X, 14.5)) * 17.5 - 6
            page.text(MARGIN_X, y, AUTHORS, size=10.5)
            front.append({"kind": "authors", "text": AUTHORS, "bbox": [MARGIN_X, y, W - MARGIN_X, y + 10]})
            y -= 13
            page.text(MARGIN_X, y, AFFIL, size=8.2)
            front.append({"kind": "affiliation", "text": AFFIL, "bbox": [MARGIN_X, y, W - MARGIN_X, y + 8]})
            y -= 20
            page.text(MARGIN_X, y, "Abstract", size=BODY + 1.4)
            front.append({"kind": "heading", "text": "Abstract", "bbox": [MARGIN_X, y, MARGIN_X + 60, y + BODY + 1.4]})
            y -= LEAD * 1.2
            front.append({"kind": "abstract", "text": ABSTRACT, "bbox": [MARGIN_X + 6, y - 4, W - MARGIN_X, y + LEAD]})
            for line in _wrap(ABSTRACT, W - 2 * MARGIN_X - 12, BODY - 0.4):
                page.text(MARGIN_X + 6, y, line, size=BODY - 0.4)
                y -= LEAD * 0.96
            y -= 6
            page.text(MARGIN_X, y, KEYWORDS, size=BODY - 0.8)
            front.append({"kind": "keywords", "text": KEYWORDS, "bbox": [MARGIN_X, y, W - MARGIN_X, y + BODY]})
            y -= LEAD * 1.8
            col_start = y
        else:
            col_start = H - MARGIN_TOP - 20

        # build per-column item lists
        left_items: list = []
        right_items: list = []
        for kind, idx in layout:
            if kind == "section":
                title, paras = SECTIONS[idx]
                left_items.append(("heading", title))
                for para in paras:
                    left_items.append(("para", para))
                if idx == 2:
                    left_items.append(("caption", TABLE["caption"]))
                    left_items.append(("table", None))
                if idx == 1:
                    left_items.append(("equation", EQUATIONS[0]))
                    left_items.append(("equation", EQUATIONS[1]))
            elif kind == "table":
                continue
            elif kind == "references":
                left_items.append(("heading", "References"))
                for ref in REFERENCES:
                    left_items.append(("para", ref))

        # equal split by rendered height so both columns end near the bottom
        total = len(left_items)
        half = max(1, total // 2)
        left, right = left_items[:half], left_items[half:]

        y_left = _column_flow(page, left, gt, 0, col_start)
        _column_flow(page, right, gt, 1, col_start)

        # table: draw into the column where the caption landed (left, page 2)
        table_gt = None
        if pno == 2:
            tx = MARGIN_X
            ty = y_left - 8
            col_w = [78, 46, 38, 38, 38]
            page.line(tx, ty + 2, tx + sum(col_w), ty + 2, 0.8)
            cx = tx
            for i, cell in enumerate(TABLE["header"]):
                page.text(cx + 2, ty - 7, cell, size=7.4)
                cx += col_w[i]
            page.line(tx, ty - 10, tx + sum(col_w), ty - 10, 0.5)
            for r, row in enumerate(TABLE["rows"]):
                ry = ty - 10 - (r + 1) * 12.5
                cx = tx
                for i, cell in enumerate(row):
                    page.text(cx + 2, ry + 3, cell, size=7.4)
                    cx += col_w[i]
            page.line(tx, ty - 10 - len(TABLE["rows"]) * 12.5 + 2,
                      tx + sum(col_w), ty - 10 - len(TABLE["rows"]) * 12.5 + 2, 0.8)
            table_gt = {"header": TABLE["header"], "rows": TABLE["rows"],
                        "bbox": [tx, ty - 10 - len(TABLE["rows"]) * 12.5, tx + sum(col_w), ty + 2]}

        # ground truth: front matter (page 1), then column 0 top-down, then column 1
        blocks = []
        for item in front:
            blocks.append({"text": item["text"], "kind": item["kind"], "bbox": item["bbox"]})
        for side in (0, 1):
            for item in gt:
                if item["col"] != side:
                    continue
                blocks.append({"text": item["text"], "kind": item["kind"], "bbox": item["bbox"]})
        if table_gt:
            blocks.append({"text": " | ".join(TABLE["header"]), "kind": "table-row", "bbox": table_gt["bbox"]})
            for row in TABLE["rows"]:
                blocks.append({"text": " | ".join(row), "kind": "table-row", "bbox": table_gt["bbox"]})
        truth_pages.append({"page": pno, "blocks": blocks, "table": table_gt})

        # plain text layer in true reading order
        lines = [head, "", str(pno), ""]
        if pno == 1:
            lines += _wrap(TITLE, W - 2 * MARGIN_X, 14.5) + [AUTHORS, AFFIL, "Abstract"]
            lines += _wrap(ABSTRACT, W - 2 * MARGIN_X - 12, BODY - 0.4) + [KEYWORDS, ""]
        for kind, payload in left + right:
            if kind == "heading":
                lines += ["", payload, ""]
            elif kind == "para":
                lines += _wrap(payload, COL_W, BODY) + [""]
            elif kind == "caption":
                lines += _wrap(payload, COL_W, BODY - 0.6)
            elif kind == "equation":
                lines += [f"{payload[1]}   ({payload[0]})"]
            elif kind == "table":
                lines += [" | ".join(TABLE["header"])]
                for row in TABLE["rows"]:
                    lines += [" | ".join(row)]
        page_texts.append("\n".join(lines))
        pages.append(page)

    if interleaved:
        for page in pages:
            text_ops, other = [], []
            for op in page.ops:
                m = re.search(r"1 0 0 1 ([-\d.]+) ([-\d.]+) Tm", op)
                if op.startswith("BT ") and m:
                    text_ops.append((float(m.group(2)), float(m.group(1)), op))
                else:
                    other.append(op)
            text_ops.sort(key=lambda t: (-t[0], t[1]))
            page.ops = other + [t[2] for t in text_ops]

    # serialise
    objects: list = []

    def add(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)

    font_ids = {}
    for name in ("F1", "F2"):
        font_ids[name] = add(f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                             f"/Encoding /WinAnsiEncoding >>".encode())
    page_ids = []
    content_ids = []
    for page in pages:
        stream = ("\n".join(page.ops)).encode("latin-1", "replace")
        content_ids.append(add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"))
    pages_id = len(objects) + 2 * len(pages) + 1
    for i, page in enumerate(pages):
        page_ids.append(add(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {W} {H}] "
            f"/Resources << /Font << /F1 {font_ids['F1']} 0 R /F2 {font_ids['F2']} 0 R >> >> "
            f"/Contents {content_ids[i]} 0 R >>".encode()))
    pages_obj = add(f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] "
                    f"/Count {len(page_ids)} >>".encode())
    cat = add(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>".encode())

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects)+1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects)+1} /Root {cat} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n").encode()

    pdf_path = os.path.join(out_dir, filename)
    with open(pdf_path, "wb") as fh:
        fh.write(bytes(out))

    truth = {"title": TITLE, "authors": AUTHORS, "affiliation": AFFIL,
             "abstract": ABSTRACT, "keywords": KEYWORDS,
             "sections": [s[0] for s in SECTIONS],
             "pages": truth_pages, "table": TABLE, "equations": EQUATIONS,
             "references": REFERENCES}
    with open(os.path.join(out_dir, "ground_truth.json"), "w", encoding="utf-8") as fh:
        json.dump(truth, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "paper.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n\n".join(page_texts) + "\n")
    return {"pdf": pdf_path, "pages": len(pages),
            "bytes": os.path.getsize(pdf_path)}


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    info = build(target, filename="paper.pdf")
    alt = build(target, interleaved=True, filename="paper_interleaved.pdf")
    print(json.dumps({"column_major": info, "row_major": alt}, indent=1))
