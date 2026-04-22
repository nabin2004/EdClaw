"""Generate a single end-to-end lecture from an outline (Ollama chat, no ADK)."""

from educlaw.autolecture.generator import generate_lecture
from educlaw.autolecture.schema import LectureOutline, LectureResult

__all__ = ["LectureOutline", "LectureResult", "generate_lecture"]
