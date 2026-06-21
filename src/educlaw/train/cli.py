"""``educlaw train`` Typer commands."""

from __future__ import annotations

import os
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


@dataset_typer.command("push-hf")
def dataset_push_hf(
    repo_id: Annotated[
        str,
        typer.Argument(help="HuggingFace dataset repo, e.g. myuser/educlaw-lectures"),
    ],
    ir_root: Annotated[
        Path | None,
        typer.Option("--ir-root", "-r", help="IR content root (default: content/ir/)"),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", help="HF token (falls back to $HF_TOKEN)"),
    ] = None,
    private: Annotated[
        bool,
        typer.Option("--private/--public", help="Create as private or public dataset"),
    ] = True,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Dataset format: sharegpt (Unsloth default) or alpaca"),
    ] = "sharegpt",
    test_size: Annotated[
        float,
        typer.Option("--test-size", help="Fraction held out as test split (0 = train only)"),
    ] = 0.0,
    include_code: Annotated[
        bool,
        typer.Option(
            "--include-code/--no-include-code",
            help="Also push Manim scene.py code-generation rows (default: on)",
        ),
    ] = True,
) -> None:
    """Push IR lecture .md files (and Manim scene.py code) to HuggingFace as a fine-tuning dataset.

    Defaults to ShareGPT format, which Unsloth Studio accepts directly.
    Set $HF_TOKEN or pass --token to authenticate.

    Example:
        educlaw train dataset push-hf myuser/educlaw-lectures --format sharegpt
    """
    from educlaw.train.hf_push import FormatType, push_to_hub

    resolved_fmt: FormatType = "sharegpt" if fmt.lower().startswith("s") else "alpaca"

    hf_token = token or os.environ.get("HF_TOKEN")
    if not hf_token:
        typer.secho(
            "No HF token found. Set $HF_TOKEN or pass --token. "
            "Get yours at https://huggingface.co/settings/tokens",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    root = (ir_root or Path("content/ir")).expanduser().resolve()
    if not root.is_dir():
        typer.secho(f"IR root not found: {root}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Scanning {root} for lecture files...")

    try:
        url = push_to_hub(
            root,
            repo_id,
            token=hf_token,
            private=private,
            fmt=resolved_fmt,
            test_size=test_size,
            include_code=include_code,
        )
    except ImportError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    except Exception as e:  # noqa: BLE001
        typer.secho(f"Push failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

    visibility = "private" if private else "public"
    code_note = " + Manim scenes" if include_code else ""
    typer.secho(
        f"Dataset pushed ({visibility}, {resolved_fmt} format{code_note}): {url}",
        fg=typer.colors.GREEN,
    )


@dataset_typer.command("ir-manim")
def dataset_ir_manim(
    ir_root: Annotated[
        Path | None,
        typer.Option("--ir-root", "-r", help="IR content root (default: content/ir/)"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(help="Output JSONL (default: src/educlaw/automanim/ir_sft_dataset.jsonl)"),
    ] = None,
    write_srt: Annotated[
        bool,
        typer.Option("--write-srt/--no-write-srt", help="Write subtitles.srt alongside each scene.py"),
    ] = False,
) -> None:
    """Build Gemma-style JSONL from IR series scene.py files for Manim code generation SFT."""
    from educlaw.train.paths import repo_root

    root = (ir_root or Path("content/ir")).expanduser().resolve()
    if not root.is_dir():
        typer.secho(f"IR root not found: {root}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    out = (output or (repo_root() / "src" / "educlaw" / "automanim" / "ir_sft_dataset.jsonl")).expanduser().resolve()

    script = repo_root() / "training" / "automanim" / "scripts" / "build_ir_sft_jsonl.py"
    if not script.is_file():
        typer.secho(f"Script not found: {script}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    import subprocess
    import shutil
    import sys

    runner = ["uv", "run"] if shutil.which("uv") else [sys.executable]
    cmd = [*runner, str(script), "--ir-root", str(root), "--output", str(out)]
    if write_srt:
        cmd.append("--write-srt")

    typer.echo(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(repo_root()), check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    typer.secho(f"Wrote {out}", fg=typer.colors.GREEN)


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
