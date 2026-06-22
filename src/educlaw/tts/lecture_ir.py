"""Unified production IR: one chunk = TTS text + optional animation spec.

This is the single source of truth that drives both audio synthesis and
Manim video generation for a lecture.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from educlaw.tts.script import SegmentType


class AnimationSpec(BaseModel):
    """What to show on screen while this chunk is spoken."""

    title: str
    description: str = ""
    visual_intent: str = ""


class IRChunk(BaseModel):
    """One narration unit: spoken text + optional visual animation."""

    id: int
    type: SegmentType
    text: str
    scene_hint: str | None = None
    pause_after_ms: int = Field(default=300, ge=0, le=3000)
    animation: AnimationSpec | None = None
    # populated after TTS synthesis
    start_ms: int | None = None
    end_ms: int | None = None


class LectureIR(BaseModel):
    """Full production IR for one lecture."""

    lecture_id: str
    title: str
    chunks: list[IRChunk]

    def timed_chunks(self) -> list[IRChunk]:
        return [c for c in self.chunks if c.start_ms is not None and c.end_ms is not None]

    def animation_chunks(self) -> list[IRChunk]:
        return [c for c in self.chunks if c.animation is not None]

    def to_srt(self) -> str:
        lines: list[str] = []
        idx = 1
        for chunk in self.chunks:
            if chunk.start_ms is None or chunk.end_ms is None:
                continue
            if not chunk.text.strip():
                continue
            lines.append(str(idx))
            lines.append(f"{_ms_to_srt(chunk.start_ms)} --> {_ms_to_srt(chunk.end_ms)}")
            lines.append(chunk.text.strip())
            lines.append("")
            idx += 1
        return "\n".join(lines)

    def to_vtt(self) -> str:
        lines = ["WEBVTT", ""]
        for chunk in self.chunks:
            if chunk.start_ms is None or chunk.end_ms is None:
                continue
            if not chunk.text.strip():
                continue
            lines.append(f"{_ms_to_vtt(chunk.start_ms)} --> {_ms_to_vtt(chunk.end_ms)}")
            lines.append(chunk.text.strip())
            lines.append("")
        return "\n".join(lines)

    def scene_map(self) -> dict[str, list[tuple[int, int]]]:
        """Return {scene_hint: [(start_ms, end_ms), ...]} for A/V sync."""
        result: dict[str, list[tuple[int, int]]] = {}
        for chunk in self.timed_chunks():
            if chunk.scene_hint and chunk.start_ms is not None and chunk.end_ms is not None:
                result.setdefault(chunk.scene_hint, []).append((chunk.start_ms, chunk.end_ms))
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
