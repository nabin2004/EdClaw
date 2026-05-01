"""Convert autocourse IR lecture markdown into Jekyll ``_lectures/`` format."""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from pathlib import Path

import frontmatter

LOG = logging.getLogger(__name__)


def _make_slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:max_len] or "lecture"


def convert_lecture(
    src_path: Path,
    dest_dir: Path,
    lecture_num: int,
    *,
    series_date: date | None = None,
) -> Path:
    """Convert a single IR lecture markdown to Jekyll lecture format.

    Returns the path of the written file.
    """
    post = frontmatter.loads(src_path.read_text(encoding="utf-8"))
    meta = dict(post.metadata) if isinstance(post.metadata, dict) else {}

    title = str(meta.get("title", f"Lecture {lecture_num}"))
    objective = str(meta.get("objective", ""))
    tldr = objective if objective else title

    base_date = series_date or date.today()
    lecture_date = base_date + timedelta(days=(lecture_num - 1) * 7)

    jekyll_meta = {
        "type": "lecture",
        "date": lecture_date.isoformat(),
        "title": title,
        "tldr": tldr,
        "thumbnail": "/static_files/presentations/lec.jpg",
    }

    out_post = frontmatter.Post(str(post.content), **jekyll_meta)
    slug = _make_slug(title)
    out_name = f"{lecture_num:02d}_{slug}.md"
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / out_name
    out_path.write_text(frontmatter.dumps(out_post), encoding="utf-8")
    LOG.info("Converted lecture %d -> %s", lecture_num, out_path.name)
    return out_path


def convert_lectures(series_dir: Path, dest_dir: Path) -> list[Path]:
    """Convert all ``lecture-*.md`` files in *series_dir* to Jekyll format.

    Returns a list of paths written under *dest_dir*.
    """
    series_date = _extract_series_date(series_dir)
    md_files = sorted(series_dir.glob("lecture-*.md"))
    if not md_files:
        LOG.warning("No lecture-*.md files found in %s", series_dir)
        return []

    results: list[Path] = []
    for i, src in enumerate(md_files, start=1):
        out = convert_lecture(src, dest_dir, i, series_date=series_date)
        results.append(out)
    return results


def _extract_series_date(series_dir: Path) -> date | None:
    """Try to parse a YYYY-MM-DD prefix from the series directory name."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", series_dir.name)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return None
