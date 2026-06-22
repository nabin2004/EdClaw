"""Structured audio script: JSON schema for TTS + subtitles + Manim sync."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SegmentType = Literal[
    "intro",
    "section_header",
    "narration",
    "example",
    "summary",
    "check_understanding",
    "transition",
]


class AudioSegment(BaseModel):
    id: int
    type: SegmentType
    text: str
    # slug matching the intended Manim scene (null = no visual change)
    scene_hint: str | None = None
    # silence to insert after this segment's audio
    pause_after_ms: int = Field(default=300, ge=0, le=3000)
    # populated after TTS synthesis
    start_ms: int | None = None
    end_ms: int | None = None


class AudioScript(BaseModel):
    lecture_id: str
    title: str
    segments: list[AudioSegment]

    def total_chars(self) -> int:
        return sum(len(s.text) for s in self.segments)

    def timed_segments(self) -> list[AudioSegment]:
        return [s for s in self.segments if s.start_ms is not None and s.end_ms is not None]

    def to_srt(self) -> str:
        """Render timed segments as SRT subtitle text."""
        lines: list[str] = []
        idx = 1
        for seg in self.segments:
            if seg.start_ms is None or seg.end_ms is None:
                continue
            if not seg.text.strip():
                continue
            lines.append(str(idx))
            lines.append(f"{_ms_to_srt(seg.start_ms)} --> {_ms_to_srt(seg.end_ms)}")
            lines.append(seg.text.strip())
            lines.append("")
            idx += 1
        return "\n".join(lines)

    def to_vtt(self) -> str:
        """Render timed segments as WebVTT subtitle text."""
        lines = ["WEBVTT", ""]
        for seg in self.segments:
            if seg.start_ms is None or seg.end_ms is None:
                continue
            if not seg.text.strip():
                continue
            lines.append(f"{_ms_to_vtt(seg.start_ms)} --> {_ms_to_vtt(seg.end_ms)}")
            lines.append(seg.text.strip())
            lines.append("")
        return "\n".join(lines)

    def scene_map(self) -> dict[str, list[tuple[int, int]]]:
        """Return {scene_hint: [(start_ms, end_ms), ...]} for Manim sync."""
        result: dict[str, list[tuple[int, int]]] = {}
        for seg in self.timed_segments():
            if seg.scene_hint and seg.start_ms is not None and seg.end_ms is not None:
                result.setdefault(seg.scene_hint, []).append((seg.start_ms, seg.end_ms))
        return result


def _ms_to_srt(ms: int) -> str:
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ms_to_vtt(ms: int) -> str:
    return _ms_to_srt(ms).replace(",", ".")
