"""Tests for teacher SFT generation (dry-run, mocked LiteLLM, response cache)."""

from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

MB_ROOT = Path(__file__).resolve().parents[1] / "training" / "manibench"
sys.path.insert(0, str(MB_ROOT))

from manibench.prompt_seeds import weighted_prompts  # noqa: E402


def _load_generate_module():
    path = MB_ROOT / "scripts" / "generate_sft_teacher.py"
    spec = importlib.util.spec_from_file_location("generate_sft_teacher", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _namespace(**kwargs: object) -> Namespace:
    defaults: dict[str, object] = {
        "model": "test/fake-model",
        "count": 5,
        "seed": 42,
        "prompts_jsonl": None,
        "out": Path(),
        "rejected_out": None,
        "cache_dir": Path(),
        "resume": False,
        "concurrency": 2,
        "temperature": 0.2,
        "max_tokens": 512,
        "timeout": 30.0,
        "max_retries": 2,
        "render_eval": False,
        "require_exec": False,
        "min_composite": 0.0,
        "dry_run": False,
        "skip_leak_check": False,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_weighted_prompts_length() -> None:
    import random

    rng = random.Random(0)
    pairs = weighted_prompts(100, rng)
    assert len(pairs) == 100
    for cat, user in pairs:
        assert cat
        assert user
        assert isinstance(user, str)


@pytest.mark.asyncio
async def test_dry_run_writes_rows(tmp_path: Path) -> None:
    mod = _load_generate_module()
    out = tmp_path / "teacher.jsonl"
    cache_dir = tmp_path / "cache"
    args = _namespace(
        out=out,
        cache_dir=cache_dir,
        count=7,
        dry_run=True,
    )
    n = await mod._run_async(args)
    assert n == 7
    lines = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 7
    for row in lines:
        assert row["source"].startswith("teacher:")
        msgs = row["messages"]
        assert [m["role"] for m in msgs] == ["system", "user", "assistant"]
        assert "metrics" in row
        assert row["task_type"]


@pytest.mark.asyncio
async def test_mocked_acompletion_and_cache_zero_second_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_generate_module()
    calls: list[int] = []

    async def fake_acompletion(**_kwargs: object) -> str:
        calls.append(1)
        return """```python
from manim import *

class MockScene(Scene):
    def construct(self):
        self.play(Create(Text("ok", font_size=40)))
```"""

    monkeypatch.setattr(mod, "_acompletion_with_retries", fake_acompletion)

    out1 = tmp_path / "a.jsonl"
    cache_dir = tmp_path / "shared_cache"
    args1 = _namespace(out=out1, cache_dir=cache_dir, count=4, seed=99, dry_run=False)
    n1 = await mod._run_async(args1)
    assert n1 == 4
    assert len(calls) == 4

    calls.clear()
    out2 = tmp_path / "b.jsonl"
    args2 = _namespace(out=out2, cache_dir=cache_dir, count=4, seed=99, dry_run=False)
    n2 = await mod._run_async(args2)
    assert n2 == 4
    assert len(calls) == 0, "cache should satisfy all prompts on second run"


@pytest.mark.asyncio
async def test_resume_skips_existing_users(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_generate_module()

    async def fake_acompletion(**_kwargs: object) -> str:
        return """```python
from manim import *

class R(Scene):
    def construct(self):
        self.play(Create(Text("r")))
```"""

    monkeypatch.setattr(mod, "_acompletion_with_retries", fake_acompletion)

    out = tmp_path / "resume.jsonl"
    cache = tmp_path / "c2"
    args = _namespace(out=out, cache_dir=cache, count=3, seed=7, dry_run=False)
    await mod._run_async(args)
    first_calls = sum(1 for _ in cache.glob("*.json"))

    async def boom(**_kwargs: object) -> str:
        raise AssertionError("API should not be called when all users are resumed")

    monkeypatch.setattr(mod, "_acompletion_with_retries", boom)
    args_resume = _namespace(out=out, cache_dir=cache, count=3, seed=7, dry_run=False, resume=True)
    n = await mod._run_async(args_resume)
    assert n == 3
    assert first_calls > 0
