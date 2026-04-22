# /// script
# dependencies = [
#   "trl>=0.12",
#   "peft>=0.13",
#   "datasets>=3.1",
#   "transformers>=4.46",
# ]
# ///
"""One-epoch LoRA SFT on iterative buffer JSONL (Stage B inner step)."""

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
            for m in row.get("messages", []):
                if m.get("role") == "user":
                    if _sha256(m["content"]) in hset:
                        raise SystemExit("Leakage detected vs pilot hashes")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", default="google/gemma-4-E2B-it")
    ap.add_argument("--train-jsonl", type=Path, required=True)
    ap.add_argument("--mix-jsonl", type=Path, nargs="*", help="Extra rows (e.g. 10% Stage-A core)")
    ap.add_argument("--hub-model-id", default="nabin2004/manibench-gemma4-sft-iter")
    ap.add_argument("--eval-hashes-json", type=Path, default=None)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--output-dir", default="incremental-out")
    ap.add_argument(
        "--no-push",
        action="store_true",
        help="Save LoRA to --output-dir only; do not push to the Hub.",
    )
    ap.add_argument(
        "--per-device-train-batch-size",
        type=int,
        default=None,
        help="Override per-device train batch size (default 2). Lower if CUDA OOM.",
    )
    ap.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Override SFT max token length (default 4096). Lower to reduce VRAM.",
    )
    args = ap.parse_args()

    if args.eval_hashes_json:
        _leak_check(args.train_jsonl, args.eval_hashes_json)

    rows = []
    with args.train_jsonl.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                if "messages" in obj:
                    rows.append({"messages": obj["messages"]})
    for mj in args.mix_jsonl or []:
        with mj.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))

    from datasets import Dataset  # noqa: WPS433
    from peft import LoraConfig  # noqa: WPS433
    from trl import SFTConfig, SFTTrainer  # noqa: WPS433

    ds = Dataset.from_list(rows).train_test_split(test_size=0.05, seed=42)

    push = not args.no_push
    batch = args.per_device_train_batch_size if args.per_device_train_batch_size is not None else 2
    max_len = args.max_length if args.max_length is not None else 4096

    trainer = SFTTrainer(
        model=args.base_model,
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
            eval_steps=50,
            report_to=os.environ.get("REPORT_TO", "none"),
            run_name=os.environ.get("TRACKIO_RUN_NAME", "incremental-sft"),
        ),
    )
    trainer.train()
    if push:
        trainer.push_to_hub()
    print("Incremental SFT done.", file=sys.stderr)


if __name__ == "__main__":
    main()
