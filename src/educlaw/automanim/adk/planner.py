"""ADK ``LlmAgent`` that emits a JSON ``VizPlan`` from subtitle blocks."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

_BAD_BACKSLASH = re.compile(r'\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})')

from google.adk.agents import LlmAgent

from educlaw.agent.model import build_model
from educlaw.automanim.adk.schema import SceneSpec, VizPlan
from educlaw.config.settings import Settings

if TYPE_CHECKING:
    from educlaw.tts.md_to_srt import SubtitleBlock

LOG = logging.getLogger(__name__)

_PLAN_INSTRUCTION = """\
You are a visualization planner for educational Manim videos.

You receive a lecture in Markdown and a numbered list of subtitle blocks (each with its \
display duration in seconds). Decide which subtitle blocks need a Manim animation to \
support understanding.

Respond with a single JSON object only (no markdown fences):
{{
  "scenes": [
    {{
      "title": "short scene title",
      "description": "what to show on screen in one sentence",
      "visual_intent": "e.g. vector addition diagram, matrix row operations",
      "subtitle_index": <1-based integer matching the subtitle block number>,
      "duration_sec": <float, copy the duration_sec from that subtitle block>
    }}
  ]
}}

Rules:
- Choose at most {max_scenes} subtitle blocks to animate.
- Only animate blocks that genuinely benefit from a diagram or motion graphic.
- Skip blocks that are introductions, transitions, questions, or summaries.
- Each scene must be self-contained (one Manim Scene subclass).
- Order scenes by subtitle_index (ascending).
"""


def build_planner_agent(settings: Settings) -> LlmAgent:
    max_s = settings.automanim_max_scenes_per_lecture
    return LlmAgent(
        name="automanim_planner",
        model=build_model(settings),
        instruction=_PLAN_INSTRUCTION.format(max_scenes=max_s),
    )


def subtitle_blocks_to_planner_input(
    lecture_markdown: str,
    subtitle_blocks: list[SubtitleBlock],
) -> str:
    """Build the user message for the planner from subtitle blocks."""
    block_lines: list[str] = []
    for b in subtitle_blocks:
        block_lines.append(
            f"[{b.index}] duration={b.duration_sec():.1f}s | {b.tts_text}"
        )
    blocks_text = "\n".join(block_lines)
    return (
        f"Lecture (Markdown):\n{lecture_markdown[:20_000]}\n\n"
        f"Subtitle blocks:\n{blocks_text}"
    )


def parse_viz_plan(raw: str, *, max_scenes: int, subtitle_blocks: list[SubtitleBlock]) -> VizPlan:
    """Parse planner JSON; enrich SceneSpec with subtitle data."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(_BAD_BACKSLASH.sub(r"\\\\", text))
    except json.JSONDecodeError as exc:
        pos = exc.pos if exc.pos is not None else 0
        radius = 70
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        window_one_line = text[start:end].replace("\n", "\\n").replace("\r", "\\r")
        LOG.error(
            "automanim planner JSON parse failed: %s (line %s col %s char %s len_text=%s) "
            "near: %r",
            exc.msg, exc.lineno, exc.colno, pos, len(text), window_one_line,
        )
        raise

    block_by_idx = {b.index: b for b in subtitle_blocks}
    scenes_raw = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    scenes: list[SceneSpec] = []
    for item in scenes_raw[:max_scenes]:
        if not (isinstance(item, dict) and item.get("title")):
            continue
        sub_idx: int | None = item.get("subtitle_index")
        sub_block = block_by_idx.get(sub_idx) if sub_idx else None
        dur = float(item.get("duration_sec") or (sub_block.duration_sec() if sub_block else 5.0))
        scenes.append(SceneSpec(
            title=str(item["title"]),
            description=str(item.get("description") or ""),
            visual_intent=str(item.get("visual_intent") or ""),
            subtitle_index=sub_idx,
            duration_sec=max(2.0, min(90.0, dur)),
            subtitle_text=sub_block.tts_text if sub_block else "",
        ))
    return VizPlan(scenes=scenes)
