#!/usr/bin/env python3
"""
Generate a Manim-specific SFT dataset for Gemma4 LoRA finetuning.

Each JSONL record is one (user-request -> Manim scene.py) pair in Gemma4 messages format:
  {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}

Two-stage per topic:
  Stage 1 - Ask LLM for N scene specs (title, description, visual_goal) as JSON
  Stage 2 - For each spec, generate complete Manim CE Python code

Usage:
  python scripts/generate_manim_dataset.py --runs 200 --workers 4
  python scripts/generate_manim_dataset.py --topics "calculus,linear algebra" --runs 50
  python scripts/generate_manim_dataset.py --runs 500 --scenes-per-topic 5 --dataset-out dataset/manim_sft.jsonl

Requires:
  pip install openai
  export OPENROUTER_API_KEY=...
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import os
import random
import re
import sys
import traceback
from pathlib import Path

try:
    from openai import AsyncOpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_MANIM_SYSTEM = """\
You write Manim Community Edition (manim) Python code only.

Rules:
- Import: `from manim import *` (latest CE API).
- Never use ManimGL-only APIs: no CONFIG dict, no ShowCreation (use Create),
  no GraphScene/InteractiveScene as in GL — use Scene, Axes, NumberPlane, etc.
- Modern names only: Create not ShowCreation; FadeIn with shift= not FadeInFrom.
- Output exactly one Python module containing exactly one subclass of Scene.
- No markdown fences. No explanation before or after the code.
- Scene class name must be PascalCase (e.g. EigenvalueScene, FourierScene).
- Use self.wait() so total animation time is at least 5 seconds.
- Prefer clean, readable animations over complex ones.
"""

_PLANNER_SYSTEM = """\
You are a Manim visualization planner for educational videos.

Given a math or science topic, return a JSON array of scene specifications.
Each element must have exactly these keys:
  "title"       – short PascalCase scene name (e.g. "VectorAddition")
  "description" – one sentence: what the scene shows
  "visual_goal" – one phrase: what the learner sees animated (e.g. "two vectors being added tip-to-tail")

