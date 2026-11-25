<!-- page 1 -->

Column-Aware Extraction of Structured Content from Two-Column

Research Articles

L. Chen, M. Okafor, R. Vasquez

Institute of Document Engineering, Example University, Beijing 100084, China


## Abstract


We study whether layout-aware reading-order reconstruction improves downstream use of scientific PDFs. A three-page benchmark with a known ground truth is rendered from a controlled layout engine, so that block order, header and footer positions, table cells and equation numbers are all known exactly. A naive extractor that reads glyphs in content-stream order recovers 71.4% of body characters in the correct position; a column-aware extractor that segments pages by whitespace cuts recovers 98.1%, and its block order agrees with the ground truth at Kendall tau = 0.97.

document layout analysis; reading order; two-column PDF; table extraction; reproducibility


## 1 Introduction


Two-column typesetting is the default for most engineering and life-science journals, yet the text layer of a PDF stores glyphs in the order the producer wrote them, not in the order a reader consumes them. Extraction tools that ignore geometry therefore interleave the left and right columns and splice the last line of one paragraph onto the first line of its neighbour.

The damage is quiet. A language model handed interleaved text still produces fluent answers, so the failure surfaces only when a claim is checked against the source. Our goal is narrower than full document understanding: recover blocks in reading order, keep a character range for every block, and report what could not be recovered.


## 2 Method


The pipeline has three stages. Stage one obtains glyph bounding boxes from a layout backend. Stage two cuts each page recursively along the widest whitespace gap that no glyph crosses, which separates columns before it separates paragraphs. Stage three assembles lines into blocks, strips running heads by frequency, and records for each block a character range into the emitted page text.

Formally, let R be the set of bounding boxes on a page and let g be a vertical gap. A cut at x = c is admissible when no box in R straddles c. We choose the admissible cut with maximal width, so that the column gutter is always taken before any intra-column gap, and recurse on both sides. The recursion stops when no gap exceeds tau = 3.5% of the page width.


## tau = 0.035 * W


(1)


## recall = |C_match| / |C_true|


(2)



<!-- page 2 -->


## 3 Experiments


The benchmark comprises three pages rendered at 8.6 pt with a 20 pt gutter, a running head, page numbers, one table with five columns and two numbered equations.

Ground truth is emitted by the renderer, so text, order and table cells are exact rather than annotated by hand.

We compare two extractors under identical inputs. The naive baseline concatenates text in content-stream order. The column-aware extractor is the pipeline of Section 2. Both are scored on character recall in the correct position, on block-order agreement, and on the number of running-head lines that leak into the body.

Table 1. Extraction quality on the three-page benchmark (mean of 3 runs).

Extractor

Content-stream Column-aware

Char. recall Order tau Head leak Table F1

71.4% 98.1%

0.41 0.97

2.0 0.0

0.55 0.88


## 4 Results


Table 1 reports the main comparison. The baseline recovers 71.4% of body characters in the correct position, leaks 2 running-head lines per page, and its block order correlates with the ground truth at tau = 0.41. The column-aware extractor reaches 98.1%, leaks none, and reaches tau = 0.97.

The residual 1.9% is concentrated in the table: cells whose text wraps across two lines are merged, because the current implementation joins lines by vertical proximity before it splits cells by horizontal gaps.

Equation numbers are recovered exactly in both conditions because they sit at the right margin and survive content-stream order.



<!-- page 3 -->


## 5 Discussion


Reading order is a precondition for every downstream task, and it is cheap to verify: a character range either re-slices to the recorded text or it does not.

We therefore report ranges rather than prose confidence, and we mark a block unresolved instead of guessing when its glyphs carry no usable position.

Two limits deserve mention. Pages whose columns are separated by a rule rather than whitespace defeat the cut test, and scanned pages have no glyph positions at all until OCR runs. Both are reported as unresolved blocks with the reason attached.


## 6 Conclusion


A whitespace-cut ordering pass, a frequency filter for running heads, and per-block character ranges together raise correct-position recall from 71.4% to 98.1% on a controlled two-column benchmark. The gain is measurable, the failure modes are named, and every reported block can be re-sliced from the emitted page text.


## References


[1] L. Chen and M. Okafor. Reading order recovery for two-column articles. Journal of Document Engineering, 12(3):201-219, 2023.

[2] R. Vasquez, A. Petrov, and S. Iyer. Table structure recognition with weak supervision. In Proceedings of the Document Analysis Conference, pages 88-97, 2022.

[3] M. Okafor. A note on running-head removal by frequency. Technical Report DE-2021-04, Example University, 2021.

[4] H. Zhang and K. Nakamura. Evaluating PDF extractors against rendered ground truth. arXiv:2401.01234, 2024.

[5] S. Iyer. Glyph geometry is not reading order. In Workshop on Scholarly Document Processing, pages 12-19, 2020.

