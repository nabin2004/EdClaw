"""Render Manim source to MP4 (local subprocess or Docker one-shot)."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol

from educlaw.automanim.schema import RenderArtifact
from educlaw.config.settings import Settings
from educlaw.viz import extract_python, find_rendered_mp4s, render_to_mp4, scene_class_name


class RenderBackend(Protocol):
    async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact: ...


class LocalRenderBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact:
        code = extract_python(source)
        sc = scene_class_name(code) or "Scene"
        ok, err = await asyncio.to_thread(
            render_to_mp4,
            code,
            dest_mp4,
            timeout_sec=self._settings.automanim_timeout_sec,
            quality=f"q{self._settings.automanim_quality}",
            manim_bin="manim",
        )
        return RenderArtifact(
            artifact_path=str(dest_mp4) if ok else "",
            scene_name=sc,
            exit_code=0 if ok else 1,
            stderr_tail=err[-8000:],
        )


def _docker_render_sync(
    settings: Settings,
    code: str,
    dest_mp4: Path,
    scene: str,
) -> RenderArtifact:
    td = Path(tempfile.mkdtemp(prefix="educlaw_automanim_docker_"))
    try:
        scene_path = td / "scene.py"
        scene_path.write_text(code, encoding="utf-8")
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "-v",
            f"{td}:/work",
            "-w",
            "/work",
            settings.automanim_image,
            "manim",
            "render",
            f"-q{settings.automanim_quality}",
            "/work/scene.py",
            scene,
        ]
        try:
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=float(settings.automanim_timeout_sec),
            )
        except subprocess.TimeoutExpired:
            return RenderArtifact(
                artifact_path="",
                scene_name=scene,
                exit_code=124,
                stderr_tail="docker timeout",
            )
        err = ((p.stderr or "") + (p.stdout or ""))[-8000:]
        if p.returncode != 0:
            return RenderArtifact(
                artifact_path="",
                scene_name=scene,
                exit_code=p.returncode,
                stderr_tail=err,
            )
        mp4s = find_rendered_mp4s(td)
        if not mp4s:
            return RenderArtifact(
                artifact_path="",
                scene_name=scene,
                exit_code=1,
                stderr_tail=err + "\nno mp4",
            )
        dest_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mp4s[-1], dest_mp4)
        return RenderArtifact(
            artifact_path=str(dest_mp4),
            scene_name=scene,
            exit_code=0,
            stderr_tail=err,
        )
    finally:
        shutil.rmtree(td, ignore_errors=True)


class DockerRenderBackend:
    """One-shot ``docker run`` with a temp dir mounted at ``/work``."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact:
        code = extract_python(source)
        sc = scene_class_name(code)
        if not sc:
            return RenderArtifact(
                artifact_path="",
                scene_name="",
                exit_code=1,
                stderr_tail="no Scene",
            )
        loop = asyncio.get_running_loop()

        def _call() -> RenderArtifact:
            return _docker_render_sync(self._settings, code, dest_mp4, sc)

        return await loop.run_in_executor(None, _call)


def build_render_backend(settings: Settings) -> RenderBackend:
    if settings.automanim_backend == "docker":
        return DockerRenderBackend(settings)
    return LocalRenderBackend(settings)
