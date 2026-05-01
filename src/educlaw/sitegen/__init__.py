"""Site generation from Copier templates and course registry management."""

from educlaw.sitegen.catalog import render_catalog
from educlaw.sitegen.converter import convert_lectures
from educlaw.sitegen.generator import generate_site
from educlaw.sitegen.registry import list_courses, register_course, remove_course

__all__ = [
    "convert_lectures",
    "generate_site",
    "list_courses",
    "register_course",
    "remove_course",
    "render_catalog",
]
