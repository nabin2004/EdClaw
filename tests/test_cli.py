"""Tests for the top-level `educlaw` CLI entrypoint."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from typer.testing import CliRunner

from educlaw.cli import app, main

runner = CliRunner()


def test_educlaw_help_stays_standard() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Run the FastAPI gateway" in result.stdout
    assert "Course site generation and catalog" in result.stdout


def test_main_plays_intro_for_bare_tty_invocation(monkeypatch) -> None:
    intro = Mock(return_value=True)
    app_call = Mock()
    echo = Mock()
    monkeypatch.setattr("educlaw.cli._play_intro", intro)
    monkeypatch.setattr("educlaw.cli.app", app_call)
    monkeypatch.setattr("educlaw.cli.typer.echo", echo)
    monkeypatch.setattr("educlaw.cli.sys.argv", ["educlaw"])
    monkeypatch.setattr("educlaw.cli.sys.stdout", SimpleNamespace(isatty=lambda: True))

    main()

    intro.assert_called_once()
    echo.assert_called_once()
    app_call.assert_called_once()


def test_main_skips_intro_when_not_tty(monkeypatch) -> None:
    intro = Mock(return_value=True)
    app_call = Mock()
    monkeypatch.setattr("educlaw.cli._play_intro", intro)
    monkeypatch.setattr("educlaw.cli.app", app_call)
    monkeypatch.setattr("educlaw.cli.sys.argv", ["educlaw"])
    monkeypatch.setattr("educlaw.cli.sys.stdout", SimpleNamespace(isatty=lambda: False))

    main()

    intro.assert_not_called()
    app_call.assert_called_once()


def test_main_skips_intro_for_help_argument(monkeypatch) -> None:
    intro = Mock(return_value=True)
    app_call = Mock()
    monkeypatch.setattr("educlaw.cli._play_intro", intro)
    monkeypatch.setattr("educlaw.cli.app", app_call)
    monkeypatch.setattr("educlaw.cli.sys.argv", ["educlaw", "--help"])
    monkeypatch.setattr("educlaw.cli.sys.stdout", SimpleNamespace(isatty=lambda: True))

    main()

    intro.assert_not_called()
    app_call.assert_called_once()


def test_intro_logo_loading() -> None:
    from educlaw.cli import _load_intro_logo, _intro_logo_path
    logo = _load_intro_logo()
    assert logo is not None
    assert "/$$$$$$$$" in logo

    path = _intro_logo_path()
    assert path.exists()
    assert path.name == "ascii-logo.txt"