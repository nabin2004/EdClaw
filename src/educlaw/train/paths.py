"""Repo paths for training scripts."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    dev_root = Path(__file__).resolve().parents[3]
    if (dev_root / "training" / "automanim").is_dir():
        return dev_root

    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "training" / "automanim").is_dir() or (parent / "pyproject.toml").is_file():
            return parent

    return dev_root


def automanim_training_dir() -> Path:
    return repo_root() / "training" / "automanim"


def build_sft_jsonl_script() -> Path:
    return automanim_training_dir() / "scripts" / "build_sft_jsonl.py"


def train_gemma4_sft_script() -> Path:
    return automanim_training_dir() / "scripts" / "train_gemma4_sft.py"


def default_dataset_dir() -> Path:
    return repo_root() / "src" / "educlaw" / "automanim" / "dataset"


def default_sft_jsonl() -> Path:
    return repo_root() / "src" / "educlaw" / "automanim" / "sft_dataset.jsonl"


def studio_preset_yaml() -> Path:
    return automanim_training_dir() / "studio" / "automanim-gemma4-e2b-qlora.yaml"


def default_lora_output_dir() -> Path:
    return repo_root() / "out" / "automanim-gemma4-e2b-lora"
