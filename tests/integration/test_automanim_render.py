"""Slow tests: real Manim CE subprocess (skipped when not on PATH or via python -m)."""

from __future__ import annotations

from pathlib import Path

import pytest

from educlaw.viz import manim_available, render_to_mp4

pytestmark = pytest.mark.slow

_GOLDEN = '''
from manim import *

class GoldenSmoke(Scene):
    def construct(self):
        self.add(Dot())
'''


@pytest.mark.skipif(not manim_available(), reason="manim CE not available (PATH or python -m manim)")
def test_render_to_mp4_smoke(tmp_path: Path) -> None:
    dest = tmp_path / "GoldenSmoke.mp4"
    ok, err = render_to_mp4(
        _GOLDEN,
        dest,
        timeout_sec=120,
        quality="l",
    )
    assert ok, err
    assert dest.is_file()
    assert dest.stat().st_size > 100
