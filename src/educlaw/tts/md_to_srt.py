"""Convert lecture Markdown directly to subtitle blocks (SRT/VTT) via LLM + TTS.

Industry standards enforced:
- 15-20 characters per second (CPS) reading speed
- Max 2 lines per subtitle block
- Max 42 characters per line
- 3-7 seconds display duration per block
"""

from __future__ import annotations

import io
import json
import re
import wave
from dataclasses import dataclass
from typing import Any

from ollama import AsyncClient

from educlaw.tts.contract import TTSRequest

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_BAD_BACKSLASH = re.compile(r'\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})')

_MAX_LINE_CHARS = 42
_TARGET_CPS = 15.0  # characters per second (conservative end of 15-20 range)
_MAX_BLOCK_SEC = 7.0
_MIN_BLOCK_SEC = 2.5

_SUBTITLE_SYSTEM = f"""\
You are an expert subtitle writer for educational video content.

Convert the provided lecture text into subtitle segments ready for on-screen display.

STRICT RULES (broadcast / streaming standard):
- Maximum {_MAX_LINE_CHARS} characters per line (count every character including spaces)
- Maximum 2 lines per subtitle block — use a newline character (\\n) between lines
- Target reading time 3-7 seconds per block at ~15 characters per second
- Break ONLY at natural sentence boundaries or meaningful clause breaks
- Plain spoken English only: no LaTeX, no Markdown syntax, no bullet dashes, no code
- Convert all math to words: "x squared plus y squared" not "x^2+y^2", "pi" not "π"
- Convert symbols: "greater than or equal to" not "≥", "therefore" not "∴"
- Do NOT include headings, formatting symbols, or source citations
- Each block should feel like a natural unit a speaker would say in one breath

Return ONLY a JSON array of strings. Each string is one subtitle block.
Use \\n inside a string only to split a block into 2 lines.
Do NOT include timestamps.

EXAMPLE (notice the 2-line blocks use \\n):
[
  "Welcome to this lecture on linear algebra.",
  "We will explore vectors, matrices,\\nand the operations on them.",
  "A vector has both a magnitude\\nand a direction in space.",
  "Think of it as an arrow pointing\\nfrom one point to another."
]
"""


@dataclass
class SubtitleBlock:
    index: int        # 1-based
    text: str         # Display text — may contain \\n for 2-line layout
    tts_text: str     # Same text with \\n replaced by space (for TTS synthesis)
    start_ms: int = 0
    end_ms: int = 0

    def duration_sec(self) -> float:
        return (self.end_ms - self.start_ms) / 1000.0


# ---------------------------------------------------------------------------
# SRT / VTT formatting
# ---------------------------------------------------------------------------

def _ms_to_srt(ms: int) -> str:
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ms_to_vtt(ms: int) -> str:
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def blocks_to_srt(blocks: list[SubtitleBlock]) -> str:
    parts: list[str] = []
    for b in blocks:
        parts.append(
            f"{b.index}\n"
            f"{_ms_to_srt(b.start_ms)} --> {_ms_to_srt(b.end_ms)}\n"
            f"{b.text}\n"
        )
    return "\n".join(parts)


def blocks_to_vtt(blocks: list[SubtitleBlock]) -> str:
    parts: list[str] = ["WEBVTT", ""]
    for b in blocks:
        parts.append(
            f"{b.index}\n"
            f"{_ms_to_vtt(b.start_ms)} --> {_ms_to_vtt(b.end_ms)}\n"
            f"{b.text}\n"
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Markdown → plain text
# ---------------------------------------------------------------------------

def clean_markdown(markdown: str, max_chars: int = 12_000) -> str:
    t = re.sub(r"```[\s\S]*?```", " ", markdown)
    t = re.sub(r"\$\$[\s\S]*?\$\$", " math expression ", t)
    t = re.sub(r"\$[^\$\n]{1,300}?\$", " math expression ", t)
    t = re.sub(r"\\\[[\s\S]*?\\\]", " math expression ", t)
    t = re.sub(r"\\\([\s\S]*?\\\)", " math expression ", t)
    t = re.sub(r"#{1,6}\s*", "", t)
    t = re.sub(r"[*_`]+", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_chars]


# ---------------------------------------------------------------------------
# LLM segmentation
# ---------------------------------------------------------------------------

async def segment_markdown(
    client: AsyncClient,
    model: str,
    markdown: str,
    *,
    max_input_chars: int = 8000,
    think: bool | None = False,
) -> list[str]:
    """Ask the LLM to break lecture markdown into subtitle text segments.

    Returns a list of raw text strings (may contain \\n for 2-line blocks).
    """
    cleaned = clean_markdown(markdown, max_input_chars)
    user = (
        "Convert this lecture text into subtitle segments.\n\n"
        f"--- LECTURE TEXT ---\n{cleaned}\n--- END ---\n\n"
        "Return only the JSON array of subtitle strings."
    )
    _extra = {} if think is None else {"think": think}
    out = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _SUBTITLE_SYSTEM},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0.15, "num_predict": 8000},
        **_extra,
    )
    msg = out.get("message") or {}
    raw = _THINK_RE.sub("", (msg.get("content") or "").strip()).strip()
    segments = _extract_json_array(raw)
    return [s for s in segments if s.strip()]


