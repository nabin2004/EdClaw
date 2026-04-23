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
    assert "plan" in kinds
    assert "scene_start" in kinds
    assert "codegen" in kinds
    assert "critic" in kinds
    assert "render" in kinds
    assert "scene_done" in kinds
    assert kinds[-1] == "done"
