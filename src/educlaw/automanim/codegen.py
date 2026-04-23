"""ADK ``LlmAgent`` that emits Manim CE Python for one ``SceneSpec``."""

from __future__ import annotations

import json

from google.adk.agents import LlmAgent

from educlaw.agent.model import build_model
from educlaw.automanim.constants import MANIM_CE_SYSTEM
from educlaw.automanim.schema import SceneSpec
from educlaw.config.settings import Settings


def build_codegen_agent(settings: Settings) -> LlmAgent:
    return LlmAgent(
        name="automanim_codegen",
        model=build_model(settings),
        instruction=MANIM_CE_SYSTEM
        + "\n\nYou output exactly one Python module containing exactly one subclass of Scene. "
        "No markdown fences. No explanation before or after the code.",
    )


def build_codegen_user_message(
    scene: SceneSpec,
    *,
    lecture_title: str,
    revision_feedback: str | None = None,
) -> str:
    payload = {
        "lecture_title": lecture_title,
        "scene_title": scene.title,
        "description": scene.description,
        "visual_intent": scene.visual_intent,
    }
    spec_json = json.dumps(payload, indent=2)
    base = (
        "Generate Manim CE Python for this scene specification (JSON):\n"
        f"{spec_json}\n"
        "The Scene class name should be PascalCase and unique (e.g. GeneratedScene1).\n"
        "Use concise animations suitable for preview quality (-ql).\n"
    )
    if revision_feedback:
        base += f"\n\nPrevious attempt failed review. Fix the issues:\n{revision_feedback}\n"
    return base
