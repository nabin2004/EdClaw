"""Convert lecture Markdown to a unified LectureIR (TTS + animation specs) via LLM."""

from __future__ import annotations

import io
import json
import re
import wave
from typing import Any

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_BAD_BACKSLASH = re.compile(r'\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})')

from ollama import AsyncClient

from educlaw.tts.contract import TTSRequest
from educlaw.tts.lecture_ir import AnimationSpec, IRChunk, LectureIR

_SYSTEM = """\
You are an expert educational content producer.
Convert a lecture written in Markdown into a unified production IR as JSON.
This IR drives both audio narration (TTS) and Manim visual animations.

RULES:
- Write ONLY natural spoken English in `text`. No LaTeX, no Markdown syntax, no bullet dashes.
- Convert math to words: write "x squared plus y squared" not "x^2 + y^2".
- Each chunk: 1-4 sentences, natural when read aloud by a narrator.
- Chunk types:
    intro            – opening hook and lecture title (exactly 1, at start)
    section_header   – spoken transition into a new section ("Now let's explore...")
    narration        – main explanation content
    example          – worked examples or walkthroughs
    summary          – brief recap at the end
    check_understanding – quiz/review questions read aloud
    transition       – short bridge between topics (1 sentence)
- scene_hint: snake_case slug for the visual scene this chunk corresponds to.
  Use null for intro, transition, summary, check_understanding.
  For content chunks, derive from the topic (e.g. "field_axioms", "gradient_step").
- pause_after_ms: intro→700, section_header→600, summary/check_understanding→500,
  narration/example→300, transition→200
- animation: For narration and example chunks that benefit from visualization, provide:
    title: short scene title
    description: what to show on screen (1 sentence, concrete)
    visual_intent: Manim animation style (e.g. "axiom list reveal", "vector addition diagram")
  Set animation to null for: intro, transition, summary, check_understanding, section_header.

Return ONLY valid JSON, no markdown fences, no explanation.

SCHEMA:
{
  "lecture_id": "<string>",
  "title": "<string>",
  "chunks": [
    {
      "id": 0,
      "type": "<type>",
      "text": "<spoken English>",
      "scene_hint": "<slug or null>",
      "pause_after_ms": <int>,
      "animation": {
        "title": "<string>",
        "description": "<string>",
        "visual_intent": "<string>"
      }
    }
  ]
}
"""


async def markdown_to_lecture_ir(
    client: AsyncClient,
    model: str,
    markdown: str,
    *,
    lecture_id: str,
    title: str,
    max_input_chars: int = 8000,
    think: bool | None = False,
) -> LectureIR:
    """Ask the LLM to convert lecture markdown into a unified LectureIR."""
    md = markdown[:max_input_chars]
    user = (
        f"Lecture ID: {lecture_id}\n"
        f"Title: {title}\n\n"
        f"--- MARKDOWN ---\n{md}\n--- END ---\n\n"
        "Convert this to the production IR JSON now."
    )
    _extra = {} if think is None else {"think": think}
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
    data = _extract_json(raw)
    data["lecture_id"] = lecture_id
    data["title"] = title
    return LectureIR.model_validate(data)


async def synthesize_from_ir(
    tts: Any,
    ir: LectureIR,
    *,
    voice: str | None,
    speed: float,
    sample_rate: int,
) -> tuple[bytes, LectureIR]:
    """Synthesize each chunk, insert silence gaps, populate timestamps.

    Returns ``(merged_wav_bytes, ir_with_timing)``.
    """
    pcm_chunks: list[bytes] = []
    sig: tuple[int, int, int] | None = None
    cursor_ms = 0

    for chunk in ir.chunks:
        text = chunk.text.strip()
        if not text:
            chunk.start_ms = cursor_ms
            chunk.end_ms = cursor_ms
            cursor_ms += chunk.pause_after_ms
            continue

        req = TTSRequest(text=text, voice=voice, speed=speed, sample_rate=sample_rate)
        audio = await tts.synthesize(req)

        with wave.open(io.BytesIO(audio.audio_bytes), "rb") as w:
            p = w.getparams()
            if sig is None:
                sig = (p.nchannels, p.sampwidth, p.framerate)
            dur_ms = int(w.getnframes() / p.framerate * 1000)
            pcm = w.readframes(w.getnframes())

        chunk.start_ms = cursor_ms
        chunk.end_ms = cursor_ms + dur_ms
        cursor_ms = chunk.end_ms + chunk.pause_after_ms

        pcm_chunks.append(pcm)
        if chunk.pause_after_ms > 0 and sig:
            nc, sw, fr = sig
            silence_frames = int(fr * chunk.pause_after_ms / 1000)
            pcm_chunks.append(b"\x00" * silence_frames * nc * sw)

    if not pcm_chunks or sig is None:
        raise ValueError("No audio synthesized from IR chunks.")

    nc, sw, fr = sig
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out_w:
        out_w.setnchannels(nc)
        out_w.setsampwidth(sw)
        out_w.setframerate(fr)
        out_w.writeframes(b"".join(pcm_chunks))

    return buf.getvalue(), ir


def _fix_backslashes(text: str) -> str:
    return _BAD_BACKSLASH.sub(r"\\\\", text)


def _extract_json(text: str) -> dict:
    for candidate in _json_candidates(text):
        fixed = _fix_backslashes(candidate)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Cannot extract JSON from model response: {text[:300]!r}")


def _json_candidates(text: str) -> list[str]:
    candidates: list[str] = [text]
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        candidates.append(m.group(1).strip())
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            if depth == 0:
                candidates.append(text[start : i + 1])
                break
    return candidates
