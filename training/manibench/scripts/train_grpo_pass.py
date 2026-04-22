# /// script
# dependencies = [
#   "trl>=0.12",
#   "peft>=0.13",
#   "datasets>=3.1",
#   "transformers>=4.46",
# ]
# ///
"""
GRPO with composite ManiBench reward.

Set `MANIBENCH_GRPO_RENDER=1` to enable subprocess manim render inside reward (slow).
Default is heuristic-only (VCER + syntax) for smoke tests.

TRL newer versions accept `model` as a Hub id string and `reward_funcs` as a callable.
See: https://huggingface.co/docs/trl/grpo_trainer
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        default="google/gemma-4-E2B-it",
        help="Base model id; use a merged Hub id if continuing from SFT/DPO.",
    )
    ap.add_argument("--prompts-jsonl", type=str, required=True)
    ap.add_argument("--hub-model-id", default="nabin2004/manibench-gemma4-grpo")
    ap.add_argument("--output-dir", default="grpo-out")
    ap.add_argument(
        "--no-push",
        action="store_true",
        help="Save to --output-dir only; do not push to the Hub.",
    )
    ap.add_argument(
        "--per-device-train-batch-size",
        type=int,
        default=None,
        help="Override per-device train batch size (default 1). Lower if CUDA OOM.",
    )
    ap.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Override GRPO max_completion_length (default 8192). Lower to reduce VRAM.",
    )
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT))
    from manibench.eval.harness import composite_reward, evaluate_sample  # noqa: WPS433

    run_render = os.environ.get("MANIBENCH_GRPO_RENDER", "0") == "1"

    def manibench_reward(completions, **kwargs):  # noqa: ANN001
        scores = []
        for c in completions:
            text = ""
            if isinstance(c, list) and c:
                first = c[0]
                text = first.get("content", "") if isinstance(first, dict) else str(first)
            elif isinstance(c, str):
                text = c
            else:
                text = str(c)
            m = evaluate_sample(text, run_render=run_render)
            scores.append(composite_reward(m))
        return scores

    prompts = []
    with open(args.prompts_jsonl, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                msgs = row.get("messages") or []
                user = ""
                for m in msgs:
                    if m.get("role") == "user":
                        user = m["content"]
                prompts.append(user)

    from datasets import Dataset  # noqa: WPS433
    from peft import LoraConfig  # noqa: WPS433
    from trl import GRPOConfig, GRPOTrainer  # noqa: WPS433

    ds = Dataset.from_dict({"prompt": prompts})

    push = not args.no_push
    batch = args.per_device_train_batch_size if args.per_device_train_batch_size is not None else 1
    max_completion = args.max_length if args.max_length is not None else 8192

    trainer = GRPOTrainer(
        model=args.model,
        reward_funcs=manibench_reward,
        args=GRPOConfig(
            output_dir=args.output_dir,
            hub_model_id=args.hub_model_id if push else None,
            push_to_hub=push,
            per_device_train_batch_size=batch,
            gradient_accumulation_steps=32,
            bf16=True,
            max_prompt_length=2048,
            max_completion_length=max_completion,
            report_to=os.environ.get("REPORT_TO", "none"),
        ),
        train_dataset=ds,
        peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear"),
    )
    trainer.train()
    if push:
        trainer.push_to_hub()
    print("GRPO done.", file=sys.stderr)


if __name__ == "__main__":
    main()
