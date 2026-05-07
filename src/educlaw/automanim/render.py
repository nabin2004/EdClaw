"""Render Manim source to MP4 (local subprocess or Docker one-shot)."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from educlaw.automanim.schema import RenderArtifact
from educlaw.config.settings import Settings
from educlaw.viz import extract_python, find_rendered_mp4s, render_to_mp4, scene_class_name

LOG = logging.getLogger(__name__)

_DOCKER_LOG_CAP = 500_000


class RenderBackend(Protocol):
    async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact: ...


def _workspace_meta(work_dir: Path) -> dict[str, str]:
    wd = work_dir.resolve()
    return {
        "scene_dir": str(wd),
        "source_path": str(wd / "scene.py"),
        "log_path": str(wd / "render.log"),
    }


def _docker_user_run_args(settings: Settings) -> list[str]:
    spec = (settings.automanim_docker_user or "auto").strip()
    if spec.lower() == "none":
        return []
    if spec.lower() == "auto":
        getuid = getattr(os, "getuid", None)
        getgid = getattr(os, "getgid", None)
        if not callable(getuid) or not callable(getgid):
            return []
        return ["--user", f"{getuid()}:{getgid()}"]
    return ["--user", spec]


class LocalRenderBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact:
        code = extract_python(source)
        sc = scene_class_name(code) or "Scene"
        work_dir = dest_mp4.parent
        meta = _workspace_meta(work_dir)
        ok, err = await asyncio.to_thread(
            render_to_mp4,
            code,
            dest_mp4,
            timeout_sec=self._settings.automanim_timeout_sec,
            quality=self._settings.automanim_quality,
            work_dir=work_dir,
        )
        art = RenderArtifact(
            artifact_path=str(dest_mp4) if ok else "",
            scene_name=sc,
            exit_code=0 if ok else 1,
            stderr_tail=err[-8000:],
            **meta,
        )
        LOG.info(
            "automanim_render backend=local scene=%s dest=%s ok=%s exit=%s",
            sc,
            dest_mp4,
            ok,
            art.exit_code,
        )
        return art


def _docker_render_sync(
    settings: Settings,
    code: str,
    dest_mp4: Path,
    scene: str,
) -> RenderArtifact:
    work_dir = dest_mp4.parent.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    scene_path = work_dir / "scene.py"
    scene_path.write_text(code, encoding="utf-8")
    log_path = work_dir / "render.log"
    meta = _workspace_meta(work_dir)

    cmd = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        *_docker_user_run_args(settings),
        "-v",
        f"{work_dir}:/work",
        "-w",
        "/work",
        settings.automanim_image,
        "manim",
        "render",
        f"-q{settings.automanim_quality}",
        "/work/scene.py",
        scene,
    ]
    proc: subprocess.CompletedProcess[str] | None = None
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=float(settings.automanim_timeout_sec),
        )
    except subprocess.TimeoutExpired:
        log_path.write_text("docker timeout\n", encoding="utf-8")
        return RenderArtifact(
            artifact_path="",
            scene_name=scene,
            exit_code=124,
            stderr_tail="docker timeout",
            **meta,
        )

    assert proc is not None
    full_out = (proc.stdout or "") + (proc.stderr or "")
    tail_log = full_out[-_DOCKER_LOG_CAP:] if len(full_out) > _DOCKER_LOG_CAP else full_out
    log_path.write_text(tail_log, encoding="utf-8")
    err = full_out[-8000:]
    if proc.returncode != 0:
        return RenderArtifact(
            artifact_path="",
            scene_name=scene,
            exit_code=proc.returncode,
            stderr_tail=err,
            **meta,
        )
    mp4s = find_rendered_mp4s(work_dir)
    if not mp4s:
        return RenderArtifact(
            artifact_path="",
            scene_name=scene,
            exit_code=1,
            stderr_tail=err + "\nno mp4",
            **meta,
        )
    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    newest = mp4s[-1]
    if newest.resolve() != dest_mp4.resolve():
        shutil.copy2(newest, dest_mp4)
    return RenderArtifact(
        artifact_path=str(dest_mp4),
        scene_name=scene,
        exit_code=0,
        stderr_tail=err,
        **meta,
    )


class DockerRenderBackend:
    """One-shot ``docker run`` with the scene directory mounted at ``/work``."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def render_scene(self, source: str, dest_mp4: Path) -> RenderArtifact:
        code = extract_python(source)
        sc = scene_class_name(code)
        if not sc:
            meta = _workspace_meta(dest_mp4.parent)
            return RenderArtifact(
                artifact_path="",
                scene_name="",
                exit_code=1,
                stderr_tail="no Scene",
                **meta,
            )
        loop = asyncio.get_running_loop()

        def _call() -> RenderArtifact:
            return _docker_render_sync(self._settings, code, dest_mp4, sc)

        art = await loop.run_in_executor(None, _call)
        LOG.info(
            "automanim_render backend=docker scene=%s dest=%s ok=%s exit=%s",
            sc,
            dest_mp4,
            bool(art.artifact_path),
            art.exit_code,
        )
        return art


def build_render_backend(settings: Settings) -> RenderBackend:
    if settings.automanim_backend == "docker":
        return DockerRenderBackend(settings)
    return LocalRenderBackend(settings)
