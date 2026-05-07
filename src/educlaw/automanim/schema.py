from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SceneSpec(BaseModel):
    """One visual scene the planner wants rendered as a Manim ``Scene``."""

    title: str
    description: str = ""
    visual_intent: str = ""


class VizPlan(BaseModel):
    """Planner output: ordered list of scenes to generate."""

    scenes: list[SceneSpec] = Field(default_factory=list)


class RenderArtifact(BaseModel):
    """Path to a rendered video on disk."""

    artifact_path: str
    scene_name: str
    exit_code: int = 0
    stderr_tail: str = ""


AutoManimKind = Literal[
    "phase",
    "plan",
    "scene_start",
    "codegen",
    "critic",
    "render",
    "scene_done",
    "done",
    "error",
]


class AutoManimEvent(BaseModel):
    """Streaming pipeline event. ``phase`` rows are human-readable breadcrumbs (UI / logs)."""

    kind: AutoManimKind
    message: str | None = None
    lecture_id: str | None = None
    scene_index: int | None = None
    scene_title: str | None = None
    source_preview: str | None = None
    artifact: RenderArtifact | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
