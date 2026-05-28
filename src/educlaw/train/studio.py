"""Unsloth Studio launcher."""

from __future__ import annotations

import shutil
import subprocess
import webbrowser

import typer

from educlaw.train.paths import default_sft_jsonl, studio_preset_yaml

INSTALL_URL = "https://unsloth.ai/install.sh"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8888


def find_unsloth_binary() -> str | None:
    return shutil.which("unsloth")


def cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def run_installer() -> None:
    typer.echo(f"Running official Unsloth installer ({INSTALL_URL})...")
    typer.echo("This installs Unsloth Studio and its own Python stack outside EdClaw.")
    result = subprocess.run(
        ["bash", "-c", f"curl -fsSL {INSTALL_URL} | sh"],
        check=False,
    )
    if result.returncode != 0:
        typer.secho("Unsloth install failed.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=result.returncode)
    typer.secho(
        "Install finished. Launch with: educlaw train studio",
        fg=typer.colors.GREEN,
    )


def print_studio_assets() -> None:
    preset = studio_preset_yaml()
    jsonl = default_sft_jsonl()
    typer.echo("")
    typer.echo("Studio assets (upload in the web UI):")
    typer.echo(f"  Preset YAML: {preset}")
    typer.echo(f"  Dataset JSONL: {jsonl}")
    if not jsonl.is_file():
        typer.secho(
            "  (JSONL missing — run: educlaw train dataset automanim)",
            fg=typer.colors.YELLOW,
        )


def launch_studio(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_browser: bool = True,
    install: bool = False,
) -> None:
    if install:
        run_installer()
        return

    binary = find_unsloth_binary()
    if binary is None:
        typer.secho(
            "Unsloth Studio is not installed (``unsloth`` not on PATH).",
            fg=typer.colors.RED,
            err=True,
        )
        typer.echo("")
        typer.echo("Install once with:")
        typer.echo("  educlaw train studio --install")
        typer.echo("")
        typer.echo("Or manually:")
        typer.echo(f"  curl -fsSL {INSTALL_URL} | sh")
        raise typer.Exit(code=1)

    if not cuda_available():
        typer.secho(
            "CUDA not detected — Studio chat/data work; training needs an NVIDIA GPU.",
            fg=typer.colors.YELLOW,
        )

    print_studio_assets()

    url_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{url_host}:{port}"
    typer.echo("")
    typer.echo(f"Starting Unsloth Studio at {url} (Ctrl+C to stop)...")

    if open_browser:
        webbrowser.open(url)

    cmd = [binary, "studio", "-H", host, "-p", str(port)]
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        typer.echo("\nStudio stopped.")
        raise typer.Exit(code=0) from None
