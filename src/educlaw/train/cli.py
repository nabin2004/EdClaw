"""``educlaw train`` Typer commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from educlaw.train import automanim as automanim_train
from educlaw.train import studio as studio_launcher

train_typer = typer.Typer(help="Local fine-tuning (AutoManim + Unsloth).", no_args_is_help=True)

dataset_typer = typer.Typer(help="Build training datasets.")
train_typer.add_typer(dataset_typer, name="dataset")

sft_typer = typer.Typer(help="Run SFT training jobs.")
train_typer.add_typer(sft_typer, name="sft")


@dataset_typer.command("automanim")
def dataset_automanim(
    dataset_dir: Annotated[
        Path | None,
        typer.Option(help="Episode root (default: bundled automanim/dataset)"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(help="Output JSONL (default: automanim/sft_dataset.jsonl)"),
    ] = None,
) -> None:
    """Build Gemma-style JSONL from AutoManim episode metadata."""
    automanim_train.build_dataset(dataset_dir=dataset_dir, output=output)


@sft_typer.command("automanim")
def sft_automanim(
    train_jsonl: Annotated[
        Path | None,
        typer.Option(help="Training JSONL path"),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option(help="LoRA output directory"),
    ] = None,
    max_steps: Annotated[
        int | None,
        typer.Option(help="Smoke run step limit (e.g. 10); omit for full epochs"),
    ] = None,
    epochs: Annotated[float | None, typer.Option(help="Training epochs")] = None,
) -> None:
    """LoRA SFT on AutoManim traces (Unsloth Core + CUDA)."""
    extra: list[str] = []
    if max_steps is not None:
        extra.extend(["--max-steps", str(max_steps)])
    if epochs is not None:
        extra.extend(["--epochs", str(epochs)])
    automanim_train.run_sft(
        train_jsonl=train_jsonl,
        output_dir=output_dir,
        extra_args=extra or None,
    )


@train_typer.command("studio")
def train_studio(
    host: Annotated[str, typer.Option(help="Bind host for Studio server")] = "0.0.0.0",
    port: Annotated[int, typer.Option(help="Bind port")] = 8888,
    no_browser: Annotated[bool, typer.Option(help="Do not open a browser tab")] = False,
    install: Annotated[
        bool,
        typer.Option("--install", help="Run the official Unsloth installer"),
    ] = False,
) -> None:
    """Launch Unsloth Studio (local no-code training UI)."""
    studio_launcher.launch_studio(
        host=host,
        port=port,
        open_browser=not no_browser,
        install=install,
    )
