"""Orchestrate a multi-lecture course from a user topic (JSON plan + autolecture)."""

from educlaw.autocourse.orchestrator import (
    CoursePlanningFailed,
    plan_course,
    run_autocourse,
)
from educlaw.autocourse.schema import AutocourseEvent, CoursePlan

__all__ = [
    "AutocourseEvent",
    "CoursePlan",
    "CoursePlanningFailed",
    "plan_course",
    "run_autocourse",
]
