from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from educlaw.automanim.orchestrator import run_automanim
from educlaw.automanim.schema import RenderArtifact
from educlaw.config.settings import Settings
from educlaw.safety.shield import Shield, Verdict


@pytest.mark.asyncio
async def test_run_automanim_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def fake_llm(agent: Any, *, user_text: str, user_id: str = "automanim") -> str:
        name = getattr(agent, "name", "")
        if name == "automanim_planner":
            return '{"scenes":[{"title":"One","description":"x","visual_intent":"y"}]}'
        return (
            "from manim import *\n\n"
            "class CScene(Scene):\n"
            "    def construct(self):\n"
            "        self.add(Dot())\n"
        )

    class _FB:
        async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact:
            dest_mp4.parent.mkdir(parents=True, exist_ok=True)
            dest_mp4.write_bytes(b"")
            return RenderArtifact(artifact_path=str(dest_mp4), scene_name="CScene", exit_code=0)

    monkeypatch.setattr("educlaw.automanim.orchestrator.run_llm_agent_once", fake_llm)
    monkeypatch.setattr("educlaw.automanim.orchestrator.build_render_backend", lambda _s: _FB())
    monkeypatch.setattr("educlaw.automanim.orchestrator.manim_available", lambda: True)

    shield = Shield(AsyncMock(), model="shield")
    shield.classify = AsyncMock(return_value=Verdict.ALLOW)

    settings = Settings(data_dir=tmp_path)
    events = [
        e
        async for e in run_automanim(
            "# Lecture\n",
            {"id": "lec.1", "title": "L1"},
            settings,
            shield,
            ollama=None,
            output_root=tmp_path / "out",
        )
    ]
    kinds = [e.kind for e in events]
    assert kinds[0] == "phase"
    plan_idx = kinds.index("plan")
    assert plan_idx >= 1
    assert all(k == "phase" for k in kinds[:plan_idx])
    assert "plan" in kinds
    assert "scene_start" in kinds
    assert "codegen" in kinds
    assert "critic" in kinds
    assert "render" in kinds
    assert "scene_done" in kinds
    assert kinds[-1] == "done"


@pytest.mark.asyncio
async def test_run_automanim_render_subprocess_failure_emits_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Non-zero Manim exit must yield kind=error (not only scene_done with empty path)."""

    async def fake_llm(agent: Any, *, user_text: str, user_id: str = "automanim") -> str:
        name = getattr(agent, "name", "")
        if name == "automanim_planner":
            return '{"scenes":[{"title":"One","description":"x","visual_intent":"y"}]}'
        return (
            "from manim import *\n\n"
            "class CScene(Scene):\n"
            "    def construct(self):\n"
            "        self.add(Dot())\n"
        )

    class _FB:
        async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact:
            return RenderArtifact(
                artifact_path="",
                scene_name="CScene",
                exit_code=1,
                stderr_tail="manim: not found",
            )

    monkeypatch.setattr("educlaw.automanim.orchestrator.run_llm_agent_once", fake_llm)
    monkeypatch.setattr("educlaw.automanim.orchestrator.build_render_backend", lambda _s: _FB())
    monkeypatch.setattr("educlaw.automanim.orchestrator.manim_available", lambda: True)

    shield = Shield(AsyncMock(), model="shield")
    shield.classify = AsyncMock(return_value=Verdict.ALLOW)

    settings = Settings(data_dir=tmp_path)
    events = [
        e
        async for e in run_automanim(
            "# L\n",
            {"id": "lec.1", "title": "L1"},
            settings,
            shield,
            ollama=None,
            output_root=tmp_path / "out",
        )
    ]
    err_msgs = [e.message for e in events if e.kind == "error" and e.scene_index == 1]
    assert err_msgs
    assert "Render failed" in (err_msgs[0] or "")
    assert "exit 1" in (err_msgs[0] or "")
    assert "manim" in (err_msgs[0] or "").lower()


@pytest.mark.asyncio
async def test_run_automanim_local_aborts_when_manim_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    called: list[str] = []

    async def boom_llm(agent: Any, *, user_text: str, user_id: str = "automanim") -> str:
        called.append(getattr(agent, "name", ""))
        return "{}"

    monkeypatch.setattr("educlaw.automanim.orchestrator.run_llm_agent_once", boom_llm)
    monkeypatch.setattr("educlaw.automanim.orchestrator.manim_available", lambda: False)

    shield = Shield(AsyncMock(), model="shield")
    shield.classify = AsyncMock(return_value=Verdict.ALLOW)

    settings = Settings(data_dir=tmp_path, automanim_backend="local")
    events = [
        e
        async for e in run_automanim(
            "# L\n",
            {"id": "lec.1", "title": "L1"},
            settings,
            shield,
            ollama=None,
            output_root=tmp_path / "out",
        )
    ]
    assert called == []
    errs = [e for e in events if e.kind == "error"]
    assert len(errs) == 1
    assert "educlaw[automanim]" in (errs[0].message or "")
