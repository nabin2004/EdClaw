"""Render the course catalog landing page from the registry."""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from educlaw.sitegen.registry import DEFAULT_REGISTRY_PATH, list_courses

LOG = logging.getLogger(__name__)

_CATALOG_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates" / "course_catalog"


def render_catalog(
    *,
    output_dir: Path | None = None,
    registry_path: Path | None = None,
    template_dir: Path | None = None,
) -> Path:
    """Render ``index.html`` from the catalog template and course registry.

    Returns the path of the written file.
    """
    tpl_dir = template_dir or _CATALOG_TEMPLATE_DIR
    out_dir = output_dir or DEFAULT_REGISTRY_PATH.parent
    reg = registry_path or DEFAULT_REGISTRY_PATH

    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=True,
    )
    template = env.get_template("index.html.jinja")

    courses = list_courses(registry_path=reg)
    html = template.render(courses=courses)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    LOG.info("Catalog rendered -> %s (%d courses)", out_path, len(courses))
    return out_path
