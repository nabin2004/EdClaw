import os
import subprocess
from pathlib import Path

import pytest

from educlaw.automanim.render import (
    DockerRenderBackend,
    LocalRenderBackend,
    _docker_render_sync,
    _docker_user_run_args,
)
from educlaw.automanim.schema import RenderArtifact
from educlaw.config.settings import Settings


def test_settings_automanim_docker_defaults() -> None:
    s = Settings()
    assert s.automanim_image == "manimcommunity/manim:stable"
    assert s.automanim_docker_user == "auto"


def test_docker_user_run_args_auto_posix_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getuid", lambda: 1000)
    monkeypatch.setattr(os, "getgid", lambda: 1001)
    s = Settings(automanim_docker_user="auto")
    assert _docker_user_run_args(s) == ["--user", "1000:1001"]


def test_docker_user_run_args_none() -> None:
    s = Settings(automanim_docker_user="none")
    assert _docker_user_run_args(s) == []


def test_docker_user_run_args_explicit() -> None:
    s = Settings(automanim_docker_user="33:44")
    assert _docker_user_run_args(s) == ["--user", "33:44"]


def test_docker_render_sync_writes_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cmds: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmds.append(cmd)
        vol = cmd[cmd.index("-v") + 1]
        host = vol.split(":", 1)[0]
        wd = Path(host)
        assert wd.is_dir()
        assert (wd / "scene.py").read_text(encoding="utf-8").startswith("from manim import")
        mp = wd / "media" / "dummy.mp4"
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_bytes(b"fake")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("educlaw.automanim.render.subprocess.run", fake_run)
    s = Settings(data_dir=tmp_path, automanim_backend="docker", automanim_docker_user="none")
    dest = tmp_path / "lec" / "01-a" / "scene.mp4"
    art = _docker_render_sync(
        s,
        "from manim import *\nclass X(Scene):\n    def construct(self):\n        pass\n",
        dest,
        "X",
    )
    assert art.exit_code == 0
    assert art.artifact_path == str(dest)
    assert dest.is_file()
    assert (dest.parent / "render.log").is_file()
    assert len(cmds) == 1
    assert s.automanim_image in cmds[0]
    assert "--network=none" in cmds[0]
    assert "--user" not in cmds[0]


def test_docker_render_sync_includes_user_when_auto(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "getuid", lambda: 9)
    monkeypatch.setattr(os, "getgid", lambda: 10)

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        vol = cmd[cmd.index("-v") + 1]
        host = vol.split(":", 1)[0]
        wd = Path(host)
        mp = wd / "m.mp4"
        wd.mkdir(parents=True, exist_ok=True)
        mp.write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("educlaw.automanim.render.subprocess.run", fake_run)
    s = Settings(data_dir=tmp_path, automanim_backend="docker", automanim_docker_user="auto")
    dest = tmp_path / "s" / "scene.mp4"
    art = _docker_render_sync(
        s,
        "from manim import *\nclass Y(Scene):\n    def construct(self):\n        pass\n",
        dest,
        "Y",
    )
    assert art.exit_code == 0


@pytest.mark.asyncio
async def test_local_render_invokes_render_to_mp4(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple] = []

    def fake_render_to_mp4(source: str, dest_mp4: Path, **kwargs: object) -> tuple[bool, str]:
        calls.append((source, str(dest_mp4), kwargs))
        dest_mp4.parent.mkdir(parents=True, exist_ok=True)
        dest_mp4.write_bytes(b"x")
        return True, ""

    monkeypatch.setattr("educlaw.automanim.render.render_to_mp4", fake_render_to_mp4)

    s = Settings(data_dir=tmp_path)
    backend = LocalRenderBackend(s)
    dest = tmp_path / "01-scene" / "scene.mp4"
    art = await backend.render_scene(
        "from manim import *\nclass CScene(Scene):\n    def construct(self):\n        pass\n",
        dest,
    )
    assert art.exit_code == 0
    assert art.scene_name == "CScene"
    assert art.scene_dir == str(dest.parent.resolve())
    assert art.source_path == str((dest.parent / "scene.py").resolve())
    assert art.log_path == str((dest.parent / "render.log").resolve())
    assert len(calls) == 1
    cmd_kwargs = calls[0][2]
    assert cmd_kwargs["quality"] == s.automanim_quality
    assert cmd_kwargs.get("manim_bin") is None
    assert cmd_kwargs["work_dir"] == dest.parent


@pytest.mark.asyncio
async def test_docker_render_builds_command(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_sync(settings: object, code: str, dest_mp4: Path, scene: str) -> RenderArtifact:
        _ = settings, code
        return RenderArtifact(artifact_path=str(dest_mp4), scene_name=scene, exit_code=0)

    monkeypatch.setattr("educlaw.automanim.render._docker_render_sync", fake_sync)
    s = Settings(data_dir=tmp_path, automanim_backend="docker")
    backend = DockerRenderBackend(s)
    art = await backend.render_scene(
        "from manim import *\nclass DScene(Scene):\n    def construct(self):\n        pass\n",
        tmp_path / "z.mp4",
    )
    assert art.scene_name == "DScene"
