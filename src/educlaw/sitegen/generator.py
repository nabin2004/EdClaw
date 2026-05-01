"""Generate a Jekyll course site from an autocourse series directory."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from copier import run_copy

from educlaw.sitegen.catalog import render_catalog
from educlaw.sitegen.converter import convert_lectures
from educlaw.sitegen.registry import DEFAULT_REGISTRY_PATH, register_course

LOG = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates" / "course_site"


def _slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "course"


def generate_site(
    series_dir: Path,
    *,
    output_dir: Path | None = None,
    template_dir: Path | None = None,
    registry_path: Path | None = None,
) -> Path:
    """Generate a full Jekyll course site from an autocourse series directory.

    Reads ``course-plan.json`` from *series_dir*, runs Copier to scaffold the
    site, converts IR lecture markdown to Jekyll format, and registers the
    course in the catalog.

    Returns the path of the generated site.
    """
    series_path = series_dir.expanduser().resolve()
    plan_path = series_path / "course-plan.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"No course-plan.json in {series_path}")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    title = plan.get("title", "Untitled Course")
    audience = plan.get("audience", "General learners")
    lecture_count = plan.get("lecture_count", 0)
    slug = _slug(title)

    sites_root = output_dir or DEFAULT_REGISTRY_PATH.parent
    sites_root = sites_root.expanduser().resolve()
    dest = sites_root / slug
    dest.mkdir(parents=True, exist_ok=True)

    tpl = (template_dir or _TEMPLATE_DIR).resolve()
    reg = registry_path or DEFAULT_REGISTRY_PATH

    answers = {
        "course_name": title,
        "course_slug": slug,
        "course_description": audience,
        "course_semester": "Spring 2026",
        "audience": audience,
        "schoolname": "",
        "schoolurl": "",
        "instructor_name": "Instructor",
        "theme_color": "#A51C30",
    }

    LOG.info("Scaffolding site for %r -> %s", title, dest)
    run_copy(
        str(tpl),
        str(dest),
        data=answers,
        defaults=True,
        overwrite=True,
        unsafe=True,
    )

    lectures_dir = dest / "_lectures"
    converted = convert_lectures(series_path, lectures_dir)
    LOG.info("Converted %d lectures into %s", len(converted), lectures_dir)

    register_course(
        slug,
        title,
        audience=audience,
        semester=answers["course_semester"],
        lecture_count=lecture_count or len(converted),
        site_dir=str(dest),
        series_dir=str(series_path),
        registry_path=reg,
    )

    render_catalog(output_dir=sites_root, registry_path=reg)

    LOG.info("Site ready at %s", dest)
    return dest
