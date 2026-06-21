"""Collect IR series scene.py files and convert them to episode-like training dicts.

Each entry matches the shape of metadata.json used by render_episode(), so the
existing Gemma4 Jinja template works without modification.

Directory layout expected:
  <ir_root>/series/<series-slug>/videos/<lecture-slug>/<scene-slug>/scene.py
  <ir_root>/series/<series-slug>/lecture-*.md          (optional, for context)
  <ir_root>/series/<series-slug>/course-plan.json      (optional, for title)
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def _slug_to_title(slug: str) -> str:
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)  # strip date prefix
    slug = re.sub(r"^teach-me-(?:about-)?", "", slug)  # strip teach-me-about-
    slug = re.sub(r"-\d+$", "", slug)                  # strip trailing -N
    slug = re.sub(r"[-_]+", " ", slug)
    return slug.title()


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _series_title(series_dir: Path) -> str:
    plan = _read_json(series_dir / "course-plan.json")
    if plan.get("title"):
        return str(plan["title"])
    return _slug_to_title(series_dir.name)


def _lecture_excerpt(series_dir: Path, max_chars: int = 800) -> str:
    """Return a short excerpt from the first lecture .md in the series."""
    for md in sorted(series_dir.glob("lecture-*.md")):
        text = _read_text(md)
        # Strip YAML frontmatter
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                text = text[end + 4:].lstrip()
        text = text.strip()
        if text:
            return text[:max_chars]
    return ""


def extract_scene_sections(code: str) -> list[str]:
    """Return human-readable section titles from '# --- Title ---' comment headers."""
    sections: list[str] = []
    for line in code.splitlines():
        stripped = line.strip()
        m = re.match(r"^#\s*-{2,}\s*(.+?)\s*-{0,}\s*$", stripped)
        if m:
            title = m.group(1).strip().strip("-").strip()
            if title:
                sections.append(title)
    return sections


def _count_play_calls(code: str) -> int:
    return len(re.findall(r"\bself\.play\s*\(", code))


def _build_narration_segments(sections: list[str], play_count: int) -> list[dict]:
    """Create SRT-compatible narration segment stubs from section titles.

    Timing is estimated: ~2 s per self.play() call, divided evenly across sections.
    """
    if not sections:
        return []

    secs_per_segment = max(2.0, (play_count * 2.0) / len(sections))
    segments: list[dict] = []
    cursor = 0.0
    for i, title in enumerate(sections):
        end = cursor + secs_per_segment
        segments.append(
            {
                "id": f"section_{i + 1}",
                "text": title,
                "voice": "Jasper",
                "speed": 1,
                "durationHint": round(secs_per_segment, 3),
                "startHint": round(cursor, 3),
            }
        )
        cursor = end
    return segments


def _build_prompt(series_title: str, lecture_slug: str, scene_slug: str, lecture_excerpt: str) -> str:
    lecture_title = _slug_to_title(lecture_slug)
    scene_title = _slug_to_title(re.sub(r"^\d+-", "", scene_slug))
    parts = [
        f"Create a Manim animation scene titled '{scene_title}' "
        f"for the lecture '{lecture_title}' from the course '{series_title}'."
    ]
    if lecture_excerpt:
        parts.append(f"\n\nContext from the lecture:\n{lecture_excerpt}")
    return "".join(parts)


def collect_ir_scenes(ir_root: Path) -> list[dict]:
    """Walk content/ir/series and return episode-like dicts for every scene.py.

    Each dict matches the metadata.json schema consumed by render_episode().
    """
    series_root = ir_root / "series"
    if not series_root.is_dir():
        series_root = ir_root  # allow passing series/ directly

    episodes: list[dict] = []

    for series_dir in sorted(series_root.iterdir()):
        if not series_dir.is_dir():
            continue

        stitle = _series_title(series_dir)
        excerpt = _lecture_excerpt(series_dir)
        videos_dir = series_dir / "videos"
        if not videos_dir.is_dir():
            continue

        for lecture_dir in sorted(videos_dir.iterdir()):
            if not lecture_dir.is_dir():
                continue

            for scene_dir in sorted(lecture_dir.iterdir()):
                if not scene_dir.is_dir():
                    continue

                scene_py = scene_dir / "scene.py"
                if not scene_py.is_file():
                    continue

                code = _read_text(scene_py)
                if not code.strip():
                    continue

                sections = extract_scene_sections(code)
                play_count = _count_play_calls(code)
                narration = _build_narration_segments(sections, play_count)

                episode_id = (
                    f"{series_dir.name}__{lecture_dir.name}__{scene_dir.name}"
                )
                prompt = _build_prompt(
                    stitle,
                    lecture_dir.name,
                    scene_dir.name,
                    excerpt,
                )

                episodes.append(
                    {
                        "episode_id": episode_id,
                        "prompt": prompt,
                        "model": "ir-series-reference",
                        "generated_code": code,
                        "narration_segments": narration,
                        "tool_logs": [],
                        "status": "success",
                        "source": "ir_series",
                        "series": stitle,
                        "lecture": lecture_dir.name,
                        "scene": scene_dir.name,
                    }
                )

    return episodes


def build_srt(narration_segments: list[dict]) -> str:
    """Render narration_segments to SRT subtitle text."""

    def _fmt_time(seconds: float) -> str:
        ms = int(round((seconds % 1) * 1000))
        s = int(seconds) % 60
        m = int(seconds) // 60 % 60
        h = int(seconds) // 3600
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines: list[str] = []
    cursor = 0.0
    for i, seg in enumerate(narration_segments, 1):
        duration = float(seg.get("durationHint", 3.0))
        start = float(seg.get("startHint", cursor))
        end = start + duration
        lines.append(str(i))
        lines.append(f"{_fmt_time(start)} --> {_fmt_time(end)}")
        lines.append(seg["text"])
        lines.append("")
        cursor = end

    return "\n".join(lines)
