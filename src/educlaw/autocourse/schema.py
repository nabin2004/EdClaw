from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from educlaw.autolecture.schema import LectureOutline, LectureResult
from educlaw.automanim.schema import AutoManimEvent


class CoursePlan(BaseModel):
    title: str
    audience: str = "General learners"
    lectures: list[LectureOutline] = Field(default_factory=list)


class AutocourseEvent(BaseModel):
    kind: Literal["plan", "lecture_start", "lecture_done", "done", "error", "automanim"]
    course_title: str | None = None
    audience: str | None = None
    lecture_index: int | None = None
    lecture_title: str | None = None
    lecture_count: int | None = None
    result: LectureResult | None = None
    message: str | None = None
    automanim: AutoManimEvent | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
