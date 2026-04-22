# /// script
# dependencies = [
#   "trl>=0.12",
#   "peft>=0.13",
#   "trackio",
#   "datasets>=3.1",
#   "transformers>=4.46",
#   "accelerate>=1.1",
# ]
# ///
"""
Stage-A SFT on Gemma-4-E2B-it + LoRA. Run locally (`uv run` + CUDA) or on HF Jobs.

Env: `HF_TOKEN` when pushing to Hub (omit with `--no-push`). Optional `TRACKIO_*`.

Dataset: default `nabin2004/manibench-sft-core` on Hub, or local JSONL via --train-jsonl.

Leak check: set --eval-hashes-json to manibench_eval_hashes.json from the repo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def _sha256(t: str) -> str:
    return hashlib.sha256(t.strip().encode()).hexdigest()


def _leak_check(jsonl_path: Path, hashes_path: Path) -> None:
    pilot = json.loads(hashes_path.read_text(encoding="utf-8"))
    hset = set((pilot.get("hashes") or pilot).values())
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            msgs = row.get("messages") or []
            for m in msgs:
                if m.get("role") == "user":
                    h = _sha256(m["content"])
                    if h in hset:
                        raise SystemExit(
                            "Leakage: training user message matches pilot hash "
                            f"{h[:16]}..."
                        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemma-4-E2B-it")
    ap.add_argument("--dataset", default="nabin2004/manibench-sft-core")
    ap.add_argument("--train-jsonl", type=Path, help="Override Hub dataset with local JSONL")
    ap.add_argument("--hub-model-id", default="nabin2004/manibench-gemma4-sft-stageA")
    ap.add_argument("--eval-hashes-json", type=Path, default=None)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--output-dir", default="stage-a-out")
    ap.add_argument(
        "--no-push",
        action="store_true",
        help="Save LoRA to --output-dir only; do not push to the Hub (no HF_TOKEN needed).",
    )
    ap.add_argument(
        "--per-device-train-batch-size",
        type=int,
        default=None,
        help="Override per-device train batch size (default 2). Lower if CUDA OOM on 24GB GPUs.",
    )
    ap.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Override SFT max token length (default 4096). Lower to reduce VRAM.",
    )
    args = ap.parse_args()

    if args.train_jsonl and args.eval_hashes_json:
        _leak_check(args.train_jsonl, args.eval_hashes_json)

    from datasets import Dataset, load_dataset  # noqa: WPS433
    from peft import LoraConfig  # noqa: WPS433
    from trl import SFTConfig, SFTTrainer  # noqa: WPS433

    if args.train_jsonl:
        rows = []
        with args.train_jsonl.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        ds = Dataset.from_list(rows).train_test_split(test_size=0.05, seed=42)
    else:
        raw = load_dataset(args.dataset, split="train")
        ds = raw.train_test_split(test_size=0.05, seed=42)

    push = not args.no_push
    batch = args.per_device_train_batch_size if args.per_device_train_batch_size is not None else 2
    max_len = args.max_length if args.max_length is not None else 4096

    trainer = SFTTrainer(
        model=args.model,
        train_dataset=ds["train"],
        eval_dataset=ds["test"],
        peft_config=LoraConfig(r=32, lora_alpha=64, target_modules="all-linear"),
        args=SFTConfig(
            output_dir=args.output_dir,
            push_to_hub=push,
            hub_model_id=args.hub_model_id if push else None,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=batch,
            gradient_accumulation_steps=16,
            learning_rate=args.lr,
            bf16=True,
            gradient_checkpointing=True,
            max_length=max_len,
            eval_strategy="steps",
            eval_steps=100,
            save_steps=200,
            report_to=os.environ.get("REPORT_TO", "none"),
            run_name=os.environ.get("TRACKIO_RUN_NAME", "stageA-sft"),
        ),
    )
    trainer.train()
    if push:
        trainer.push_to_hub()
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
