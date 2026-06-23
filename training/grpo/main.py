#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "transformers>=5.5.0",
#   "peft>=0.19",
#   "trl>=0.23",
#   "datasets>=3.1",
#   "accelerate>=1.1",
#   "huggingface-hub>=0.27",
#   "torch",
# ]
# ///
"""GRPO on Gemma-4-E2B with frozen SFT LoRA + trainable Manim adapter."""

from __future__ import annotations

import argparse
import os
import sys

from peft import LoraConfig, PeftModel, TaskType
from transformers import AutoModelForCausalLM, AutoProcessor
from trl import GRPOConfig, GRPOTrainer

from manibench import build_dataset
from rewards import combined_reward

BASE_MODEL    = "google/gemma-4-E2B-it"
SFT_LORA_PATH = "nabin2004/EduClaw-Gemma4-it"
DEFAULT_OUTPUT = "./grpo_manim_modular"


def check_cuda_or_exit() -> None:
    import torch

    if not torch.cuda.is_available():
        print(
            "CUDA is required for Gemma-4 GRPO. Run on an NVIDIA GPU server:\n"
            "  cd training/grpo && uv run main.py --smoke",
            file=sys.stderr,
        )
        raise SystemExit(1)


def load_model(base_model: str, sft_lora_path: str):
    processor = AutoProcessor.from_pretrained(
        base_model,
        padding_side="left",
        trust_remote_code=True,
    )
    tokenizer = getattr(processor, "tokenizer", processor)
    if getattr(tokenizer, "pad_token", None) is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )

    # Frozen SFT adapter — kept in memory but not trained
    model = PeftModel.from_pretrained(model, sft_lora_path, adapter_name="sft")
    for name, param in model.named_parameters():
        if "sft" in name:
            param.requires_grad = False

    # Trainable Manim GRPO adapter
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model.add_adapter("manim", lora_config)
    model.set_adapter("manim")
    model.train()

    return model, processor


def make_training_args(
    output_dir: str,
    *,
    smoke: bool = False,
    max_steps: int | None = None,
) -> GRPOConfig:
    if smoke:
        return GRPOConfig(
            output_dir=output_dir,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            max_steps=1,
            learning_rate=1e-6,
            logging_steps=1,
            save_strategy="no",
            bf16=True,
            gradient_checkpointing=True,
            max_completion_length=256,
            num_generations=2,
            temperature=0.8,
            top_p=0.9,
            use_vllm=False,
            beta=0.0,
            loss_type="dapo",
            scale_rewards="group",
        )

    kwargs: dict = dict(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        learning_rate=1e-6,
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
        bf16=True,
        gradient_checkpointing=True,
        max_completion_length=1024,
        num_generations=4,
        temperature=0.8,
        top_p=0.9,
        use_vllm=False,
        beta=0.0,
        loss_type="dapo",
        scale_rewards="group",
    )
    if max_steps is not None:
        kwargs["max_steps"] = max_steps
        kwargs.pop("num_train_epochs", None)
    return GRPOConfig(**kwargs)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="GRPO Manim training (Gemma-4 dual LoRA)")
    ap.add_argument("--base-model", default=BASE_MODEL)
    ap.add_argument("--sft-lora", default=SFT_LORA_PATH)
    ap.add_argument("--output-dir", default=DEFAULT_OUTPUT)
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

    dataset = build_dataset()
    model, processor = load_model(args.base_model, args.sft_lora)
    training_args = make_training_args(
        args.output_dir,
        smoke=args.smoke,
        max_steps=args.max_steps,
    )

    trainer = GRPOTrainer(
        model=model,
        args=training_args,
        reward_funcs=combined_reward,
        train_dataset=dataset,
        processing_class=processor,
    )

    trainer.train()
    model.save_pretrained(args.output_dir, adapter_name="manim")
    print(f"Manim GRPO LoRA saved to {args.output_dir}")


if __name__ == "__main__":
    main()