Return ONLY a valid JSON array. No markdown fences. No explanation.
"""

# ---------------------------------------------------------------------------
# Topic pool (visually rich topics where Manim shines)
# ---------------------------------------------------------------------------

_DEFAULT_TOPICS: list[str] = [
    # Linear Algebra
    "Vector Addition and Scalar Multiplication",
    "Matrix Multiplication as Linear Transformation",
    "Eigenvalues and Eigenvectors",
    "Gram-Schmidt Orthogonalization",
    "Singular Value Decomposition",
    "Null Space and Column Space",
    "Change of Basis",
    "Dot Product and Projections",
    "Determinant as Area and Volume Scaling",
    # Calculus
    "Limit Definition of the Derivative",
    "Riemann Sum Convergence to an Integral",
    "Fundamental Theorem of Calculus",
    "Chain Rule and Composite Functions",
    "Taylor Series Approximation",
    "Gradient and Directional Derivative",
    "Gradient Descent on a Loss Surface",
    "Divergence and Curl of a Vector Field",
    "Integration by Parts Geometric Interpretation",
    # Probability and Statistics
    "Central Limit Theorem via Sampling",
    "Bayes Theorem with Venn Diagrams",
    "Normal Distribution and Standard Deviations",
    "Markov Chain State Transitions",
    "Law of Large Numbers",
    "Entropy and Information Gain",
    "Hypothesis Testing and p-values",
    # Machine Learning
    "Backpropagation through a Neural Network",
    "Stochastic Gradient Descent on Loss Surface",
    "K-Means Clustering Iterations",
    "Decision Tree Splitting Criterion",
    "Support Vector Machine Margin Maximization",
    "PCA Dimensionality Reduction",
    "Sigmoid and Softmax Activation Functions",
    "Convolutional Filter Sliding Over an Image",
    "Attention Mechanism as Dot-Product Weighting",
    "Bias-Variance Tradeoff Visualization",
    # Physics
    "Simple Harmonic Oscillator",
    "Projectile Motion with Air Resistance",
    "Electric Field Lines from Point Charges",
    "Wave Superposition and Interference",
    "Fourier Series Approximation of a Square Wave",
    "Lorentz Force on a Moving Charge",
    "Newton's Laws of Motion",
    "Conservation of Momentum Collisions",
    "Gravitational Potential Well",
    "Standing Wave Modes on a String",
    # Algorithms and CS
    "Binary Search on a Sorted Array",
    "Bubble Sort Swapping Elements",
    "Merge Sort Divide and Conquer",
    "Breadth-First Search Tree Traversal",
    "Dijkstra's Shortest Path Algorithm",
    "Hash Table Collision Resolution",
    "Dynamic Programming Fibonacci Table",
    "Recursion Tree for Tower of Hanoi",
    # Number Theory / Discrete Math
    "Sieve of Eratosthenes",
    "Euclidean Algorithm for GCD",
    "Modular Arithmetic Clock",
    "Graph Coloring and Chromatic Number",
    "Pigeonhole Principle Example",
    # Geometry / Topology
    "Pythagorean Theorem Geometric Proof",
    "Unit Circle and Trigonometric Functions",
    "Inscribed Angle Theorem",
    "Euler's Identity on the Complex Plane",
    "Möbius Strip Construction",
    "Fractal Iteration (Koch Snowflake)",
]

# ---------------------------------------------------------------------------
# User-prompt templates (diversity for training)
# ---------------------------------------------------------------------------

_USER_TEMPLATES: list[str] = [
    "Write a Manim animation scene titled '{title}' for a lecture on {topic}.\n\n{description}",
    "Generate Manim CE Python for a scene called '{title}'.\n\nTopic: {topic}\nGoal: {visual_goal}",
    "Create a Manim scene that {visual_goal}.\n\nScene title: {title}\nLecture topic: {topic}",
    "I need a Manim scene named '{title}' for an educational video about {topic}.\n{description} Show this visually with animation.",
    "Topic: {topic}\nScene: {title}\n\nWrite Manim Python code that {visual_goal}.",
    "Produce a self-contained Manim animation for the following specification:\n- Title: {title}\n- Topic: {topic}\n- What to show: {description}",
    "Educational Manim scene request:\nTitle: {title}\nConcept: {topic}\nAnimation goal: {visual_goal}\n\nReturn only the Python code.",
    "Write Manim code for a scene titled '{title}' that {visual_goal}. This is for a lecture on {topic}.",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _build_user_prompt(spec: dict, topic: str) -> str:
    tmpl = random.choice(_USER_TEMPLATES)
    return tmpl.format(
        title=spec.get("title", "AnimationScene"),
        topic=topic,
        description=spec.get("description", ""),
        visual_goal=spec.get("visual_goal", ""),
    )


def _expand_topics(base: list[str], target: int) -> list[str]:
    out: list[str] = []
    while len(out) < target:
        shuffled = base[:]
        random.shuffle(shuffled)
        out.extend(shuffled)
    return out[:target]


# ---------------------------------------------------------------------------
# LLM calls
# ---------------------------------------------------------------------------

async def _plan_scenes(
    client: AsyncOpenAI,
    model: str,
    topic: str,
    n_scenes: int,
) -> list[dict]:
    """Stage 1: Ask LLM for scene specifications (JSON array)."""
    user_msg = (
        f"Topic: {topic}\n\n"
        f"Generate exactly {n_scenes} scene specifications for Manim animations "
        "that visually explain key concepts in this topic. "
        "Return a JSON array only."
    )
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _PLANNER_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.8,
        max_tokens=1024,
    )
    raw = resp.choices[0].message.content or ""
    raw = _strip_fences(raw)
    # Remove stray leading text before '['
    bracket = raw.find("[")
    if bracket > 0:
        raw = raw[bracket:]
    try:
        specs = json.loads(raw)
        if not isinstance(specs, list):
            return []
        return [s for s in specs if isinstance(s, dict) and s.get("title")][:n_scenes]
    except json.JSONDecodeError:
        return []


async def _generate_scene_code(
    client: AsyncOpenAI,
    model: str,
    spec: dict,
    topic: str,
) -> str | None:
    """Stage 2: Generate Manim Python code for one scene spec."""
    user_prompt = _build_user_prompt(spec, topic)
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _MANIM_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=2048,
    )
    code = (resp.choices[0].message.content or "").strip()
    code = _strip_fences(code)
    if not code or "class" not in code or "def construct" not in code:
        return None
    if not _is_valid_python(code):
        return None
    return code


# ---------------------------------------------------------------------------
# Per-run worker
# ---------------------------------------------------------------------------

async def _run_one(
    run_idx: int,
    topic: str,
    client: AsyncOpenAI,
    model: str,
    n_scenes: int,
    dataset_out: Path,
    sem: asyncio.Semaphore,
) -> int:
    """Generate up to n_scenes Manim training examples for one topic. Returns count written."""
    label = f"[{run_idx:04d}/{topic[:50]}]"
    async with sem:
        try:
            specs = await _plan_scenes(client, model, topic, n_scenes)
            if not specs:
                print(f"{label} -> planner returned no specs, skipping")
                return 0

            # Generate code for each spec concurrently within the run
            tasks = [
                _generate_scene_code(client, model, spec, topic)
                for spec in specs
            ]
            codes = await asyncio.gather(*tasks, return_exceptions=True)

            written = 0
            for spec, code in zip(specs, codes):
                if isinstance(code, Exception) or not code:
                    continue
                user_prompt = _build_user_prompt(spec, topic)
                record = {
                    "messages": [
                        {"role": "system", "content": _MANIM_SYSTEM.strip()},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": code},
                    ],
                    "topic": topic,
                    "scene_title": spec.get("title", ""),
                    "source": f"manim_sft/{model}",
                }
                _write_jsonl(dataset_out, record)
                written += 1

            print(f"{label} -> {written}/{len(specs)} scenes written")
            return written

        except Exception:  # noqa: BLE001
            print(f"{label} ERROR:")
            traceback.print_exc()
            return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def _async_main(args: argparse.Namespace) -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY or OPENAI_API_KEY", file=sys.stderr)
        return 1

    base_url = (
        "https://openrouter.ai/api/v1"
        if os.environ.get("OPENROUTER_API_KEY")
        else None
    )
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    if args.topics:
        base_topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    else:
        base_topics = _DEFAULT_TOPICS

    topics = _expand_topics(base_topics, args.runs)

    dataset_out = Path(args.dataset_out).expanduser().resolve()
    dataset_out.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"Manim SFT dataset generation: {args.runs} runs, "
        f"{args.scenes_per_topic} scenes/topic, {args.workers} workers, "
        f"model={args.model}"
    )
    print(f"Output: {dataset_out}")

    sem = asyncio.Semaphore(args.workers)
    tasks = [
        _run_one(
            run_idx=i,
            topic=topic,
            client=client,
            model=args.model,
            n_scenes=args.scenes_per_topic,
            dataset_out=dataset_out,
            sem=sem,
        )
        for i, topic in enumerate(topics[: args.runs], start=1)
    ]

    results = await asyncio.gather(*tasks)
    total = sum(r for r in results if isinstance(r, int))
    n_ok = sum(1 for r in results if isinstance(r, int) and r > 0)
    n_fail = len(results) - n_ok
    print(f"\nDone: {n_ok}/{len(results)} runs succeeded, {n_fail} failed.")
    print(f"Total training records written: {total}")
    print(f"Dataset: {dataset_out}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--topics",
        default=None,
        help="Comma-separated list of topics (default: built-in visual-math pool).",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=100,
        metavar="N",
        help="Total number of topics to process (default: 100).",
    )
    p.add_argument(
        "--scenes-per-topic",
        type=int,
        default=4,
        metavar="N",
        dest="scenes_per_topic",
        help="Manim scenes to generate per topic (default: 4).",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=4,
        metavar="N",
        help="Concurrent topic workers (default: 4).",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("OPENROUTER_MODEL", "moonshotai/kimi-k2.5"),
        help="Model ID (default: moonshotai/kimi-k2.5 or $OPENROUTER_MODEL).",
    )
    p.add_argument(
        "--dataset-out",
        default="dataset/manim_sft.jsonl",
        metavar="FILE",
        help="JSONL output path (default: dataset/manim_sft.jsonl).",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main()
