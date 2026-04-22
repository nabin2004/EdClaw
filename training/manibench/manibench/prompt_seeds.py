"""Rich, reproducible user prompts per ManiBench task category for SFT / teacher distillation."""

from __future__ import annotations

import random

from manibench.constants import DEFAULT_TASK_DISTRIBUTION

# Topic / angle seeds per category (natural-language instructions for Manim CE).
_DIRECT_TOPICS: list[str] = [
    "Visualize the quadratic formula x = (-b ± √(b²-4ac)) / (2a) with labels for a, b, c.",
    "Animate a unit circle with sin(θ) and cos(θ) as projections on axes, updating as θ sweeps.",
    "Show the Pythagorean theorem with a right triangle and squares on each side.",
    "Demonstrate the derivative of x² as the limit of secant slopes approaching a tangent at a point.",
    "Plot y = e^x and y = ln(x) as reflections across y = x.",
    "Animate a Riemann sum with rectangles under a smooth curve f(x).",
    "Show vector addition in 2D: two arrows from origin and their sum parallelogram.",
    "Visualize matrix multiplication (2×2) acting on a unit square as a shear + scale.",
    "Animate a simple pendulum: rod, bob, and small-angle approximation text.",
    "Show Bayes' rule P(A|B) with a Venn-style or partitioned rectangle update.",
    "Demonstrate the chain rule with nested function boxes f(g(x)).",
    "Animate sorting: compare two bars and swap when out of order (bubble step).",
    "Show a number line with integer addition using colored jumps.",
    "Visualize complex multiplication z·w as rotation and scaling in the complex plane.",
    "Animate a Fourier series partial sum approaching a square wave.",
]

_DRIFT_TOPICS: list[str] = [
    "A dot moves smoothly from LEFT to RIGHT while a label tracks its position; use animate() not jump cuts.",
    "Fade in axes, then grow a graph along the x-axis with LaggedStart so motion feels continuous.",
    "Show a ValueTracker driving a line's slope; the line must update every frame without discrete jumps.",
    "Animate a circle's radius growing while arc length text updates in sync with the arc.",
    "Two objects: one follows a parametric path (circle), the other linear interpolation; both must stay smooth.",
    "Demonstrate always_redraw for a tangent line that follows a moving point on a curve.",
    "A bar chart where bars grow with rate_func=smooth; heights must match final labels.",
    "Show a camera-style zoom into a small region of a diagram without popping the scale.",
    "Animate color interpolation on a shape while it moves along a path.",
    "Use updaters so a brace stays attached to a changing interval on the number line.",
]

_DEBUG_TOPICS: list[str] = [
    "Fix this broken snippet: it uses ShowCreation — rewrite for Manim CE using Create.\n```python\nfrom manim import *\nclass Bug(Scene):\n    def construct(self):\n        self.play(ShowCreation(Circle()))\n```",
    "This code fails because CONFIG is used on the Scene class — remove CONFIG and use explicit constructor args.\n```python\nfrom manim import *\nclass Bug(Scene):\n    CONFIG = {\"run_time\": 2}\n    def construct(self):\n        self.play(Create(Square()))\n```",
    "Replace manim_imports_ext with standard CE imports and make the scene valid.\n```python\nfrom manim_imports_ext import *\nclass Bug(Scene):\n    def construct(self):\n        self.play(ShowCreation(Dot()))\n```",
    "The scene uses FadeInFrom which is outdated — use FadeIn with shift= instead.\n```python\nfrom manim import *\nclass Bug(Scene):\n    def construct(self):\n        self.play(FadeInFrom(Text(\"Hi\"), direction=UP))\n```",
    "Fix: GraphScene is not available in CE — use Axes and plot() to draw y = sin(x).",
    "This uses self.add_sound — remove audio and keep only visual play() calls for CE.",
    "The code references InteractiveScene — rewrite as a plain Scene with buttons replaced by static labels.",
    "Fix invalid nesting: self.play expects Mobjects; wrap Text and Circle in a VGroup if needed.",
    "Scene runs but nothing appears: ensure at least one self.play with visible mobjects.",
    "Replace deprecated ShowCreation with Create throughout the file snippet below.\n```python\nfrom manim import *\nclass Bug(Scene):\n    def construct(self):\n        self.play(ShowCreation(Line(LEFT, RIGHT)))\n```",
]

