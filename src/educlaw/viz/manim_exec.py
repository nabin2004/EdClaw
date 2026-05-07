"""Manim CE execution helpers (shared by ManiBench and AutoManim)."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_CODE_FENCE = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.IGNORECASE)


def extract_python(text: str) -> str:
    """Strip markdown fences; if none, return stripped text."""
    m = _CODE_FENCE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def scene_class_name(source: str) -> str | None:
    """Return the first ``class Name(Scene)`` name in *source*, or None."""
    m = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", source)
    return m.group(1) if m else None


def syntax_ok(source: str) -> bool:
    try:
        ast.parse(source)
    except SyntaxError:
        return False
    return True


def has_manim_scene(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Scene":
                    return True
                if isinstance(base, ast.Attribute) and base.attr == "Scene":
                    return True
    return False


def manim_command_prefix(manim_bin: str | None = None) -> list[str]:
    """Argv prefix so ``prefix + ['render', ...]`` invokes Manim CE."""
    if manim_bin:
        return [manim_bin]
    w = shutil.which("manim")
    if w:
        return [w]
    return [sys.executable, "-m", "manim"]


def manim_available() -> bool:
    """True if Manim CE is invokable via ``manim`` on PATH or ``python -m manim``."""
    if shutil.which("manim"):
        return True
    try:
        r = subprocess.run(
            [sys.executable, "-m", "manim", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def render_executable(
    source: str,
    *,
    timeout_sec: int = 60,
    quality: str = "ql",
    manim_bin: str | None = None,
) -> tuple[bool, str]:
    """Run manim render in a temp dir. Returns (success, stderr snippet)."""
    scene = scene_class_name(source)
    if not scene:
        return False, "no Scene subclass found"

    with tempfile.TemporaryDirectory(prefix="educlaw_manim_") as td:
        path = Path(td) / "generated_scene.py"
        path.write_text(source, encoding="utf-8")
        cmd = [*manim_command_prefix(manim_bin), "render", f"-q{quality}", str(path), scene]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=td,
            )
        except subprocess.TimeoutExpired:
            return False, "timeout"
        ok = proc.returncode == 0
        err = (proc.stderr or "")[-4000:]
        if not ok and proc.stdout:
            err += (proc.stdout or "")[-2000:]
        return ok, err


def find_rendered_mp4s(work_dir: Path) -> list[Path]:
    """Return mp4 paths under *work_dir* (Manim ``media/`` layout), newest last."""
    return sorted(work_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)


def render_to_mp4(
    source: str,
    dest_mp4: Path,
    *,
    timeout_sec: int = 60,
    quality: str = "ql",
    manim_bin: str | None = None,
) -> tuple[bool, str]:
    """Run manim in a temp dir; on success copy the newest ``*.mp4`` to *dest_mp4*."""
    scene = scene_class_name(source)
    if not scene:
        return False, "no Scene subclass found"

    with tempfile.TemporaryDirectory(prefix="educlaw_manim_") as td:
        td_path = Path(td)
        path = td_path / "generated_scene.py"
        path.write_text(source, encoding="utf-8")
        cmd = [*manim_command_prefix(manim_bin), "render", f"-q{quality}", str(path), scene]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=td,
            )
        except subprocess.TimeoutExpired:
            return False, "timeout"
        ok = proc.returncode == 0
        err = (proc.stderr or "")[-4000:]
        if not ok and proc.stdout:
            err += (proc.stdout or "")[-2000:]
        if not ok:
            return False, err
        mp4s = find_rendered_mp4s(td_path)
        if not mp4s:
            return False, err + "\n(no mp4 produced)"
        dest_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mp4s[-1], dest_mp4)
        return True, err
