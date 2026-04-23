"""ManiBench-style automated metrics: executability, VCER, alignment, coverage (heuristic)."""

from __future__ import annotations

from typing import Any

from educlaw.viz import (
    extract_python,
    has_manim_scene,
    render_executable,
    scene_class_name,
    syntax_ok,
)
from manibench.eval.vcer_patterns import scan_vcer

# Backward-compatible alias for internal / external callers
_scene_class_name = scene_class_name

# Optional per-problem event keywords (lowercased) for alignment
# Full benchmark uses dataset; this is a generic fallback
_DEFAULT_EVENT_KEYWORDS: list[str] = [
    "play(",
    "wait(",
    "create(",
    "write(",
    "next_to(",
    "move_to(",
    "animate",
    "value",
    "number",
    "tex(",
    "mathtex(",
    "arrow",
    "dot(",
    "line(",
    "axis",
    "vgroup",
    "brace",
]

def coverage_score(source: str) -> float:
    """Heuristic 4-dimension style coverage (0-1), code-only lower bound."""
    s = source.lower()
    score = 0.0
    # Math (0.35)
    math_hits = sum(1 for k in ("mathtex", "tex(", "math", "tex =") if k in s)
    score += 0.35 * min(1.0, math_hits / 3.0)
    # Visual (0.30)
    vis_keys = ("set_color", "set_fill", "arrow", "dot", "rectangle", "gradient")
    vis_hits = sum(1 for k in vis_keys if k in s)
    score += 0.30 * min(1.0, vis_hits / 3.0)
    # Numeric (0.20)
    num_hits = sum(
        1 for k in ("decimal", "integer", "valuetracker", "number_line", "axes", "axes(") if k in s
    )
    score += 0.20 * min(1.0, num_hits / 2.0)
    # Structural (0.15)
    str_hits = sum(1 for k in ("vgroup", "group(", "succession(", "laggedstart", "wait(") if k in s)
    score += 0.15 * min(1.0, str_hits / 3.0)
    return round(min(1.0, score), 4)


def alignment_score(source: str, required_keywords: list[str] | None = None) -> float:
    """Fraction of required keywords present (timing not verified — heuristic)."""
    keywords = required_keywords or _DEFAULT_EVENT_KEYWORDS
    if not keywords:
        return 1.0
    found = sum(1 for kw in keywords if kw.lower() in source.lower())
    return round(found / len(keywords), 4)


def evaluate_sample(
    raw_output: str,
    *,
    required_keywords: list[str] | None = None,
    run_render: bool = True,
    manim_bin: str = "manim",
) -> dict[str, Any]:
    """Compute Exec, VCER, Alignment, Coverage for one generation."""
    code = extract_python(raw_output)
    vcer_r = scan_vcer(code)

    exec_score = 0.0
    err = ""
    if not syntax_ok(code):
        exec_score = 0.0
        err = "syntax_error"
    elif not has_manim_scene(code):
        exec_score = 0.0
        err = "no_scene"
    elif run_render:
        ok, err = render_executable(code, manim_bin=manim_bin)
        exec_score = 1.0 if ok else 0.0
    else:
        # Static-only mode (faster CI)
        exec_score = 1.0 if not vcer_r.has_conflict else 0.0

    ali = alignment_score(code, required_keywords)
    cov = coverage_score(code)

    return {
        "executability": exec_score,
        "vcer": vcer_r.vcer,
        "vcer_hits": vcer_r.hits,
        "alignment": ali,
        "coverage": cov,
        "error": err,
    }


def composite_reward(metrics: dict[str, Any]) -> float:
    """Plan default: 0.4*Exec + 0.3*(1-VCER) + 0.2*Cov + 0.1*Align."""
    ex = float(metrics["executability"])
    vc = float(metrics["vcer"])
    cov = float(metrics["coverage"])
    ali = float(metrics["alignment"])
    return 0.4 * ex + 0.3 * (1.0 - vc) + 0.2 * cov + 0.1 * ali
