"""AutoManim SFT dataset rendering (Gemma-4 Jinja-style text)."""

from automanim_sft.build_dataset import build_automanim_jsonl, print_build_summary
from automanim_sft.template import (
    GEMMA4_AUTOMANIM_TEMPLATE,
    dataset_to_messages,
    render_episode,
)
from automanim_sft.tool_definitions import AUTOMANIM_TOOL_DEFINITIONS

__all__ = [
    "AUTOMANIM_TOOL_DEFINITIONS",
    "GEMMA4_AUTOMANIM_TEMPLATE",
    "build_automanim_jsonl",
    "dataset_to_messages",
    "print_build_summary",
    "render_episode",
]
