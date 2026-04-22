"""Shared prompts and constants for ManiBench training."""

MANIM_CE_SYSTEM = """You write Manim Community Edition (manim) Python code only.
Rules:
- Use: from manim import * or explicit imports from manim (latest CE API).
- Never use ManimGL-only APIs: no manim_imports_ext, no CONFIG dict on classes,
  no ShowCreation (use Create), no GraphScene/InteractiveScene as in GL —
  use Scene, Axes, etc.
- Prefer modern names: Create not ShowCreation; FadeIn with shift= not FadeInFrom.
- Target library: manim (community). Scripts must run with
  `manim render -ql script.py SceneName`.
"""

MANIM_GL_SYSTEM = """You write Manim (Grant Sanderson / 3b1b style) Python code.
You may use classic patterns: CONFIG dicts, ShowCreation, GraphScene,
manim_imports_ext when helpful."""

DEFAULT_TASK_DISTRIBUTION = {
    "direct_visualization": 0.40,
    "drift_sensitive": 0.20,
    "debugging": 0.20,
    "version_conflict_traps": 0.10,
    "multi_scene_narrative": 0.10,
}
