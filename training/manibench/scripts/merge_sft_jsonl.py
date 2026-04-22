#!/usr/bin/env python3
"""Merge multiple JSONL files into one training file (core + synthetic)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.leakage import assert_no_eval_leakage  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--skip-leak-check", action="store_true")
    args = ap.parse_args()

    rows = []
    for p in args.inputs:
        with p.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))

    if not args.skip_leak_check:
        texts = []
        for r in rows:
            for m in r.get("messages", []):
                if m.get("role") == "user":
                    texts.append(m["content"])
        assert_no_eval_leakage(texts)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Merged {len(rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
