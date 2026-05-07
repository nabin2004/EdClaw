from pathlib import Path
import pytest

from educlaw.automanim.render import LocalRenderBackend
from educlaw.config.settings import Settings


@pytest.mark.asyncio
async def test_local_render_invokes_render_to_mp4(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple] = []

    def fake_render_to_mp4(source: str, dest_mp4: Path, **kwargs: object) -> tuple[bool, str]:
        calls.append((source, str(dest_mp4), kwargs))
        dest_mp4.parent.mkdir(parents=True, exist_ok=True)
        dest_mp4.write_bytes(b"x")
        return True, ""

    monkeypatch.setattr("educlaw.automanim.render.render_to_mp4", fake_render_to_mp4)

    s = Settings(data_dir=tmp_path)
    backend = LocalRenderBackend(s)
    dest = tmp_path / "out.mp4"
    art = await backend.render_scene("from manim import *\nclass CScene(Scene):\n    def construct(self):\n        pass\n", dest)
    assert art.exit_code == 0
    assert art.scene_name == "CScene"
    assert len(calls) == 1
    cmd_kwargs = calls[0][2]
    assert cmd_kwargs["quality"] == f"q{s.automanim_quality}"
    assert cmd_kwargs.get("manim_bin") is None


@pytest.mark.asyncio
async def test_docker_render_builds_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import educlaw.automanim.render as render_mod

    from educlaw.automanim.schema import RenderArtifact

    def fake_sync(settings: object, code: str, dest_mp4: Path, scene: str) -> RenderArtifact:
        _ = settings, code
        return RenderArtifact(artifact_path=str(dest_mp4), scene_name=scene, exit_code=0)

    monkeypatch.setattr(render_mod, "_docker_render_sync", fake_sync)
    s = Settings(data_dir=tmp_path, automanim_backend="docker")
    backend = render_mod.DockerRenderBackend(s)
    art = await backend.render_scene(
        "from manim import *\nclass DScene(Scene):\n    def construct(self):\n        pass\n",
        tmp_path / "z.mp4",
    )
    assert art.scene_name == "DScene"
