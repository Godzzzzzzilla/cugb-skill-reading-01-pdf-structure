# reading-01-pdf-structure — case demo-two-column-01

- status: **success** (all mandatory checks passed; every anchor re-slices exactly)
- checks: 13/13 passed, ratio=1.0
- evidence: 14 anchored claims
- finished: 2026-11-25T07:54:32Z

## Result

```json
{
 "document": {
  "pages": [
   {
    "page": 1,
    "source": "pages/p0001.txt",
    "chars": 2412,
    "blocks": 17,
    "width": 595.0,
    "height": 842.0
   },
   {
    "page": 2,
    "source": "pages/p0002.txt",
    "chars": 1461,
    "blocks": 16,
    "width": 595.0,
    "height": 842.0
   },
   {
    "page": 3,
    "source": "pages/p0003.txt",
    "chars": 1554,
    "blocks": 12,
    "width": 595.0,
    "height": 842.0
   }
  ],
  "sections": [
   {
    "title": "Abstract",
    "level": 1,
    "page": 1,
    "block_id": "p001b05",
    "char_start": 192,
    "char_end": 200,
    "evidence": "font-size",
    "evidence_id": "sec1"
   },
   {
    "title": "1 Introduction",
    "level": 1,
    "page": 1,
    "block_id": "p001b08",
    "char_start": 869,
    "char_end": 883,
    "evidence": "font-size",
    "evidence_id": "sec2"
   },
   {
    "title": "2 Method",
    "level": 1,
    "page": 1,
    "block_id": "p001b11",
    "char_start": 1594,
    "char_end": 1602,
    "evidence": "font-size",
    "evidence_id": "sec3"
   },
   {
    "title": "tau = 0.035 * W",
    "level": 1,
    "page": 1,
    "block_id": "p001b14",
    "char_start": 2356,
    "char_end": 2371,
    "evidence": "font-size",
    "evidence_id": "sec4"
   },
   {
    "title": "recall = |C_match| / |C_true|",
    "level": 1,
    "page": 1,
    "block_id": "p001b16",
    "char_start": 2378,
    "char_end": 2407,
    "evidence": "font-size",
    "evidence_id": "sec5"
   },
   {
    "title": "3 Experiments",
    "level": 1,
    "page": 2,
    "block_id": "p002b01",
    "char_start": 0,
    "char_end": 13,
    "evidence": "font-size",
    "evidence_id": "sec6"
   },
   {
    "title": "4 Results",
    "level": 1,
    "page": 2,
    "block_id": "p002b13",
    "char_start": 816,
    "char_end": 825,
    "evidence": "font-size",
    "evidence_id": "sec7"
   },
   {
    "title": "5 Discussion",
    "level": 1,
    "page": 3,
    "block_id": "p003b01",
    "char_start": 0,
    "char_end": 12,
    "evidence": "font-size",
    "evidence_id": "sec8"
   },
   {
    "title": "6 Conclusion",
    "level": 1,
    "page": 3,
    "block_id": "p003b05",
    "char_start": 571,
    "char_end": 583,
    "evidence": "font-size",
    "evidence_id": "sec9"
   },
   {
    "title": "References",
    "level": 1,
    "page": 3,
    "block_id": "p003b07",
    "char_start": 907,
    "char_end": 917,
    "evidence": "font-size",
    "evidence_id": "sec10"
   }
  ],
  "captions": [
   {
    "kind": "table",
    "text": "Table 1. Extraction quality on the three-page benchmark (mean of 3 runs).",
    "page": 2,
    "block_id": "p002b05",
    "char_start": 614,
    "char_end": 687,
    "bbox": [
     52.0,
     227.2,
     251.2,
     245.5
    ],
    "evidence_id": "cap1"
   }
  ],
  "equations": [
   {
    "number": "1",
    "text": "tau = 0.035 * W",
    "with_number": "tau = 0.035 * W (1)",
    "number_block": "p001b15",
    "page": 1,
    "block_id": "p001b14",
    "char_start": 2356,
    "char_end": 2371,
    "evidence_id": "eq1"
   },
   {
    "number": "2",
    "text": "recall = |C_match| / |C_true|",
    "with_number": "recall = |C_match| / |C_true| (2)",
    "number_block": "p001b17",
    "page": 1,
    "block_id": "p001b16",
    "char_start": 2378,
    "char_end": 2407,
    "evidence_id": "eq2"
   }
  ],
  "tables": [
   {
    "rows": [
     [
      "Extractor",
      "Char. recall",
      "Order tau",
      "Head leak",
      "Table F1"
     ],
     [
      "Content-stream",
      "71.4%",
      "0.41",
      "2.0",
      "0.55"
     ],
     [
      "Column-aware",
      "98.1%",
      "0.97",
      "0.0",
      "0.88"
     ]
    ],
    "n_rows": 3,
    "n_cols": 5,
    "bbox": [
     55.0,
     267.9,
     289.0,
     299.5
    ],
    "page": 2,
    "evidence": "caption-anchored",
    "evidence_id": "tab1"
   }
  ],
  "blocks": [
   {
    "block_id": "p001b01",
    "page": 1,
    "source": "pages/p0001.txt",
    "char_start": 0,
    "char_end": 61,
    "text": "Column-Aware Extraction of Structured Content from Two-Column",
    "bbox": [
     52.0,
     60.5,
     477.5,
     75.0
    ],
    "size": 14.5
   },
   {
    "block_id": "p001b02",
    "page": 1,
    "source": "pages/p0001.txt",
    "char_start": 63,
    "char_end": 80,
    "text": "Research Articles",
    "bbox": [
     52.0,
     78.0,
     165.6,
     92.5
    ],
    "size": 14.5
   },
   {
    "block_id": "p001b03",
    "page": 1,
    "source": "pages/p0001.txt",
    "char_start": 82,
    "char_end": 112,
    "text": "L. Chen, M. Okafor, R. Vasquez",
    "bbox": [
     52.0,
     104.7,
     200.8,
     115.2
    ],
    "size": 10.5
   },
   {
    "block_id": "p001b04",
    "page": 1,
    "source": "pages/p0001.txt",
    "char_start": 114,
    "char_end": 190,
    "text": "Institute of Document Engineering, Example University, Beijing 100084, China",
    "bbox": [
     52.0,
     119.5,
     335.0,
     127.7
    ],
    "size": 8.2
   },
   {
    "block_id": "p001b05",
    "page": 1,
    "source": "pages/p0001.txt",
    "char_start": 192,
    "char_end": 200,
    "text": "Abstract",
    "bbox": [
     52.0,
     138.1,
     88.7,
     148.1
    ],
    "size": 10.0
   },
   {
    "block_id": "p001b06",
    "page": 1,
    "source": "pages/p0001.txt",
    "char_start": 202,
    "char_end": 775,
    "text": "We study whether layout-aware reading-order reconstruction improves downstream use of scientific PDFs. A three-page benchmark with a known ground truth is rendered from a controlled layout engine, so that block order, header and footer positions, table cells and equation numbers are all known exactly. A naive extractor that reads glyphs in content-stream order recovers 71.4% of body characters in the correct position; a column-aware extractor that segments pages by whitespace cuts recovers 98.1%, and its block order agrees with the ground truth at Kendall tau = 0.97.",
    "bbox": [
     58.0,
     152.9,
     494.1,
     204.1
    ],
    "size": 8.2
   },
   {
    "block_id": "p0
```

