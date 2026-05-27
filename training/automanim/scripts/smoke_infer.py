#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "unsloth",
# ]
# ///
"""
Load a saved LoRA directory and run one Gemma-4 chat generation (CUDA required).

Example::

  uv run training/automanim/scripts/smoke_infer.py \\
    --adapter-dir out/automanim-gemma4-e2b-lora \\
    --prompt "Animate SGD on a loss surface with gradient arrows."
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    import torch
    from transformers import TextStreamer
    from unsloth import FastModel
    from unsloth.chat_templates import get_chat_template

    ap = argparse.ArgumentParser(description="Smoke-test Gemma-4 LoRA inference")
    ap.add_argument(
        "--adapter-dir",
        type=Path,
        required=True,
        help="Directory with LoRA weights (trainer output)",
    )
    ap.add_argument(
        "--prompt",
        default=(
            "Continue the animation idea: visualize gradient descent stepping "
            "down a quadratic loss curve."
        ),
    )
    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--max-seq-length", type=int, default=8192)
    ap.add_argument(
        "--device",
        default="cuda",
        help="Device for tensors (default cuda)",
    )
    args = ap.parse_args()

    if not torch.cuda.is_available():
        print("CUDA is required.", file=sys.stderr)
        raise SystemExit(1)

    print("Loading adapter from", args.adapter_dir.resolve(), flush=True)
    model, tokenizer = FastModel.from_pretrained(
        model_name=str(args.adapter_dir),
        dtype=None,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
        full_finetuning=False,
    )
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="gemma-4",
    )

    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": args.prompt}],
        }
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
        tokenize=True,
        return_dict=True,
    ).to(args.device)

    streamer = TextStreamer(tokenizer, skip_prompt=True)
    _ = model.generate(
        **inputs,
        max_new_tokens=args.max_new_tokens,
        temperature=1.0,
        top_p=0.95,
        top_k=64,
        streamer=streamer,
    )


if __name__ == "__main__":
    main()
