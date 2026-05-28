"""Tests for ``educlaw train`` and Studio config export."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from educlaw.cli import app

runner = CliRunner()


def _studio_export_module():
    root = Path(__file__).resolve().parents[1]
    studio_dir = root / "training" / "automanim" / "studio"
    sys.path.insert(0, str(studio_dir))
    import export_config  # noqa: WPS433

    return export_config


def test_train_dataset_automanim_help() -> None:
    result = runner.invoke(app, ["train", "dataset", "automanim", "--help"])
    assert result.exit_code == 0
    assert "Build Gemma-style JSONL" in result.stdout


def test_train_studio_help() -> None:
    result = runner.invoke(app, ["train", "studio", "--help"])
    assert result.exit_code == 0
    assert "Unsloth Studio" in result.stdout
    assert "--install" in result.stdout


def test_studio_config_export_keys() -> None:
    export_config = _studio_export_module()
    cfg = export_config.build_studio_config()
    assert cfg["model"]["name"] == "google/gemma-4-E2B-it"
    assert cfg["lora"]["r"] == 8
    assert "training" in cfg
    assert "logging" in cfg
    assert cfg["dataset"]["train_on_completions"] is True
    assert cfg["dataset"]["instruction_part"] == "<|turn>user\n"


def test_studio_config_write_yaml(tmp_path: Path) -> None:
    export_config = _studio_export_module()
    out = tmp_path / "preset.yaml"
    export_config.write_studio_config(out)
    text = out.read_text(encoding="utf-8")
    assert "google/gemma-4-E2B-it" in text
    assert "lora:" in text
    assert "r: 8" in text


def test_studio_missing_binary_exits() -> None:
    with patch("educlaw.train.studio.find_unsloth_binary", return_value=None):
        with patch("educlaw.train.studio.cuda_available", return_value=True):
            result = runner.invoke(app, ["train", "studio", "--no-browser"])
    assert result.exit_code == 1
    combined = result.output
    assert "not on PATH" in combined or "not installed" in combined
