#!/usr/bin/env python3
"""Independent verifier: re-slice every anchor and recompute the audit.

    python scripts/verify.py --result /app/output/result.json

It trusts nothing in result.json except the coordinates.  Exit code 0 means
every recorded range still matches its quote; 1 means at least one does not.
This is the command a reviewer runs to decide whether to believe the result.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import armkit as ak  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", default="/app/output/result.json")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    path = os.path.abspath(args.result)
    out_dir = os.path.dirname(path)
    if not os.path.isfile(path):
        print(f"FAIL: no result at {path}")
        return 1
    doc = json.load(open(path, encoding="utf-8"))
    evidence = doc.get("evidence") or []
    ok = bad = 0
    for rec in evidence:
        anchor = rec.get("anchor") or {}
        good, why = ak.verify_anchor(out_dir, anchor)
        if good:
            ok += 1
            if not args.quiet:
                print(f"  ✓ {rec.get('id')}: {anchor.get('source')}[{anchor.get('char_start')}:{anchor.get('char_end')}] {why}")
        else:
            bad += 1
            print(f"  ✗ {rec.get('id')}: {why}")

    declared = doc.get("audit", {}).get("ratio")
    status = doc.get("status")
    print(f"anchors: {ok} verified, {bad} failed, {len(evidence)} total")
    print(f"declared: status={status} audit_ratio={declared}")
    if evidence and bad == 0:
        print("VERDICT: anchors are reproducible from the emitted text files alone")
        return 0
    if not evidence:
        print("VERDICT: no anchors to verify")
        return 1
    print("VERDICT: at least one anchor cannot be re-sliced; do not trust those claims")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
