#!/usr/bin/env python3
"""Build DPO preference dataset: chosen = Manim CE, rejected = GL-style (VCER triggers)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.constants import MANIM_CE_SYSTEM  # noqa: E402
from manibench.leakage import assert_no_eval_leakage  # noqa: E402


def _chosen_scene(i: int) -> str:
    return f'''from manim import *

class CEExample{i}(Scene):
    def construct(self):
        t = Text("CE {i}", font_size=48)
        self.play(Create(t))
'''


def _rejected_scene_gl(i: int) -> str:
    """Deliberately GL-flavored patterns that fail VCER under CE."""
    return f'''from manim_imports_ext import *

class GLExample{i}(Scene):
    CONFIG = {{"run_time": 1}}
    def construct(self):
        s = Square()
        self.play(ShowCreation(s))
'''


def generate_pairs(n: int, seed: int) -> list[dict]:
    rnd = random.Random(seed)
    rows = []
    prompt_templates = [
        "Write a Manim scene that shows the title '{title}'.",
        "Animate a square appearing with title '{title}'.",
        "Create a minimal Scene that writes '{title}' on screen.",
    ]
    for i in range(n):
        title = f"Slide {i}"
        user = rnd.choice(prompt_templates).format(title=title)
        rows.append(
            {
                "prompt": [
                    {"role": "system", "content": MANIM_CE_SYSTEM},
                    {"role": "user", "content": user},
                ],
                "chosen": _chosen_scene(i),
                "rejected": _rejected_scene_gl(i),
                "meta": {"pair_id": i, "strategy": "dual_template_gl_vs_ce"},
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "manibench-preference.jsonl")
    ap.add_argument("--pairs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-leak-check", action="store_true")
    args = ap.parse_args()

    rows = generate_pairs(args.pairs, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if not args.skip_leak_check:
        texts = []
        for r in rows:
            for m in r["prompt"]:
                if m["role"] == "user":
                    texts.append(m["content"])
        assert_no_eval_leakage(texts)

    with args.out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} DPO rows to {args.out}")
    print("(Optional) Filter by render-success with scripts/filter_dpo_by_render.py on HF Jobs.")


if __name__ == "__main__":
    main()
