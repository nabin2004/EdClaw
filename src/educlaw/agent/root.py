"""Root ``LlmAgent`` for EduClaw."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from educlaw.agent.deps import AgentDeps
from educlaw.agent.model import build_model
from educlaw.agent.wiring import (
    build_after_agent_callbacks,
    build_after_model_callbacks,
    build_before_model_callbacks,
    build_tools,
)


def build_root_agent(deps: AgentDeps) -> LlmAgent:
    return LlmAgent(
        name="educlaw_root",
        model=build_model(deps.settings),
        instruction=(
            "You are EduClaw, a patient Socratic tutor for structured courses (IR). "
            "Prefer concise explanations and ask guiding questions. "
            "Use tools for IR lookup, learner beliefs, and sandboxed commands when needed."
        ),
        tools=build_tools(deps),
        before_model_callback=build_before_model_callbacks(deps),
        after_model_callback=build_after_model_callbacks(deps),
        after_agent_callback=build_after_agent_callbacks(deps),
    )
