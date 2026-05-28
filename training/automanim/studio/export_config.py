"""Build Unsloth Studio YAML configs aligned with ``train_gemma4_sft.py`` defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional in PEP 723 scripts
    yaml = None  # type: ignore[assignment]

DEFAULT_MODEL = "google/gemma-4-E2B-it"
DEFAULT_INSTRUCTION_PART = "<|turn>user\n"
DEFAULT_RESPONSE_PART = "<|turn>model\n"


@dataclass
class StudioConfigParams:
    model_name: str = DEFAULT_MODEL
    training_method: str = "qlora"
    max_seq_length: int = 8192
    epochs: float = 5.0
    max_steps: int = 0
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    lr: float = 2e-4
    seed: int = 3407
    eval_split: float = 0.1
    lora_r: int = 8
    lora_alpha: int = 8
    lora_dropout: float = 0.0
    report_to: str = "none"
    instruction_part: str = DEFAULT_INSTRUCTION_PART
    response_part: str = DEFAULT_RESPONSE_PART
    dataset_text_field: str = "text"
    extra: dict[str, Any] = field(default_factory=dict)


def build_studio_config(params: StudioConfigParams | None = None) -> dict[str, Any]:
    """Return a Studio-importable config dict mirroring CLI SFT defaults."""
    p = params or StudioConfigParams()
    warmup = 5
    cfg: dict[str, Any] = {
        "model": {
            "name": p.model_name,
            "method": p.training_method,
            "load_in_4bit": p.training_method == "qlora",
            "max_seq_length": p.max_seq_length,
            "trust_remote_code": False,
        },
        "dataset": {
            "format_type": "auto",
            "text_field": p.dataset_text_field,
            "eval_split": p.eval_split if p.eval_split > 0 else None,
            "train_on_completions": True,
            "instruction_part": p.instruction_part,
            "response_part": p.response_part,
        },
        "training": {
            "max_steps": p.max_steps,
            "num_train_epochs": p.epochs,
            "per_device_train_batch_size": p.batch_size,
            "gradient_accumulation_steps": p.gradient_accumulation_steps,
            "learning_rate": p.lr,
            "warmup_steps": warmup,
            "weight_decay": 0.001,
            "optim": "adamw_8bit",
            "lr_scheduler_type": "linear",
            "seed": p.seed,
            "gradient_checkpointing": "unsloth",
            "save_steps": max(50, warmup),
        },
        "lora": {
            "r": p.lora_r,
            "lora_alpha": p.lora_alpha,
            "lora_dropout": p.lora_dropout,
            "finetune_vision_layers": False,
            "finetune_language_layers": True,
            "finetune_attention_modules": True,
            "finetune_mlp_modules": True,
        },
        "logging": {
            "report_to": p.report_to,
            "logging_steps": 1,
        },
    }
    if p.extra:
        cfg["extra"] = p.extra
    return cfg


def config_to_yaml(config: dict[str, Any]) -> str:
    if yaml is None:
        raise RuntimeError("PyYAML is required to export Studio config (pip install pyyaml)")
    return yaml.safe_dump(config, sort_keys=False, default_flow_style=False)


def write_studio_config(path: Path, params: StudioConfigParams | None = None) -> Path:
    """Write Studio YAML to ``path`` and return the resolved path."""
    text = config_to_yaml(build_studio_config(params))
    out = path.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def params_from_train_args(args: Any) -> StudioConfigParams:
    """Build :class:`StudioConfigParams` from ``train_gemma4_sft`` argparse namespace."""
    max_steps = int(args.max_steps) if getattr(args, "max_steps", -1) > 0 else 0
    return StudioConfigParams(
        model_name=str(args.model_name),
        max_seq_length=int(args.max_seq_length),
        epochs=float(args.epochs),
        max_steps=max_steps,
        batch_size=int(args.batch_size),
        gradient_accumulation_steps=int(args.gradient_accumulation_steps),
        lr=float(args.lr),
        seed=int(args.seed),
        eval_split=float(args.eval_split),
        report_to=str(args.report_to),
    )


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Export Unsloth Studio YAML for AutoManim SFT")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("automanim-gemma4-e2b-qlora.yaml"),
        help="Destination YAML path",
    )
    args = ap.parse_args()
    out = write_studio_config(args.output)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
