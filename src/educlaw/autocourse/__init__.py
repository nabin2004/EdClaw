"""Orchestrate a multi-lecture course from a user topic (JSON plan + autolecture)."""

from educlaw.autocourse.orchestrator import run_autocourse
from educlaw.autocourse.schema import AutocourseEvent, CoursePlan

__all__ = ["AutocourseEvent", "CoursePlan", "run_autocourse"]
