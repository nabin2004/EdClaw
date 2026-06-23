"""Unit tests for GRPO ManiBench reward functions (no GPU)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from rewards import (
    HEURISTIC_EXEC_PARTIAL,
    REWARD_WEIGHTS,
    alignment_reward,
    combined_reward,
    executability_reward,
)

_MINIMAL_SCENE = """```python
from manim import *

class MyScene(Scene):
    def construct(self):
        pass
```"""

_BAD_SYNTAX = """```python
from manim import *
class MyScene(Scene)
    def construct(self):
        pass
```"""

_RICH_SCENE = """```python
from manim import *

class MyScene(Scene):
    def construct(self):
        axes = Axes()
        label = MathTex(r"x^2")
        dot = Dot()
        arrow = Arrow(ORIGIN, RIGHT)
        rect = Rectangle()
        group = VGroup(axes, label)
        group.arrange(DOWN)
        self.play(Create(axes), FadeIn(label))
        self.wait()
```"""


@pytest.fixture(autouse=True)
def _heuristic_render_only(monkeypatch):
    monkeypatch.setenv("MANIBENCH_GRPO_RENDER", "0")


def test_executability_bad_syntax_returns_zero():
    rewards = executability_reward([_BAD_SYNTAX])
    assert rewards == [0.0]


def test_executability_minimal_scene_partial_credit():
    rewards = executability_reward([_MINIMAL_SCENE])
    assert rewards == [HEURISTIC_EXEC_PARTIAL]


def test_alignment_undetectable_event_gets_no_credit():
    events = [(1.0, [])]
    with patch("rewards.get_alignment_events", return_value=events):
        rewards = alignment_reward([_MINIMAL_SCENE], problem_id=["test-problem"])
    assert rewards == [0.0]


def test_alignment_detected_event_gets_full_weight():
    events = [(1.0, [r"\bDot\b"])]
    with patch("rewards.get_alignment_events", return_value=events):
        rewards = alignment_reward([_RICH_SCENE], problem_id=["test-problem"])
    assert rewards == [1.0]


def test_combined_lazy_stub_scores_lower_than_rich_scene():
    lazy = [_MINIMAL_SCENE, _MINIMAL_SCENE]
    rich = [_RICH_SCENE, _RICH_SCENE]
    lazy_scores = combined_reward(lazy, problem_id=["", ""])
    rich_scores = combined_reward(rich, problem_id=["", ""])
    assert max(lazy_scores) < min(rich_scores)


def test_combined_length_penalty_reduces_reward():
    os.environ["MANIBENCH_LENGTH_PENALTY_COEF"] = "0.01"
    os.environ["MANIBENCH_MAX_COMPLETION_LENGTH"] = "100"
    short_ids = [list(range(50))]
    long_ids = [list(range(100))]
    base = combined_reward([_MINIMAL_SCENE], completion_ids=short_ids)
    penalized = combined_reward([_MINIMAL_SCENE], completion_ids=long_ids)
    assert penalized[0] < base[0]


def test_combined_reward_weights_sum_to_one():
    assert sum(REWARD_WEIGHTS.values()) == pytest.approx(1.0)


def test_combined_reward_clamped_to_unit_interval():
    os.environ["MANIBENCH_LENGTH_PENALTY_COEF"] = "0.5"
    scores = combined_reward([_BAD_SYNTAX], completion_ids=[[1] * 512])
    assert all(0.0 <= s <= 1.0 for s in scores)
