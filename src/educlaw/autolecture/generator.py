from __future__ import annotations

import re

from ollama import AsyncClient

from educlaw.autolecture.schema import LectureOutline, LectureResult

_LECTURE_SYSTEM = """You are an expert instructor writing one complete lecture in Markdown.
Structure the lecture with clear headings (##, ###), not a YAML frontmatter block.
Include, in order:
1. A short hook motivating why this matters
2. Core explanations (definitions, intuition, steps)
3. One concrete worked example or walkthrough
4. A brief recap
5. A "Check your understanding" section with 2–3 questions \
(no answers required in the lecture body)

Be accurate, concise, and classroom-ready. Use Markdown lists and bold for key terms where \
helpful."""


def _slug_id(title: str, index: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base = base[:48] or "lecture"
    return f"{base}.{index}"


async def generate_lecture(
    client: AsyncClient,
    model: str,
    outline: LectureOutline,
    *,
    course_title: str,
    lecture_index: int,
    lecture_count: int,
    prior_lecture_titles: list[str],
) -> LectureResult:
    prior = (
        ", ".join(prior_lecture_titles)
        if prior_lecture_titles
        else "(none — this is early in the course)"
    )
    objectives = (
        "\n".join(f"- {o}" for o in outline.objectives) or "- (derive from title and topics)"
    )
    topics = "\n".join(f"- {t}" for t in outline.key_topics) or "- (infer from title)"

    user = f"""Course: {course_title}
You are writing lecture {lecture_index} of {lecture_count} in this course.
Prior lecture titles covered so far: {prior}

This lecture's title: {outline.title}

Learning objectives:
{objectives}

Key topics to cover:
{topics}
"""

    out = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _LECTURE_SYSTEM},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0.35, "num_predict": 8192},
    )
    msg = out.get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text:
        text = "(Model returned an empty lecture.)"

    node_id = _slug_id(outline.title, lecture_index)
    ir_suggestion: dict[str, object] = {
        "id": node_id,
        "title": outline.title,
        "objective": "; ".join(outline.objectives) if outline.objectives else outline.title,
        "prerequisites": [],
        "difficulty": 3,
        "modality": ["text", "quiz"],
        "tags": ["generated", "autolecture"],
    }

    return LectureResult(markdown=text, ir_suggestion=ir_suggestion)
