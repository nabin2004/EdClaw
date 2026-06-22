"""Generate and parse Markdown-format LectureIR via LLM.

The IR is stored as a .md file with frontmatter + section headers, making it
human-readable and easy for LLMs to produce.  Each section becomes one IRChunk.

Format example
--------------
---
lecture_id: lec-01-introduction
title: Introduction to Vectors
---

## INTRO | pause_ms=700

Welcome to Introduction to Vectors...

---

## NARRATION | scene=what_is_a_vector | pause_ms=300

A vector is a mathematical object that has both magnitude and direction...

### ANIMATION
title: What Is a Vector?
description: Show an arrow from the origin to a point in 2D space, labeling magnitude and direction
visual_intent: labeled vector arrow diagram

---

## TRANSITION | pause_ms=200

Now let's look at how we add two vectors together.

---
"""

from __future__ import annotations

import re
from typing import Any

import frontmatter as _fm
from ollama import AsyncClient

from educlaw.tts.lecture_ir import AnimationSpec, IRChunk, LectureIR
from educlaw.tts.script import SegmentType

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)

# ## NARRATION | scene=some_slug | pause_ms=300
_SECTION_RE = re.compile(
    r"^##\s+([A-Z_]+)((?:\s*\|\s*[a-z_]+=\S+)*)\s*$",
    re.MULTILINE,
)
_KV_RE = re.compile(r"([a-z_]+)=(\S+)")
_ANIM_TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_ANIM_DESC_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_ANIM_INTENT_RE = re.compile(r"^visual_intent:\s*(.+)$", re.MULTILINE | re.IGNORECASE)

_TYPE_MAP: dict[str, SegmentType] = {
    "intro": "intro",
    "section_header": "section_header",
    "narration": "narration",
    "example": "example",
    "summary": "summary",
    "check_understanding": "check_understanding",
    "transition": "transition",
}

_DEFAULT_PAUSE: dict[str, int] = {
    "intro": 700,
    "section_header": 600,
    "summary": 500,
    "check_understanding": 500,
    "narration": 300,
    "example": 300,
    "transition": 200,
}

_SYSTEM = """\
You are an expert educational content producer.
Convert a lecture written in Markdown into a production Intermediate Representation (IR) in Markdown format.
This IR drives both audio narration (TTS) and Manim visual animations.

OUTPUT — write ONLY the following Markdown structure, with no extra text before or after:

---
lecture_id: <lecture_id>
title: <title>
---

## INTRO | pause_ms=700

<1-4 sentences of spoken English opening the lecture>

---

## SECTION_HEADER | pause_ms=600

<spoken transition into the first topic, e.g. "Let us begin by exploring...">

---

## NARRATION | scene=<scene_slug> | pause_ms=300

<1-4 sentences of natural spoken explanation>

### ANIMATION
title: <short scene title>
description: <one sentence: what to show on screen>
visual_intent: <Manim animation style, e.g. "gradient descent step diagram">

---

## EXAMPLE | scene=<scene_slug> | pause_ms=300

<1-4 sentences walking through a worked example>

### ANIMATION
title: <short scene title>
description: <one sentence: what to show on screen>
visual_intent: <Manim style, e.g. "step-by-step calculation reveal">

---

## TRANSITION | pause_ms=200

<one sentence bridging to the next topic>

---

## SUMMARY | pause_ms=500

<1-3 sentences recapping the key points>

---

CHUNK TYPES (use UPPERCASE in ## headers):
  INTRO              – opening hook and lecture title (exactly 1, always first)
  SECTION_HEADER     – spoken transition into a new major section
  NARRATION          – main explanation content
  EXAMPLE            – worked example or step-by-step walkthrough
  SUMMARY            – brief recap (1-2 at the end)
  CHECK_UNDERSTANDING – quiz or review question read aloud
  TRANSITION         – one-sentence bridge between topics

ATTRIBUTE RULES:
- scene=<slug>: snake_case slug for the Manim visual scene.
  Include for NARRATION and EXAMPLE only.
  OMIT for INTRO, TRANSITION, SUMMARY, CHECK_UNDERSTANDING, SECTION_HEADER.
- pause_ms: INTRO=700  SECTION_HEADER=600  SUMMARY=500  CHECK_UNDERSTANDING=500
            NARRATION=300  EXAMPLE=300  TRANSITION=200

TEXT RULES:
- Natural spoken English only — no LaTeX, no Markdown, no bullet dashes.
- Convert math to words: "x squared plus y squared" not "x^2 + y^2".
- Each chunk: 1-4 sentences, natural when a narrator reads it aloud.

ANIMATION BLOCK:
- Include ONLY for NARRATION and EXAMPLE chunks where a visual helps.
- Omit for INTRO, SECTION_HEADER, TRANSITION, SUMMARY, CHECK_UNDERSTANDING.
- Separate every chunk with a --- horizontal rule.
"""


