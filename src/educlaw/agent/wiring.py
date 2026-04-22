"""Register tools and callbacks for ``LlmAgent``."""

from __future__ import annotations

from typing import Any

from educlaw.agent.callbacks import dagestan_ingest, ir_assemble, shield_in, shield_out
from educlaw.agent.deps import AgentDeps
from educlaw.agent.tools import dagestan_tools, ir_tools, manim_tool, record_answer, shell_tool


def build_tools(deps: AgentDeps) -> list[Any]:
    return [
        *ir_tools.build(deps),
        *dagestan_tools.build(deps),
        shell_tool.build(deps),
        manim_tool.build(deps),
        record_answer.build(),
    ]


def build_before_model_callbacks(deps: AgentDeps) -> list[Any]:
    return [shield_in.make(deps), ir_assemble.make(deps)]


def build_after_model_callbacks(deps: AgentDeps) -> list[Any]:
    return [shield_out.make(deps)]


def build_after_agent_callbacks(deps: AgentDeps) -> list[Any]:
    return [dagestan_ingest.make(deps)]
