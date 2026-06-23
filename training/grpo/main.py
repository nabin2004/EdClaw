#!/usr/bin/env python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "unsloth @ git+https://github.com/unslothai/unsloth",
#   "unsloth-zoo @ git+https://github.com/unslothai/unsloth-zoo",
#   "trl>=0.28.0",
#   "transformers>=5.5.0",
#   "tokenizers>=0.22.0,<=0.23.0",
#   "datasets>=3.1",
#   "accelerate>=1.1",
#   "bitsandbytes",
#   "huggingface-hub>=0.27",
#   "torch",
# ]
# ///
"""GRPO on Gemma-4-E2B via Unsloth: stacked SFT LoRA + trainable GRPO adapter."""

from __future__ import annotations

import argparse
import os
import sys

from manibench import build_dataset
from rewards import combined_reward

SFT_LORA_PATH = "nabin2004/EduClaw-Gemma4-it"
DEFAULT_OUTPUT = "./grpo_manim_modular"
DEFAULT_MAX_SEQ_LENGTH = 4096


def check_cuda_or_exit() -> None:
    import torch

    if not torch.cuda.is_available():
        print(
            "CUDA is required for Gemma-4 GRPO. Run on an NVIDIA GPU server:\n"
            "  cd training/grpo && uv run main.py --smoke",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _hub_token() -> str | None:
    raw = os.environ.get("HF_TOKEN", "")
    return raw.strip() or None


def load_model(
    sft_lora_path: str,
    *,
    max_seq_length: int = DEFAULT_MAX_SEQ_LENGTH,
    load_in_4bit: bool = False,
):
    from unsloth import FastVisionModel

    model, tokenizer = FastVisionModel.from_pretrained(
        model_name=sft_lora_path,
        max_seq_length=max_seq_length,
        load_in_4bit=load_in_4bit,
        fast_inference=False,
        token=_hub_token(),
    )
    if getattr(tokenizer, "pad_token", None) is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = FastVisionModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0.05,
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )
    return model, tokenizer


def max_prompt_token_length(dataset, tokenizer) -> int:
    lengths = []
    for row in dataset:
        prompt = row["prompt"]
        ids = tokenizer.apply_chat_template(
            prompt,
            add_generation_prompt=True,
            tokenize=True,
        )
        lengths.append(len(ids))
    return max(lengths) if lengths else 0


def resolve_max_completion_length(
    dataset,
    tokenizer,
    *,
    max_seq_length: int,
    cap: int | None = None,
) -> int:
    prompt_len = max_prompt_token_length(dataset, tokenizer)
    computed = max_seq_length - (prompt_len + 1)
    if computed < 64:
        print(
            f"Warning: max_completion_length={computed} is very small "
            f"(prompt tokens={prompt_len}, max_seq_length={max_seq_length}).",
            file=sys.stderr,
        )
        computed = max(computed, 64)
    if cap is not None:
        return min(computed, cap)
    return computed


def make_training_args(
    output_dir: str,
    *,
    max_completion_length: int,
    smoke: bool = False,
    max_steps: int | None = None,
):
    from trl import GRPOConfig

    common = dict(
        output_dir=output_dir,
        optim="adamw_8bit",
        loss_type="bnpo",
        mask_truncated_completions=True,
        use_vllm=False,
        report_to="none",
        bf16=True,
        gradient_checkpointing=True,
        max_completion_length=max_completion_length,
        temperature=0.8,
        top_p=0.9,
        warmup_ratio=0.1,
        weight_decay=0.001,
        lr_scheduler_type="linear",
    )

    if smoke:
        return GRPOConfig(
            **common,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            max_steps=1,
            learning_rate=5e-5,
            logging_steps=1,
            save_strategy="no",
            num_generations=2,
        )

    kwargs: dict = dict(
        **common,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        learning_rate=5e-5,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
        num_generations=4,
    )
    if max_steps is not None:
        kwargs["max_steps"] = max_steps
        kwargs.pop("num_train_epochs", None)
    return GRPOConfig(**kwargs)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="GRPO Manim training (Unsloth Gemma-4 stacked LoRA)",
    )
    ap.add_argument("--sft-lora", default=SFT_LORA_PATH)
    ap.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--max-seq-length",
        type=int,
        default=DEFAULT_MAX_SEQ_LENGTH,
        help="Model context window for Unsloth load (default 4096)",
    )
    ap.add_argument(
        "--max-completion-length",
        type=int,
        default=None,
        help="Cap completion tokens (default: max_seq_length - longest prompt)",
    )
    ap.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="Load SFT checkpoint in 4-bit (OOM fallback; match 4-bit SFT)",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="One GRPO step, small completions (GPU smoke test)",
    )
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument(
        "--no-render",
        action="store_true",
        help="Disable manim subprocess in executability reward (default: heuristic only)",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    if args.no_render:
        os.environ["MANIBENCH_GRPO_RENDER"] = "0"
    elif "MANIBENCH_GRPO_RENDER" not in os.environ:
        os.environ["MANIBENCH_GRPO_RENDER"] = "0"

    check_cuda_or_exit()

    # Unsloth must be imported before trl so GRPOTrainer is patched.
    import unsloth  # noqa: F401
    from trl import GRPOTrainer

    dataset = build_dataset()
    model, tokenizer = load_model(
        args.sft_lora,
        max_seq_length=args.max_seq_length,
        load_in_4bit=args.load_in_4bit,
    )

    completion_cap = 256 if args.smoke else args.max_completion_length
    max_completion_length = resolve_max_completion_length(
        dataset,
        tokenizer,
        max_seq_length=args.max_seq_length,
        cap=completion_cap,
    )
    print(f"max_completion_length={max_completion_length}", flush=True)

    training_args = make_training_args(
        args.output_dir,
        max_completion_length=max_completion_length,
        smoke=args.smoke,
        max_steps=args.max_steps,
    )

    trainer = GRPOTrainer(
        model=model,
        args=training_args,
        reward_funcs=combined_reward,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    trainer.train()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"GRPO LoRA saved to {args.output_dir}")


if __name__ == "__main__":
    main()
