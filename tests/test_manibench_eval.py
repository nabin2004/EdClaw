"""Tests for training/manibench evaluation and leakage guards."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

MB_ROOT = Path(__file__).resolve().parents[1] / "training" / "manibench"
sys.path.insert(0, str(MB_ROOT))

from manibench.eval.harness import evaluate_sample, extract_python  # noqa: E402
from manibench.eval.vcer_patterns import scan_vcer  # noqa: E402
from manibench.leakage import (  # noqa: E402
    assert_no_eval_leakage,
    load_pilot_hashes,
)


def test_extract_python_fence() -> None:
    raw = 'Here:\n```python\nx = 1\n```'
    assert extract_python(raw).strip() == "x = 1"


def test_vcer_detects_show_creation() -> None:
    src = (
        "from manim import *\nclass A(Scene):\n"
        "    def construct(self):\n"
        "        self.play(ShowCreation(Dot()))"
    )
    r = scan_vcer(src)
    assert r.vcer == 1.0


def test_evaluate_sample_static_bad_syntax() -> None:
    m = evaluate_sample("not python {{{", run_render=False)
    assert m["executability"] == 0.0


def test_evaluate_sample_static_good_ce() -> None:
    code = '''from manim import *

class Good(Scene):
    def construct(self):
        self.play(Create(Text("hi")))
'''
    m = evaluate_sample(code, run_render=False)
    assert m["executability"] == 1.0
    assert m["vcer"] == 0.0


def test_leakage_raises_on_pilot_prompt() -> None:
    hashes = load_pilot_hashes()
    # Recover one pilot prompt text from placeholder file
    pilot_path = MB_ROOT / "manibench" / "data" / "pilot_prompts.json"
    data = json.loads(pilot_path.read_text(encoding="utf-8"))
    prompt = data[0]["full_prompt"]
    with pytest.raises(ValueError, match="leak|pilot"):
        assert_no_eval_leakage([prompt], pilot_hashes=hashes)


def test_composite_reward_bounds() -> None:
    from manibench.eval.harness import composite_reward  # noqa: WPS433

    m = {"executability": 1.0, "vcer": 0.0, "coverage": 0.5, "alignment": 0.5}
    r = composite_reward(m)
    assert 0.0 <= r <= 1.0
