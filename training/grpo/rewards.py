import re
import subprocess
import tempfile
from pathlib import Path
from typing import List

from manibench import get_vcer_patterns, get_alignment_events, get_coverage_terms


def executability_reward(completions: List[str], **kwargs) -> List[float]:
    rewards = []
    for code in completions:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                script = Path(tmpdir) / "scene.py"
                script.write_text(code, encoding="utf-8")
                result = subprocess.run(
                    ["manim", "-pql", str(script)],
                    capture_output=True, text=True, timeout=60, cwd=tmpdir,
                )
                rewards.append(1.0 if result.returncode == 0 else 0.0)
        except Exception:
            rewards.append(0.0)
    return rewards


def vcer_reward(completions: List[str], **kwargs) -> List[float]:
    """Penalises ManimGL-specific patterns that break in Manim CE."""
    problem_ids = kwargs.get("problem_id", [""] * len(completions))
    rewards = []
    for code, pid in zip(completions, problem_ids):
        patterns = get_vcer_patterns(pid)
        conflicts = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE))
        rewards.append(max(0.0, 1.0 - conflicts / len(patterns)))
    return rewards


def alignment_reward(completions: List[str], **kwargs) -> List[float]:
    """
    Weighted presence check for ManiBench required_visual_events.
    Score = Σ(weight_i × present_i) / Σ(weight_i)
    Events without detectable patterns receive 0.5 (neutral).
    """
    problem_ids = kwargs.get("problem_id", [""] * len(completions))
    rewards = []
    for code, pid in zip(completions, problem_ids):
        events = get_alignment_events(pid)
        if not events:
            rewards.append(1.0)
            continue
        total_w = sum(w for w, _ in events)
        score = 0.0
        for weight, patterns in events:
            if not patterns:
                score += weight * 0.5
            elif any(re.search(p, code) for p in patterns):
                score += weight
        rewards.append(score / total_w)
    return rewards


_FALLBACK_PATTERNS = {
    "math":       [r"Tex\(", r"MathTex\(", r"\\[a-zA-Z]+", r"\blabel\b"],
    "visual":     [r"set_color\(", r"set_fill\(", r"Arrow\(", r"Dot\(", r"Rectangle\("],
    "numeric":    [r"DecimalNumber\(", r"Integer\(", r"ValueTracker\(", r"Axes\(", r"NumberLine\("],
    "structural": [r"VGroup\(", r"Group\(", r"arrange\(", r"wait\(", r"LaggedStart\(", r"Succession\("],
}
_FALLBACK_WEIGHTS = {"math": 0.35, "visual": 0.30, "numeric": 0.20, "structural": 0.15}


def coverage_reward(completions: List[str], **kwargs) -> List[float]:
    """Fraction of per-problem coverage terms found; falls back to category weights."""
    problem_ids = kwargs.get("problem_id", [""] * len(completions))
    rewards = []
    for code, pid in zip(completions, problem_ids):
        terms = get_coverage_terms(pid)
        if terms:
            found = sum(1 for t in terms if re.search(rf"\b{re.escape(t)}\b", code))
            rewards.append(found / len(terms))
        else:
            cat_scores = {
                cat: min(sum(len(re.findall(p, code, re.IGNORECASE)) for p in pats) / 10.0, 1.0)
                for cat, pats in _FALLBACK_PATTERNS.items()
            }
            rewards.append(sum(_FALLBACK_WEIGHTS[c] * cat_scores[c] for c in _FALLBACK_WEIGHTS))
    return rewards


def combined_reward(completions: List[str], **kwargs) -> List[float]:
    exec_r  = executability_reward(completions, **kwargs)
    vcer_r  = vcer_reward(completions, **kwargs)
    align_r = alignment_reward(completions, **kwargs)
    cover_r = coverage_reward(completions, **kwargs)
    return [0.25*e + 0.25*v + 0.25*a + 0.25*c
            for e, v, a, c in zip(exec_r, vcer_r, align_r, cover_r)]
