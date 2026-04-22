#!/usr/bin/env python3
"""Push a local dataset directory or JSONL to the Hugging Face Hub."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True, help="e.g. nabin2004/manibench-sft-core")
    ap.add_argument("--jsonl", type=Path, help="Path to JSONL messages file")
    ap.add_argument("--dataset-dir", type=Path, help="Path from datasets.save_to_disk")
    ap.add_argument("--private", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN required for push", file=sys.stderr)
        sys.exit(1)

    from datasets import Dataset, DatasetDict  # noqa: WPS433

    if args.jsonl:
        rows = []
        with args.jsonl.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        ds = Dataset.from_list(rows)
    elif args.dataset_dir:
        from datasets import load_from_disk

        ds = load_from_disk(str(args.dataset_dir))
    else:
        print("Provide --jsonl or --dataset-dir", file=sys.stderr)
        sys.exit(1)

    if isinstance(ds, DatasetDict):
        ds.push_to_hub(args.repo_id, private=args.private, token=token)
    else:
        DatasetDict({"train": ds}).push_to_hub(args.repo_id, private=args.private, token=token)

    print(f"Pushed to https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