async def generate_ir_markdown(
    client: AsyncClient,
    model: str,
    markdown: str,
    *,
    lecture_id: str,
    title: str,
    max_input_chars: int = 8000,
    think: bool | None = False,
) -> str:
    """Ask the LLM to convert lecture Markdown into a Markdown IR string."""
    md = markdown[:max_input_chars]
    user = (
        f"Lecture ID: {lecture_id}\n"
        f"Title: {title}\n\n"
        f"--- MARKDOWN ---\n{md}\n--- END ---\n\n"
        "Convert this lecture to the production IR Markdown now."
    )
    _extra: dict[str, Any] = {} if think is None else {"think": think}
    out = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0.2, "num_predict": 6000},
        **_extra,
    )
    msg = out.get("message") or {}
    raw = _THINK_RE.sub("", (msg.get("content") or "").strip()).strip()
    # Strip markdown fences if the model wrapped the output
    raw = re.sub(r"^```(?:markdown)?\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    return _ensure_frontmatter_first(raw.strip(), lecture_id=lecture_id, title=title)


def parse_ir_markdown(md_text: str) -> LectureIR:
    """Parse a Markdown IR document into a LectureIR object."""
    lecture_id = "unknown"
    title = "Untitled"
    content = md_text
    try:
        post = _fm.loads(md_text)
        lecture_id = str(post.metadata.get("lecture_id", "unknown"))
        title = str(post.metadata.get("title", "Untitled"))
        content = post.content
    except Exception:
        pass

    chunks: list[IRChunk] = []
    matches = list(_SECTION_RE.finditer(content))

    for idx, match in enumerate(matches):
        type_key = match.group(1).strip().lower()
        attrs_str = match.group(2) or ""

        section_start = match.end()
        section_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        section_text = content[section_start:section_end]

        attrs = dict(_KV_RE.findall(attrs_str))
        scene_hint: str | None = attrs.get("scene") or None
        try:
            pause_ms = int(attrs.get("pause_ms", _DEFAULT_PAUSE.get(type_key, 300)))
        except ValueError:
            pause_ms = _DEFAULT_PAUSE.get(type_key, 300)

        # Split off optional ### ANIMATION block
        anim_parts = re.split(
            r"^###\s+ANIMATION\s*$", section_text, flags=re.MULTILINE | re.IGNORECASE
        )
        text_part = re.sub(r"^\s*---\s*$", "", anim_parts[0], flags=re.MULTILINE).strip()

        animation: AnimationSpec | None = None
        if len(anim_parts) > 1:
            anim_block = anim_parts[1]
            t_m = _ANIM_TITLE_RE.search(anim_block)
            d_m = _ANIM_DESC_RE.search(anim_block)
            i_m = _ANIM_INTENT_RE.search(anim_block)
            if t_m:
                animation = AnimationSpec(
                    title=t_m.group(1).strip(),
                    description=(d_m.group(1).strip() if d_m else ""),
                    visual_intent=(i_m.group(1).strip() if i_m else ""),
                )

        chunk_type: SegmentType = _TYPE_MAP.get(type_key, "narration")  # type: ignore[assignment]
        if text_part:
            chunks.append(
                IRChunk(
                    id=len(chunks),
                    type=chunk_type,
                    text=text_part,
                    scene_hint=scene_hint,
                    pause_after_ms=pause_ms,
                    animation=animation,
                )
            )

    return LectureIR(lecture_id=lecture_id, title=title, chunks=chunks)


def ir_to_markdown(ir: LectureIR) -> str:
    """Serialize a LectureIR back to the Markdown IR format."""
    lines: list[str] = [
        "---",
        f"lecture_id: {ir.lecture_id}",
        f"title: {ir.title}",
        "---",
        "",
    ]
    for chunk in ir.chunks:
        header_parts = [f"## {chunk.type.upper()}"]
        if chunk.scene_hint:
            header_parts.append(f"scene={chunk.scene_hint}")
        header_parts.append(f"pause_ms={chunk.pause_after_ms}")
        lines.append(" | ".join(header_parts))
        lines.append("")
        lines.append(chunk.text)
        lines.append("")
        if chunk.animation:
            lines.append("### ANIMATION")
            lines.append(f"title: {chunk.animation.title}")
            lines.append(f"description: {chunk.animation.description}")
            lines.append(f"visual_intent: {chunk.animation.visual_intent}")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _ensure_frontmatter_first(text: str, *, lecture_id: str, title: str) -> str:
    """If the model output is missing frontmatter, prepend it."""
    if text.startswith("---"):
        return text
    # Try to find frontmatter anywhere in the output
    m = re.search(r"(---\nlecture_id:[\s\S]*?---)", text)
    if m:
        rest = text[m.end():].lstrip()
        return m.group(1) + "\n\n" + rest
    # Prepend a minimal frontmatter block
    fm_block = f"---\nlecture_id: {lecture_id}\ntitle: {title}\n---\n\n"
    return fm_block + text
