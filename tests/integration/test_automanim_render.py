"""Slow tests: real ``manim`` subprocess (skipped when not on PATH)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from educlaw.viz import render_to_mp4

pytestmark = pytest.mark.slow

_GOLDEN = '''
from manim import *

class GoldenSmoke(Scene):
    def construct(self):
        self.add(Dot())
'''


@pytest.mark.skipif(not shutil.which("manim"), reason="manim not on PATH")
def test_render_to_mp4_smoke(tmp_path: Path) -> None:
    dest = tmp_path / "GoldenSmoke.mp4"
    ok, err = render_to_mp4(
        _GOLDEN,
        dest,
        timeout_sec=120,
        quality="ql",
        manim_bin="manim",
    )
    assert ok, err
    assert dest.is_file()
    assert dest.stat().st_size > 100
