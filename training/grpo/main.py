#!/usr/bin/env python
"""GRPO on Gemma-4-E2B via Unsloth: stacked SFT LoRA + trainable GRPO adapter."""

from __future__ import annotations

import argparse
import os
import sys

from manibench import build_dataset
from rewards import DEFAULT_LENGTH_PENALTY_COEF, combined_reward

SFT_LORA_PATH = "nabin2004/EduClaw-Gemma4-it"
DEFAULT_BASE_MODEL = "google/gemma-4-E2B-it"
DEFAULT_OUTPUT = "./grpo_manim_modular"
DEFAULT_MAX_SEQ_LENGTH = 2048
DEFAULT_MAX_COMPLETION_LENGTH = 512
DEFAULT_NUM_GENERATIONS = 4
DEFAULT_LEARNING_RATE = 1e-4
DEFAULT_BETA = 0.001
GRPO_ADAPTER = "grpo"


def _hub_token() -> str | None:
    raw = os.environ.get("HF_TOKEN", "")
    return raw.strip() or None


def _base_model_for_adapter(adapter_path: str, fallback: str) -> str:
    import json
    from pathlib import Path

    local = Path(adapter_path)
    if local.is_dir():
        cfg_path = local / "adapter_config.json"
        if cfg_path.is_file():
            with cfg_path.open(encoding="utf-8") as f:
                return json.load(f).get("base_model_name_or_path", fallback)
        return fallback

    from huggingface_hub import hf_hub_download

    cfg_path = Path(
        hf_hub_download(
            adapter_path,
            "adapter_config.json",
            token=_hub_token(),
        ),
    )
    with cfg_path.open(encoding="utf-8") as f:
        return json.load(f).get("base_model_name_or_path", fallback)


def check_cuda_or_exit() -> None:
    import torch

    if not torch.cuda.is_available():
        print(
            "CUDA is required for Gemma-4 GRPO. Run on an NVIDIA GPU server:\n"
            "  cd training/grpo && uv sync && uv run python main.py --smoke",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _grpo_lora_config():
    from peft import LoraConfig, TaskType

    return LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )


def load_model(
    sft_lora_path: str,
    *,
    base_model: str | None = None,
    max_seq_length: int = DEFAULT_MAX_SEQ_LENGTH,
    load_in_4bit: bool = True,
    grpo_only: bool = False,
):
    from peft import PeftModel
    from unsloth import FastVisionModel

    if grpo_only:
        base = base_model or DEFAULT_BASE_MODEL
    else:
        base = base_model or _base_model_for_adapter(sft_lora_path, DEFAULT_BASE_MODEL)
    token = _hub_token()

    model, tokenizer = FastVisionModel.from_pretrained(
        model_name=base,
        max_seq_length=max_seq_length,
        load_in_4bit=load_in_4bit,
        fast_inference=False,
        token=token,
    )
    if getattr(tokenizer, "pad_token", None) is None:
        tokenizer.pad_token = tokenizer.eos_token

    grpo_config = _grpo_lora_config()

    if grpo_only:
        model = PeftModel(model, grpo_config, adapter_name=GRPO_ADAPTER)
    else:
        # Frozen SFT adapter — Unsloth cannot call get_peft_model() on a model that
        # already has LoRA (load base first, then stack adapters via PEFT).
        model = PeftModel.from_pretrained(
            model,
            sft_lora_path,
            adapter_name="sft",
            token=token,
        )
        for name, param in model.named_parameters():
            if "sft" in name:
                param.requires_grad = False
        model.add_adapter(GRPO_ADAPTER, grpo_config)

    model.set_adapter(GRPO_ADAPTER)
    model.train()
    return model, tokenizer


def _prompt_token_len(tokenizer, prompt: list) -> int:
    ids = tokenizer.apply_chat_template(
        prompt,
        add_generation_prompt=True,
        tokenize=True,
    )
    return len(ids)


def truncate_dataset_prompts(dataset, tokenizer, max_prompt_length: int):
    from datasets import Dataset

    from manibench import format_user_prompt

    rows = []
    for row in dataset:
        text = row["prompt"][0]["content"][0]["text"]
        prompt = format_user_prompt(text)
        while _prompt_token_len(tokenizer, prompt) > max_prompt_length and len(text) > 64:
            text = text[: int(len(text) * 0.9)]
            prompt = format_user_prompt(text)
        if _prompt_token_len(tokenizer, prompt) > max_prompt_length:
            print(
                f"Warning: prompt still {_prompt_token_len(tokenizer, prompt)} tokens "
                f"(limit {max_prompt_length}); problem_id={row.get('problem_id')}",
                file=sys.stderr,
            )
        rows.append({**row, "prompt": prompt})
    return Dataset.from_list(rows)


