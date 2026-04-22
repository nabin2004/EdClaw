from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IrAssessment(BaseModel):
    id: str
    prompt: str
    rubric: str
    kind: Literal["mcq", "short_answer", "code"] = "short_answer"


class IrBlock(BaseModel):
    kind: Literal["prose", "equation", "code", "video_ref"]
    text: str | None = None
    latex: str | None = None
    lang: str | None = None
    source: str | None = None
    video_id: str | None = None


class IrManimHint(BaseModel):
    scene: str
    hints: list[str] = Field(default_factory=list)


class IrNode(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9._-]+$")
    title: str
    objective: str
    prerequisites: list[str] = Field(default_factory=list)
    difficulty: int = Field(ge=1, le=5)
    modality: list[Literal["text", "video", "code", "quiz"]]
    body: list[IrBlock] = Field(default_factory=list)
    assessments: list[IrAssessment] = Field(default_factory=list)
    manim: IrManimHint | None = None
    tags: list[str] = Field(default_factory=list)
