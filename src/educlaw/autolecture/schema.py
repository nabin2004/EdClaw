from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LectureOutline(BaseModel):
    title: str
    objectives: list[str] = Field(default_factory=list)
    key_topics: list[str] = Field(default_factory=list)
    estimated_minutes: int | None = None


class LectureResult(BaseModel):
    """Full lecture text plus optional IR-shaped metadata for future export."""

    markdown: str
    ir_suggestion: dict[str, Any] = Field(default_factory=dict)
