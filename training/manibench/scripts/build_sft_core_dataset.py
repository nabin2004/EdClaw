#!/usr/bin/env python3
"""Build `manibench-sft-core` parquet/jsonl from GL→CE catalog + gallery seeds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.gl_ce_catalog import gallery_seed_examples, iter_gl_ce_pairs  # noqa: E402
from manibench.leakage import assert_no_eval_leakage  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "manibench-sft-core")
    ap.add_argument("--skip-leak-check", action="store_true")
    args = ap.parse_args()

    rows = iter_gl_ce_pairs() + gallery_seed_examples()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if not args.skip_leak_check:
        texts = []
        for r in rows:
            for m in r["messages"]:
                if m["role"] == "user":
                    texts.append(m["content"])
        assert_no_eval_leakage(texts)

    jsonl = args.out.with_suffix(".jsonl")
    with jsonl.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    try:
        from datasets import Dataset

        ds = Dataset.from_list(rows)
        ds.save_to_disk(str(args.out))
        print(f"Saved Dataset to disk: {args.out} ({len(rows)} rows)")
    except ImportError:
        print(f"datasets not installed; wrote JSONL only: {jsonl} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
