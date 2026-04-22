#!/usr/bin/env python3
"""Expand synthetic SFT rows (~5000) across the 5 ManiBench task-category weights."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.constants import DEFAULT_TASK_DISTRIBUTION, MANIM_CE_SYSTEM  # noqa: E402
from manibench.leakage import assert_no_eval_leakage  # noqa: E402
from manibench.prompt_seeds import generate_prompt  # noqa: E402


def _weighted_categories(rng: random.Random, n: int) -> list[str]:
    cats = list(DEFAULT_TASK_DISTRIBUTION.keys())
    weights = [DEFAULT_TASK_DISTRIBUTION[c] for c in cats]
    return rng.choices(cats, weights=weights, k=n)


def _scene_for(cat: str, idx: int) -> str:
    """Simple CE-valid stub scenes (executable in principle)."""
    base = f"Syn{idx}"
    if cat == "direct_visualization":
        return f'''from manim import *

class {base}(Scene):
    def construct(self):
        self.play(Write(Text("Direct {idx}", font_size=44)))
'''
    if cat == "drift_sensitive":
        return f'''from manim import *

class {base}(Scene):
    def construct(self):
        d = Dot(LEFT)
        self.play(Create(d))
        self.play(d.animate.move_to(RIGHT))
'''
    if cat == "debugging":
        return f'''from manim import *

class {base}(Scene):
    def construct(self):
        # Fixed: use Create instead of invalid call
        self.play(Create(Circle(radius=0.4)))
'''
    if cat == "version_conflict_traps":
        return f'''from manim import *

class {base}(Scene):
    def construct(self):
        self.play(Create(Square(side_length=0.8)))
'''
    return f'''from manim import *

class {base}(Scene):
    def construct(self):
        self.play(FadeIn(Text("Multi {idx}", font_size=36)))
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "manibench-synthetic-sft.jsonl")
    ap.add_argument("--skip-leak-check", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    cats = _weighted_categories(rng, args.count)
    rows = []
    for i, cat in enumerate(cats):
        user = generate_prompt(cat, i, rng)
        rows.append(
            {
                "messages": [
                    {"role": "system", "content": MANIM_CE_SYSTEM},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": _scene_for(cat, i).strip()},
                ],
                "task_type": cat,
                "source": "synthetic_stub",
            }
        )

    if not args.skip_leak_check:
        assert_no_eval_leakage([r["messages"][1]["content"] for r in rows])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} synthetic rows to {args.out}")


if __name__ == "__main__":
    main()
