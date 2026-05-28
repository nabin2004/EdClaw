"""AutoManim SFT training wrappers."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import typer

from educlaw.train.paths import (
    build_sft_jsonl_script,
    default_dataset_dir,
    default_lora_output_dir,
    default_sft_jsonl,
    repo_root,
    train_gemma4_sft_script,
)


def _runner() -> list[str]:
    if shutil.which("uv"):
        return ["uv", "run"]
    return [sys.executable]


def _run_script(script: Path, extra_args: list[str]) -> None:
    root = repo_root()
    if not script.is_file():
        typer.secho(f"Script not found: {script}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    cmd = [*_runner(), str(script), *extra_args]
    typer.echo(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(root), check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


def check_cuda_or_exit() -> None:
    try:
        import torch
    except ImportError:
        typer.secho(
            "PyTorch not installed. Install with: pip install -e \".[automanim-training]\"",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from None
    if not torch.cuda.is_available():
        typer.secho(
            "CUDA is required for AutoManim SFT. Use a GPU host or Unsloth Studio.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def build_dataset(
    dataset_dir: Path | None = None,
    output: Path | None = None,
    extra_args: list[str] | None = None,
) -> None:
    ds = (dataset_dir or default_dataset_dir()).expanduser().resolve()
    out = (output or default_sft_jsonl()).expanduser().resolve()
    args = [
        "--dataset-dir",
        str(ds),
        "--output",
        str(out),
        *(extra_args or []),
    ]
    _run_script(build_sft_jsonl_script(), args)
    typer.secho(f"Wrote {out}", fg=typer.colors.GREEN)


def run_sft(
    train_jsonl: Path | None = None,
    output_dir: Path | None = None,
    extra_args: list[str] | None = None,
    *,
    skip_cuda_check: bool = False,
) -> None:
    if not skip_cuda_check:
        check_cuda_or_exit()
    jsonl = (train_jsonl or default_sft_jsonl()).expanduser().resolve()
    if not jsonl.is_file():
        typer.secho(
            f"Training JSONL not found: {jsonl}\nRun: educlaw train dataset automanim",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    out = (output_dir or default_lora_output_dir()).expanduser().resolve()
    args = [
        "--train-jsonl",
        str(jsonl),
        "--output-dir",
        str(out),
        *(extra_args or []),
    ]
    _run_script(train_gemma4_sft_script(), args)
