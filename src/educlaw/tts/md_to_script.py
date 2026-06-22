"""Convert lecture Markdown to a structured AudioScript via LLM, then synthesize."""

from __future__ import annotations

import io
import json
import re
import wave
from typing import Any

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
# Matches backslashes NOT followed by valid JSON escape characters
_BAD_BACKSLASH = re.compile(r'\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})')

from ollama import AsyncClient

from educlaw.tts.contract import TTSRequest
from educlaw.tts.script import AudioScript, AudioSegment

_SYSTEM = """\
You are an expert educational audio scriptwriter.
Convert a lecture written in Markdown into a structured audio narration script as JSON.

RULES:
- Write ONLY in natural spoken English. No LaTeX, no Markdown syntax, no bullet dashes.
- Convert math notation to words: write "x squared plus y squared" not "x^2 + y^2".
- Each segment should be 1-4 sentences and feel natural when read aloud by a narrator.
- Segment types to use:
    intro            – opening hook and lecture title (exactly 1 segment at the start)
    section_header   – spoken transition into a new section ("Now let's explore...")
    narration        – main explanation content
    example          – worked examples or walkthroughs
    summary          – brief recap section at the end
    check_understanding – quiz/review questions read aloud
    transition       – short bridge between topics (1 sentence)
- scene_hint: snake_case slug for the Manim scene this audio corresponds to.
  Use null for intro, transition, summary, check_understanding.
  For content segments, derive it from the section topic (e.g. "cost_functions", "gradient_step").
- pause_after_ms values:
    intro → 700
    section_header → 600
    summary → 500
    check_understanding → 500
    narration / example → 300
    transition → 200

Return ONLY valid JSON. No markdown code fences, no explanation text before or after.

SCHEMA:
{
  "lecture_id": "<string>",
  "title": "<string>",
  "segments": [
    {
      "id": 0,
      "type": "<SegmentType>",
      "text": "<spoken English — no markdown/LaTeX>",
      "scene_hint": "<slug or null>",
      "pause_after_ms": <integer>
    }
  ]
}
"""


async def markdown_to_script(
    client: AsyncClient,
    model: str,
    markdown: str,
    *,
    lecture_id: str,
    title: str,
    max_input_chars: int = 8000,
    think: bool | None = False,
) -> AudioScript:
    """Ask the LLM to convert a lecture markdown into a structured AudioScript."""
    md = markdown[:max_input_chars]
    user = (
        f"Lecture ID: {lecture_id}\n"
        f"Title: {title}\n\n"
        f"--- MARKDOWN ---\n{md}\n--- END ---\n\n"
        "Convert this to the audio script JSON now."
    )
    _extra = {} if think is None else {"think": think}
    out = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0.2, "num_predict": 4096},
        **_extra,
    )
    msg = out.get("message") or {}
    raw = _THINK_RE.sub("", (msg.get("content") or "").strip()).strip()
    data = _extract_json(raw)
    data["lecture_id"] = lecture_id
    data["title"] = title
    return AudioScript.model_validate(data)


async def synthesize_from_script(
    tts: Any,
    script: AudioScript,
    *,
    voice: str | None,
    speed: float,
    sample_rate: int,
) -> tuple[bytes, AudioScript]:
    """Synthesize each segment, insert silence gaps, track timestamps.

    Returns ``(merged_wav_bytes, script_with_timing)``.
    """
    pcm_chunks: list[bytes] = []
    sig: tuple[int, int, int] | None = None  # (nchannels, sampwidth, framerate)
    cursor_ms = 0

    for seg in script.segments:
        text = seg.text.strip()
        if not text:
            seg.start_ms = cursor_ms
            seg.end_ms = cursor_ms
            cursor_ms += seg.pause_after_ms
            continue

        req = TTSRequest(text=text, voice=voice, speed=speed, sample_rate=sample_rate)
        audio = await tts.synthesize(req)

        with wave.open(io.BytesIO(audio.audio_bytes), "rb") as w:
            p = w.getparams()
            if sig is None:
                sig = (p.nchannels, p.sampwidth, p.framerate)
            dur_ms = int(w.getnframes() / p.framerate * 1000)
            pcm = w.readframes(w.getnframes())

        seg.start_ms = cursor_ms
        seg.end_ms = cursor_ms + dur_ms
        cursor_ms = seg.end_ms + seg.pause_after_ms

        pcm_chunks.append(pcm)
        if seg.pause_after_ms > 0 and sig:
            nc, sw, fr = sig
            silence_frames = int(fr * seg.pause_after_ms / 1000)
            pcm_chunks.append(b"\x00" * silence_frames * nc * sw)

    if not pcm_chunks or sig is None:
        raise ValueError("No audio was synthesized from script segments.")

    nc, sw, fr = sig
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out_w:
        out_w.setnchannels(nc)
        out_w.setsampwidth(sw)
        out_w.setframerate(fr)
        out_w.writeframes(b"".join(pcm_chunks))

    return buf.getvalue(), script


def _fix_backslashes(text: str) -> str:
    """Escape backslashes that aren't valid JSON escapes (e.g. LaTeX in model output)."""
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
    """Yield JSON candidate strings from a model response in order of preference."""
    candidates: list[str] = []
    # Raw text first
    candidates.append(text)
    # Inside ```json ... ``` fences
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        candidates.append(m.group(1).strip())
    # First { ... } block
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
