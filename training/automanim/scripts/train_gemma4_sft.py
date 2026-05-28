#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "unsloth",
#   "datasets>=3.1",
#   "trl>=0.12",
#   "accelerate>=1.2",
#   "wandb>=0.18",
# ]
# ///
"""
Fine-tune ``google/gemma-4-E2B-it`` on pre-rendered AutoManim JSONL (``{"text": ...}``).

Requires CUDA. Prefer ``HF_TOKEN`` in the environment when using ``--hub-model-id``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def check_cuda_or_exit() -> None:
    import torch

    if not torch.cuda.is_available():
        print(
            "CUDA is required. Run on the college GPU host or HF Jobs.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def parse_args():
    env_report = os.environ.get("REPORT_TO", "none")
    env_lr = os.environ.get("AUTOMANIM_SFT_LR")
    lr_default = float(env_lr) if env_lr else 2e-4

    parser = argparse.ArgumentParser(
        description="Unsloth LoRA SFT on AutoManim Gemma-rendered JSONL",
    )
    parser.add_argument(
        "--train-jsonl",
        type=Path,
        default=None,
        help='Training JSONL where each row is {"text": "…"}',
    )
    parser.add_argument(
        "--model-name",
        default="google/gemma-4-E2B-it",
        help="Base Hugging Face model id",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=8192,
        help="Trainer max packed length (sequences may truncate; lower if OOM)",
    )
    parser.add_argument(
        "--epochs",
        type=float,
        default=5.0,
        help="Ignored when --max-steps > 0",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=-1,
        help="Smoke run (e.g. 10); use -1 to train by epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Per-device train batch size",
    )
    parser.add_argument(
        "--gradient-accumulation",
        type=int,
        default=4,
        dest="gradient_accumulation_steps",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=lr_default,
    )
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument(
        "--eval-split",
        type=float,
        default=0.1,
        help="Train/test split fraction; set to 0 to disable eval split",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("out/automanim-gemma4-e2b-lora"),
        help="Checkpoints / LoRA artifact directory",
    )
    parser.add_argument(
        "--device-map",
        default="auto",
        help="passed to FastModel.from_pretrained (e.g. auto, sequential)",
    )
    parser.add_argument(
        "--hf-token-env",
        default="HF_TOKEN",
        help="Env var holding read token when downloading gated models",
    )
    parser.add_argument(
        "--report-to",
        default=env_report,
        choices=["none", "wandb", "tensorboard"],
        help="Logging backends (defaults to REPORT_TO env or none)",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Do not upload to Hugging Face Hub",
    )
    parser.add_argument(
        "--hub-model-id",
        default=None,
        help="HF repo id to push adapters (requires HF_TOKEN)",
    )
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument(
        "--export-studio-config",
        type=Path,
        default=None,
        help="Write Unsloth Studio YAML matching these args and exit (no training)",
    )
    return parser.parse_args()


def _hub_token(tok_env: str) -> str | None:
    raw = os.environ.get(tok_env) or ""
    cleaned = raw.strip()
    return cleaned or None


def _export_studio_config(args) -> None:
    here = Path(__file__).resolve().parent
    studio_dir = here.parent / "studio"
    sys.path.insert(0, str(studio_dir))
    from export_config import params_from_train_args, write_studio_config  # noqa: WPS433

    params = params_from_train_args(args)
    out = write_studio_config(args.export_studio_config, params)
    print("Wrote Studio config to", out.resolve(), flush=True)


def main() -> None:
    args = parse_args()
    if args.export_studio_config is not None:
        _export_studio_config(args)
        return

    if args.train_jsonl is None:
        raise SystemExit("--train-jsonl is required for training")

    check_cuda_or_exit()

    token = _hub_token(args.hf_token_env)

    rows: list[dict] = []
    with args.train_jsonl.open(encoding="utf-8") as f_in:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if not rows:
        raise SystemExit("No rows loaded from JSONL")

    push = bool(args.hub_model_id) and not args.no_push

    report_to = args.report_to  # transformers accepts "none" | "wandb" | ...

    import torch
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastModel
    from unsloth.chat_templates import train_on_responses_only

    dataset = Dataset.from_list(rows)

    hub_token_read = token

    hub_token_push = token if push else None
    if push and not hub_token_push:
        print("--hub-model-id requested but HF token missing.", file=sys.stderr)
        raise SystemExit(2)

    load_kwargs = {
        "model_name": args.model_name,
        "dtype": None,
        "max_seq_length": args.max_seq_length,
        "load_in_4bit": True,
        "full_finetuning": False,
        "token": hub_token_read,
        "device_map": args.device_map,
    }

    print("Loading model + tokenizer...", flush=True)
    model, tokenizer = FastModel.from_pretrained(**load_kwargs)

    peft_config = {
        "finetune_vision_layers": False,
        "finetune_language_layers": True,
        "finetune_attention_modules": True,
        "finetune_mlp_modules": True,
        "r": 8,
        "lora_alpha": 8,
        "lora_dropout": 0,
        "bias": "none",
        "random_state": args.seed,
    }
    print("Applying PEFT adapters...", flush=True)
    model = FastModel.get_peft_model(model, **peft_config)

    eval_dataset = None
    eval_kwargs: dict = {}
    if args.eval_split and args.eval_split > 0:
        split = dataset.train_test_split(test_size=args.eval_split, seed=args.seed)
        dataset = split["train"]
        eval_dataset = split["test"]
        print(
            "Split:",
            len(dataset),
            "train /",
            len(eval_dataset) if eval_dataset is not None else 0,
            "eval",
            flush=True,
        )
        eval_es = max(2, 5)
        if args.max_steps > 0:
            eval_es = max(2, min(eval_es, args.max_steps // 2))
        eval_kwargs = {
            "eval_strategy": "steps",
            "eval_steps": eval_es,
        }

    warmup_steps = 5 if len(dataset) >= 20 else max(1, len(dataset) // 4)

    max_steps_kw = {}
    epochs_kw = {"num_train_epochs": float(args.epochs)}
    if args.max_steps > 0:
        max_steps_kw = {"max_steps": int(args.max_steps)}
        epochs_kw = {"num_train_epochs": 1}

    bf16_allowed = torch.cuda.is_bf16_supported()
    fp16_allowed = torch.cuda.is_fp16_supported() and not bf16_allowed

    args.output_dir.mkdir(parents=True, exist_ok=True)

    cfg = SFTConfig(
        output_dir=str(args.output_dir),
        dataset_text_field="text",
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_steps=warmup_steps,
        logging_steps=max(1, args.logging_steps),
        learning_rate=args.lr,
        optim="adamw_8bit",
        weight_decay=0.001,
        lr_scheduler_type="linear",
        seed=args.seed,
        report_to=report_to,
        bf16=bf16_allowed,
        fp16=fp16_allowed,
        gradient_checkpointing=True,
        max_length=args.max_seq_length,
        save_steps=max(50, warmup_steps),
        push_to_hub=False,
        **epochs_kw,
        **max_steps_kw,
        **eval_kwargs,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        args=cfg,
    )

    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|turn>user\n",
        response_part="<|turn>model\n",
    )

    print("Training...", flush=True)
    trainer.train()

    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    if push and args.hub_model_id:
        trainer.model.push_to_hub(args.hub_model_id, token=hub_token_push)
        tokenizer.push_to_hub(args.hub_model_id, token=hub_token_push)
        print("Pushed adapters to Hugging Face:", args.hub_model_id, flush=True)
    print("Saved to", args.output_dir.resolve(), flush=True)


if __name__ == "__main__":
    main()
