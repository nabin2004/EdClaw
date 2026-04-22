# /// script
# dependencies = []
# ///
"""
Self-contained ManiBench-style evaluator for HF Jobs `uv run` (no repo checkout).

Scores: executability (optional manim subprocess), VCER, alignment, coverage heuristics.

Example (local):
  uv run scripts/eval_uv_standalone.py --in samples.jsonl --out scores.jsonl --no-render

Example (HF Jobs): upload this file and pass script_args.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

GL_BAN_PATTERNS: list[tuple[str, str]] = [
    (r"manim_imports_ext", "import_system: manim_imports_ext"),
    (r"from\s+manimlib", "import_system: manimlib"),
    (r"\bCONFIG\s*=\s*\{", "class_config: CONFIG dict"),
    (r"\bShowCreation\s*\(", "animation: ShowCreation"),
    (r"\bFadeInFrom\s*\(", "animation: FadeInFrom"),
    (r"\bInteractiveScene\b", "scene: InteractiveScene"),
    (r"\bGraphScene\b", "scene: GraphScene"),
    (r"\bPiCreature\b", "pi_creature"),
    (r"apply_depth_test", "3d"),
    (r"set_shading\s*\(", "3d shading"),
    (r"frame\.reorient\s*\(", "camera"),
    (r"\bMCircle\b", "hallucination MCircle"),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), reason) for p, reason in GL_BAN_PATTERNS]

_DEFAULT_EVENT_KEYWORDS = [
    "play(",
    "wait(",
    "create(",
    "write(",
    "animate",
    "tex(",
    "mathtex(",
    "dot(",
    "vgroup",
]

_CODE_FENCE = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.IGNORECASE)


def extract_python(text: str) -> str:
    m = _CODE_FENCE.search(text)
    return m.group(1).strip() if m else text.strip()


def scan_vcer(source: str) -> tuple[float, list[str]]:
    hits: list[str] = []
    for pat, reason in _COMPILED:
        if pat.search(source):
            hits.append(reason)
    return (1.0 if hits else 0.0), hits


def _scene_class_name(source: str) -> str | None:
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


def coverage_score(source: str) -> float:
    s = source.lower()
    score = 0.0
    math_hits = sum(1 for k in ("mathtex", "tex(", "math") if k in s)
    score += 0.35 * min(1.0, math_hits / 3.0)
    vis_hits = sum(1 for k in ("set_color", "arrow", "dot") if k in s)
    score += 0.30 * min(1.0, vis_hits / 3.0)
    num_hits = sum(1 for k in ("decimal", "valuetracker", "axes") if k in s)
    score += 0.20 * min(1.0, num_hits / 2.0)
    str_hits = sum(1 for k in ("vgroup", "succession(", "wait(") if k in s)
    score += 0.15 * min(1.0, str_hits / 3.0)
    return round(min(1.0, score), 4)


def alignment_score(source: str, keywords: list[str] | None) -> float:
    kws = keywords or _DEFAULT_EVENT_KEYWORDS
    found = sum(1 for kw in kws if kw.lower() in source.lower())
    return round(found / len(kws), 4) if kws else 1.0


def render_executable(source: str, timeout_sec: int, manim_bin: str) -> tuple[bool, str]:
    scene = _scene_class_name(source)
    if not scene:
        return False, "no Scene subclass"
    with tempfile.TemporaryDirectory(prefix="mb_") as td:
        path = Path(td) / "scene.py"
        path.write_text(source, encoding="utf-8")
        cmd = [manim_bin, "render", "-ql", str(path), scene]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, cwd=td)
        except subprocess.TimeoutExpired:
            return False, "timeout"
        ok = proc.returncode == 0
        err = (proc.stderr or "")[-3000:]
        return ok, err


def evaluate_sample(
    raw: str,
    *,
    run_render: bool,
    manim_bin: str,
    timeout_sec: int,
    keywords: list[str] | None,
) -> dict[str, Any]:
    code = extract_python(raw)
    vc, hits = scan_vcer(code)
    err = ""
    exec_score = 0.0
    if not syntax_ok(code):
        exec_score = 0.0
        err = "syntax_error"
    elif not has_manim_scene(code):
        exec_score = 0.0
        err = "no_scene"
    elif run_render:
        ok, err = render_executable(code, timeout_sec, manim_bin)
        exec_score = 1.0 if ok else 0.0
    else:
        exec_score = 1.0 if vc == 0.0 else 0.0

    return {
        "executability": exec_score,
        "vcer": vc,
        "vcer_hits": hits,
        "alignment": alignment_score(code, keywords),
        "coverage": coverage_score(code),
        "error": err,
    }


def composite_reward(m: dict[str, Any]) -> float:
    ex = float(m["executability"])
    vc = float(m["vcer"])
    cov = float(m["coverage"])
    ali = float(m["alignment"])
    return 0.4 * ex + 0.3 * (1.0 - vc) + 0.2 * cov + 0.1 * ali


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--manim-bin", default="manim")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    out_rows = []
    with args.inp.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            text = obj.get("completion") or obj.get("text") or obj.get("assistant")
            if text is None and "messages" in obj:
                text = ""
                for m in reversed(obj["messages"]):
                    if m.get("role") == "assistant":
                        text = m["content"]
                        break
            assert text is not None
            metrics = evaluate_sample(
                text,
                run_render=not args.no_render,
                manim_bin=args.manim_bin,
                timeout_sec=args.timeout,
                keywords=None,
            )
            metrics["reward"] = composite_reward(metrics)
            obj["metrics"] = metrics
            out_rows.append(obj)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fo:
        for r in out_rows:
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Scored {len(out_rows)} rows -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
