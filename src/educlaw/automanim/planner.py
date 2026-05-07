"""ADK ``LlmAgent`` that emits a JSON ``VizPlan`` from lecture text."""

from __future__ import annotations

import json
import logging
from typing import Any

from google.adk.agents import LlmAgent

from educlaw.agent.model import build_model
from educlaw.automanim.schema import SceneSpec, VizPlan
from educlaw.config.settings import Settings

LOG = logging.getLogger(__name__)

_PLAN_INSTRUCTION = """You are a visualization planner for educational Manim videos.
Given a lecture (Markdown) and metadata, decide which short Manim scenes would help.
Respond with a single JSON object only (no markdown fences), shape:
{{
  "scenes": [
    {{
      "title": "short scene title",
      "description": "what to show on screen in one sentence",
      "visual_intent": "e.g. vector addition, matrix transform, eigenvector stretch"
    }}
  ]
}}
Rules:
- Prefer 1 to {max_scenes} scenes; pick only moments that benefit from motion/diagrams.
- Order scenes as they would appear in the lecture narrative.
- Each scene must be self-contained (one Manim Scene class can cover it in ~30–90s at low quality).
"""


def build_planner_agent(settings: Settings) -> LlmAgent:
    max_s = settings.automanim_max_scenes_per_lecture
    return LlmAgent(
        name="automanim_planner",
        model=build_model(settings),
        instruction=_PLAN_INSTRUCTION.format(max_scenes=max_s),
    )


def parse_viz_plan(raw: str, *, max_scenes: int) -> VizPlan:
    """Parse and cap planner JSON output."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        pos = exc.pos if exc.pos is not None else 0
        radius = 70
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        window_one_line = text[start:end].replace("\n", "\\n").replace("\r", "\\r")
        LOG.error(
            "automanim planner JSON parse failed: %s (line %s col %s char %s len_text=%s) "
            "near: %r | hint: invalid JSON escapes often come from LaTeX (e.g. \\lambda) "
            "or Windows paths; use doubled backslashes in strings or avoid backslashes.",
            exc.msg,
            exc.lineno,
            exc.colno,
            pos,
            len(text),
            window_one_line,
        )
        raise
    scenes_raw = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    scenes: list[SceneSpec] = []
    for item in scenes_raw[:max_scenes]:
        if isinstance(item, dict) and item.get("title"):
            scenes.append(
                SceneSpec(
                    title=str(item["title"]),
                    description=str(item.get("description") or ""),
                    visual_intent=str(item.get("visual_intent") or ""),
                )
            )
    return VizPlan(scenes=scenes)