## Evidence

| id | claim | locator | ok |
|---|---|---|---|
| sec1 | section heading: Abstract | `p.1 pages/p0001.txt[192:200]` | ✓ |
| sec2 | section heading: 1 Introduction | `p.1 pages/p0001.txt[869:883]` | ✓ |
| sec3 | section heading: 2 Method | `p.1 pages/p0001.txt[1594:1602]` | ✓ |
| sec4 | section heading: tau = 0.035 * W | `p.1 pages/p0001.txt[2356:2371]` | ✓ |
| sec5 | section heading: recall = |C_match| / |C_true| | `p.1 pages/p0001.txt[2378:2407]` | ✓ |
| sec6 | section heading: 3 Experiments | `p.2 pages/p0002.txt[0:13]` | ✓ |
| sec7 | section heading: 4 Results | `p.2 pages/p0002.txt[816:825]` | ✓ |
| sec8 | section heading: 5 Discussion | `p.3 pages/p0003.txt[0:12]` | ✓ |
| sec9 | section heading: 6 Conclusion | `p.3 pages/p0003.txt[571:583]` | ✓ |
| sec10 | section heading: References | `p.3 pages/p0003.txt[907:917]` | ✓ |
| cap1 | table caption | `p.2 pages/p0002.txt[614:687]` | ✓ |
| eq1 | equation (1) | `p.1 pages/p0001.txt[2356:2371]` | ✓ |
| eq2 | equation (2) | `p.1 pages/p0001.txt[2378:2407]` | ✓ |
| tab1 | table on page 2, 3x5 cells, first cell 'Extractor' | `p.2 pages/p0002.txt[689:698]` | ✓ |

## Limits

- layout backend was pdfminer; glyph coordinates are approximate