_VCER_TOPICS: list[str] = [
    "Port this GL-style idea to Manim CE only: square appearing edge-by-edge — do NOT use ShowCreation or CONFIG.",
    "Write CE code for 'write title then underline' without manim_imports_ext or GraphScene.",
    "Animate axes + plot without GraphScene; use Axes and plot_line_graph or plot().",
    "Show a transformation from a GL tutorial that used ShowCreation — use Create and CE-safe APIs only.",
    "Demonstrate CE equivalent of 'FadeInFromLarge' using FadeIn with scale_factor.",
    "Build a minimal Scene that would fail VCER if written in GL style — but your answer must be clean CE.",
    "Explain in comments why you avoid manim_imports_ext, then implement a simple circle + label.",
    "Rewrite a classic 'CONFIG = {...}' pattern using explicit attributes on Mobjects in CE.",
    "Use only `from manim import *` or explicit manim imports; no Grant Sanderson extension modules.",
    "Create a scene that draws a brace between two moving points using always_redraw (CE).",
]

_MULTI_TOPICS: list[str] = [
    "Part 1: title card. Part 2: definition on screen. Part 3: short example animation — use clear section transitions.",
    "Story: problem statement → diagram → conclusion; use FadeOut between sections.",
    "Three labeled phases: Setup, Derivation, Takeaway — each with distinct mobjects.",
    "Introduce axes, then add a curve, then highlight an area under the curve in a third beat.",
    "Multi-step proof: state theorem, show construction, reveal QED — minimal clutter between steps.",
    "Lecture-style: bullet list appears, then morphs into a single equation, then animates a graph.",
    "Two scenes in one file is NOT required — one Scene with three clear construct() segments separated by self.wait.",
    "Narrative: clock → formula for period → pendulum sketch; tie visuals with short on-screen captions.",
    "Compare two methods side-by-side, then fade one away leaving the winner.",
    "Build tension: wrong answer crossed out, then correct answer with emphasis animation.",
]


def generate_prompt(category: str, idx: int, rng: random.Random) -> str:
    """Return a natural-language user prompt for the given task category."""
    if category == "direct_visualization":
        topic = rng.choice(_DIRECT_TOPICS)
        angle = rng.choice(
            [
                "Keep it under ~40 lines.",
                "Prefer MathTex/Tex where appropriate.",
                "Use only Manim Community Edition APIs.",
                "Make colors readable on a dark background.",
            ]
        )
        return (
            f"[direct_visualization] Task #{idx}. {topic} "
            f"{angle} Output a single Scene subclass named `GeneratedScene{idx}` (or any valid Scene name) "
            "that renders with `manim render -ql script.py SceneName`."
        )

    if category == "drift_sensitive":
        topic = rng.choice(_DRIFT_TOPICS)
        return (
            f"[drift_sensitive] Task #{idx}. {topic} "
            "Avoid discrete position jumps between adjacent animation steps. "
            "Output one complete Manim CE Scene file."
        )

    if category == "debugging":
        topic = rng.choice(_DEBUG_TOPICS)
        return f"[debugging] Task #{idx}. {topic} Output the full corrected Manim CE script."

    if category == "version_conflict_traps":
        topic = rng.choice(_VCER_TOPICS)
        return (
            f"[version_conflict_traps] Task #{idx}. {topic} "
            "Ensure the final code passes a GL-vs-CE static checker (no GL-only imports or APIs)."
        )

    if category == "multi_scene_narrative":
        topic = rng.choice(_MULTI_TOPICS)
        return (
            f"[multi_scene_narrative] Task #{idx}. {topic} "
            "Use one Scene class with a coherent multi-beat construct()."
        )

    # Fallback for unknown category
    return (
        f"[{category}] Task #{idx}. Generate a minimal Manim CE Scene that demonstrates "
        "the requested animation pattern. Output runnable Python only."
    )


def weighted_prompts(n: int, rng: random.Random) -> list[tuple[str, str]]:
    """Sample ``n`` (category, user_prompt) pairs using ``DEFAULT_TASK_DISTRIBUTION``."""
    cats = list(DEFAULT_TASK_DISTRIBUTION.keys())
    weights = [DEFAULT_TASK_DISTRIBUTION[c] for c in cats]
    chosen = rng.choices(cats, weights=weights, k=n)
    return [(cat, generate_prompt(cat, i, rng)) for i, cat in enumerate(chosen)]
