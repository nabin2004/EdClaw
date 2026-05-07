"""Unit tests for Manim CE invocation resolution."""

from __future__ import annotations

import sys
from unittest.mock import patch

from educlaw.viz.manim_exec import manim_command_prefix


def test_manim_command_prefix_explicit() -> None:
    assert manim_command_prefix("/opt/bin/manim") == ["/opt/bin/manim"]


def test_manim_command_prefix_uses_which() -> None:
    with patch("educlaw.viz.manim_exec.shutil.which", return_value="/usr/bin/manim"):
        assert manim_command_prefix() == ["/usr/bin/manim"]


def test_manim_command_prefix_falls_back_to_module() -> None:
    with patch("educlaw.viz.manim_exec.shutil.which", return_value=None):
        assert manim_command_prefix() == [sys.executable, "-m", "manim"]
