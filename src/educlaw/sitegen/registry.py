"""Course registry backed by a ``courses.yml`` YAML file."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

LOG = logging.getLogger(__name__)

_yaml = YAML()
_yaml.default_flow_style = False

DEFAULT_REGISTRY_PATH = Path("sites") / "courses.yml"


def _load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = _yaml.load(path)
    if data is None:
        return []
    return list(data.get("courses", []))


def _save(path: Path, courses: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _yaml.dump({"courses": courses}, path)


def register_course(
    slug: str,
    title: str,
    *,
    audience: str = "",
    semester: str = "",
    lecture_count: int = 0,
    site_dir: str = "",
    series_dir: str = "",
    created: str | None = None,
    registry_path: Path | None = None,
) -> None:
    """Add or update a course entry in the registry."""
    reg = registry_path or DEFAULT_REGISTRY_PATH
    courses = _load(reg)

    entry: dict[str, Any] = {
        "slug": slug,
        "title": title,
        "audience": audience,
        "semester": semester,
        "lecture_count": lecture_count,
        "site_dir": site_dir,
        "series_dir": series_dir,
        "created": created or date.today().isoformat(),
    }

    for i, c in enumerate(courses):
        if c.get("slug") == slug:
            courses[i] = entry
            LOG.info("Updated existing course %r in registry", slug)
            break
    else:
        courses.append(entry)
        LOG.info("Registered new course %r", slug)

    _save(reg, courses)


def list_courses(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Return all registered courses."""
    return _load(registry_path or DEFAULT_REGISTRY_PATH)


def remove_course(slug: str, *, registry_path: Path | None = None) -> bool:
    """Remove a course by slug. Returns True if found and removed."""
    reg = registry_path or DEFAULT_REGISTRY_PATH
    courses = _load(reg)
    before = len(courses)
    courses = [c for c in courses if c.get("slug") != slug]
    if len(courses) < before:
        _save(reg, courses)
        LOG.info("Removed course %r from registry", slug)
        return True
    return False