def _extract_json_array(text: str) -> list[str]:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    start = text.find("[")
    if start != -1:
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
            if depth == 0:
                text = text[start : i + 1]
                break
    fixed = _BAD_BACKSLASH.sub(r"\\\\", text)
    try:
        data = json.loads(fixed)
        if isinstance(data, list):
            return [str(s) for s in data if s]
    except json.JSONDecodeError:
        pass
    # Last-resort: treat non-bracket lines as segments
    return [
        ln.strip().strip('",')
        for ln in text.splitlines()
        if ln.strip().strip('",') and not ln.strip().startswith(("[", "]"))
    ]


# ---------------------------------------------------------------------------
# Timing estimation (used when TTS is disabled)
# ---------------------------------------------------------------------------

def estimate_timing(segments: list[str], cps: float = _TARGET_CPS, gap_ms: int = 200) -> list[SubtitleBlock]:
    """Assign approximate timings based on reading speed, without TTS."""
    blocks: list[SubtitleBlock] = []
    cursor_ms = 0
    for idx, seg in enumerate(segments, start=1):
        tts_text = seg.replace("\n", " ").strip()
        char_count = len(tts_text)
        dur_ms = max(int(_MIN_BLOCK_SEC * 1000), min(int(_MAX_BLOCK_SEC * 1000), int(char_count / cps * 1000)))
        blocks.append(SubtitleBlock(
            index=idx,
            text=seg,
            tts_text=tts_text,
            start_ms=cursor_ms,
            end_ms=cursor_ms + dur_ms,
        ))
        cursor_ms += dur_ms + gap_ms
    return blocks


# ---------------------------------------------------------------------------
# TTS synthesis per subtitle block
# ---------------------------------------------------------------------------

async def synthesize_blocks(
    tts: Any,
    segments: list[str],
    *,
    voice: str | None,
    speed: float,
    sample_rate: int,
    gap_ms: int = 200,
) -> tuple[list[SubtitleBlock], bytes]:
    """Synthesize TTS for each segment; return (blocks_with_timing, merged_wav).

    gap_ms: silence inserted between subtitle blocks.
    """
    blocks: list[SubtitleBlock] = []
    pcm_chunks: list[bytes] = []
    sig: tuple[int, int, int] | None = None
    cursor_ms = 0

    for idx, seg in enumerate(segments, start=1):
        tts_text = seg.replace("\n", " ").strip()
        if not tts_text:
            continue

        req = TTSRequest(text=tts_text, voice=voice, speed=speed, sample_rate=sample_rate)
        audio = await tts.synthesize(req)

        with wave.open(io.BytesIO(audio.audio_bytes), "rb") as w:
            p = w.getparams()
            if sig is None:
                sig = (p.nchannels, p.sampwidth, p.framerate)
            dur_ms = int(w.getnframes() / p.framerate * 1000)
            pcm = w.readframes(w.getnframes())

        blocks.append(SubtitleBlock(
            index=idx,
            text=seg,
            tts_text=tts_text,
            start_ms=cursor_ms,
            end_ms=cursor_ms + dur_ms,
        ))
        cursor_ms += dur_ms + gap_ms

        pcm_chunks.append(pcm)
        if gap_ms > 0 and sig:
            nc, sw, fr = sig
            silence_frames = int(fr * gap_ms / 1000)
            pcm_chunks.append(b"\x00" * silence_frames * nc * sw)

    if not pcm_chunks or sig is None:
        raise ValueError("No audio synthesized from subtitle segments.")

    nc, sw, fr = sig
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out_w:
        out_w.setnchannels(nc)
        out_w.setsampwidth(sw)
        out_w.setframerate(fr)
        out_w.writeframes(b"".join(pcm_chunks))

    return blocks, buf.getvalue()
