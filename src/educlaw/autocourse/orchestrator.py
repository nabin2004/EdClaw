from __future__ import annotations

import json
from collections.abc import AsyncIterator

from ollama import AsyncClient
from pydantic import ValidationError

from educlaw.autocourse.schema import AutocourseEvent, CoursePlan
from educlaw.autolecture.generator import generate_lecture
from educlaw.automanim.orchestrator import run_automanim
from educlaw.config.settings import Settings
from educlaw.safety.shield import NoopShield, Shield

_MAX_LECTURES = 8


class CoursePlanningFailed(Exception):
    """Raised when ``plan_course`` cannot produce a valid ``CoursePlan``."""

    def __init__(self, message: str, *, raw_preview: str | None = None) -> None:
        super().__init__(message)
        self.raw_preview = raw_preview or ""


_PLAN_SYSTEM = f"""You are a curriculum designer. The user describes what they want to learn \
or teach.
Respond with a single JSON object only (no markdown fences), using this shape:
{{
  "title": "short course title",
  "audience": "who this is for",
  "lectures": [
    {{
      "title": "lecture title",
      "objectives": ["objective 1", "objective 2"],
      "key_topics": ["topic a", "topic b"],
      "estimated_minutes": 30
    }}
  ]
}}
Rules:
- Include between 2 and {_MAX_LECTURES} lectures in "lectures". If the user explicitly asks for \
exactly N lectures and N is between 2 and {_MAX_LECTURES} (inclusive), include exactly N.
- Order lectures so prerequisites come first.
- Objectives and key_topics must be non-empty arrays for each lecture.
- estimated_minutes is optional (integer or null).
"""


async def plan_course(
    client: AsyncClient,
    settings: Settings,
    user_prompt: str,
) -> CoursePlan:
    """Call Ollama once and return a validated ``CoursePlan`` (raises ``CoursePlanningFailed``)."""
    raw: str | None = None
    try:
        out = await client.chat(
            model=settings.model_id,
            messages=[
                {"role": "system", "content": _PLAN_SYSTEM},
                {"role": "user", "content": user_prompt.strip()},
            ],
            format="json",
            options={"temperature": 0.25, "num_predict": 4096},
        )
        msg = out.get("message") or {}
        raw = (msg.get("content") or "").strip()
        if not raw:
            raise CoursePlanningFailed("Empty plan from model.")
        plan = CoursePlan.model_validate_json(raw)
    except CoursePlanningFailed:
        raise
    except (json.JSONDecodeError, ValidationError) as e:
        raise CoursePlanningFailed(
            f"Invalid course plan: {e}",
            raw_preview=(raw or "")[:500],
        ) from e
    except Exception as e:  # noqa: BLE001
        raise CoursePlanningFailed(f"Course planning failed: {e!s}") from e

    if not plan.lectures:
        raise CoursePlanningFailed("Course plan has no lectures.")
    return plan


async def run_autocourse(
    user_prompt: str,
    settings: Settings,
    client: AsyncClient,
) -> AsyncIterator[AutocourseEvent]:
    try:
        plan = await plan_course(client, settings, user_prompt)
    except CoursePlanningFailed as e:
        yield AutocourseEvent(
            kind="error",
            message=str(e),
            extra={"raw_preview": e.raw_preview},
        )
        return

    lectures = plan.lectures[:_MAX_LECTURES]
    if not lectures:
        yield AutocourseEvent(kind="error", message="Course plan has no lectures.")
        return

    yield AutocourseEvent(
        kind="plan",
        course_title=plan.title,
        audience=plan.audience,
        lecture_count=len(lectures),
    )

    prior_titles: list[str] = []
    n = len(lectures)
    shield: Shield | NoopShield | None = None
    if settings.automanim_enabled:
        shield = (
            Shield(client, model=settings.shield_model) if settings.shield_enabled else NoopShield()
        )

    for i, outline in enumerate(lectures, start=1):
        yield AutocourseEvent(
            kind="lecture_start",
            course_title=plan.title,
            lecture_index=i,
            lecture_title=outline.title,
            lecture_count=n,
        )
        try:
            result = await generate_lecture(
                client,
                settings.model_id,
                outline,
                course_title=plan.title,
                lecture_index=i,
                lecture_count=n,
                prior_lecture_titles=list(prior_titles),
            )
        except Exception as e:  # noqa: BLE001
            yield AutocourseEvent(
                kind="error",
                message=f"Lecture {i} generation failed: {e!s}",
                lecture_index=i,
                lecture_title=outline.title,
            )
            return

        prior_titles.append(outline.title)
        yield AutocourseEvent(
            kind="lecture_done",
            course_title=plan.title,
            lecture_index=i,
            lecture_title=outline.title,
            lecture_count=n,
            result=result,
        )

        if settings.automanim_enabled and shield is not None:
            try:
                async for am_ev in run_automanim(
                    result.markdown,
                    dict(result.ir_suggestion),
                    settings,
                    shield,
                    ollama=client,
                    output_root=settings.automanim_output_dir,
                ):
                    yield AutocourseEvent(
                        kind="automanim",
                        course_title=plan.title,
                        lecture_index=i,
                        lecture_title=outline.title,
                        lecture_count=n,
                        automanim=am_ev,
                    )
            except Exception as e:  # noqa: BLE001 — non-fatal; continue course
                yield AutocourseEvent(
                    kind="error",
                    course_title=plan.title,
                    lecture_index=i,
                    lecture_title=outline.title,
                    lecture_count=n,
                    message=f"AutoManim failed: {e!s}",
                )

    yield AutocourseEvent(
        kind="done",
        course_title=plan.title,
        lecture_count=n,
        message="Autocourse finished.",
    )