def max_prompt_token_length(dataset, tokenizer) -> int:
    lengths = [_prompt_token_len(tokenizer, row["prompt"]) for row in dataset]
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
    num_generations: int,
    smoke: bool = False,
    max_steps: int | None = None,
):
    from trl import GRPOConfig

    # Unsloth/TRL: batch size * grad_accum must be divisible by num_generations.
    common = dict(
        output_dir=output_dir,
        optim="paged_adamw_8bit",
        loss_type="bnpo",
        mask_truncated_completions=False,
        use_vllm=False,
        report_to="none",
        bf16=True,
        gradient_checkpointing=True,
        max_completion_length=max_completion_length,
        num_generations=num_generations,
        per_device_train_batch_size=num_generations,
        gradient_accumulation_steps=1,
        temperature=1.0,
        top_p=0.9,
        beta=DEFAULT_BETA,
        warmup_ratio=0.1,
        weight_decay=0.001,
        lr_scheduler_type="linear",
    )

    if smoke:
        return GRPOConfig(
            **common,
            max_steps=1,
            learning_rate=DEFAULT_LEARNING_RATE,
            logging_steps=1,
            save_strategy="no",
        )

    kwargs: dict = dict(
        **common,
        num_train_epochs=3,
        learning_rate=DEFAULT_LEARNING_RATE,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
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
    ap.add_argument(
        "--base-model",
        default=None,
        help="Override base model (default: read from SFT adapter_config.json)",
    )
    ap.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--max-seq-length",
        type=int,
        default=DEFAULT_MAX_SEQ_LENGTH,
        help="Model context window for Unsloth load (default 2048; lower if OOM)",
    )
    ap.add_argument(
        "--max-prompt-length",
        type=int,
        default=1024,
        help="Truncate prompts in the dataset (TRL 0.29+ has no max_prompt_length)",
    )
    ap.add_argument(
        "--max-completion-length",
        type=int,
        default=DEFAULT_MAX_COMPLETION_LENGTH,
        help="Cap completion tokens (default 512)",
    )
    ap.add_argument(
        "--num-generations",
        type=int,
        default=DEFAULT_NUM_GENERATIONS,
        help="GRPO samples per prompt (default 4; lower saves VRAM)",
    )
    ap.add_argument(
        "--full-precision",
        action="store_true",
        help="Load base in 16-bit instead of 4-bit (needs >16GB VRAM)",
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
    ap.add_argument(
        "--render",
        action="store_true",
        help="Enable manim subprocess in executability reward (slow; Phase 2 training)",
    )
    ap.add_argument(
        "--grpo-only",
        action="store_true",
        help="Train GRPO LoRA on base model only (skip frozen SFT adapter stack)",
    )
    ap.add_argument(
        "--reward-debug",
        action="store_true",
        help="Print per-step reward component stats to stderr",
    )
    ap.add_argument(
        "--length-penalty",
        type=float,
        default=DEFAULT_LENGTH_PENALTY_COEF,
        help=f"Length penalty coefficient (default {DEFAULT_LENGTH_PENALTY_COEF})",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    if args.render:
        os.environ["MANIBENCH_GRPO_RENDER"] = "1"
    elif args.no_render:
        os.environ["MANIBENCH_GRPO_RENDER"] = "0"
    elif "MANIBENCH_GRPO_RENDER" not in os.environ:
        os.environ["MANIBENCH_GRPO_RENDER"] = "0"

    if args.reward_debug:
        os.environ["MANIBENCH_GRPO_REWARD_DEBUG"] = "1"

    os.environ["MANIBENCH_LENGTH_PENALTY_COEF"] = str(args.length_penalty)

    check_cuda_or_exit()

    # Unsloth must be imported before trl so GRPOTrainer is patched.
    import unsloth  # noqa: F401
    from trl import GRPOTrainer

    model, tokenizer = load_model(
        args.sft_lora,
        base_model=args.base_model,
        max_seq_length=args.max_seq_length,
        load_in_4bit=not args.full_precision,
        grpo_only=args.grpo_only,
    )

    dataset = truncate_dataset_prompts(
        build_dataset(),
        tokenizer,
        args.max_prompt_length,
    )

    completion_cap = 256 if args.smoke else args.max_completion_length
    max_completion_length = resolve_max_completion_length(
        dataset,
        tokenizer,
        max_seq_length=args.max_seq_length,
        cap=completion_cap,
    )
    os.environ["MANIBENCH_MAX_COMPLETION_LENGTH"] = str(max_completion_length)

    print(
        f"VRAM-friendly settings: load_in_4bit={not args.full_precision}, "
        f"grpo_only={args.grpo_only}, "
        f"max_prompt_length={args.max_prompt_length}, "
        f"max_completion_length={max_completion_length}, "
        f"num_generations={args.num_generations}, "
        f"length_penalty={args.length_penalty}, "
        f"render={os.environ.get('MANIBENCH_GRPO_RENDER', '0')}",
        flush=True,
    )

    training_args = make_training_args(
        args.output_dir,
        max_completion_length=max_completion_length,
        num_generations=args.num_generations,
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
    model.save_pretrained(args.output_dir, adapter_name=GRPO_ADAPTER)
    tokenizer.save_pretrained(args.output_dir)
    print(f"GRPO LoRA saved to {args.output_dir}")


if __name__ == "__main__":
    main()
