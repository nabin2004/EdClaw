"""Pedagogy-focused ``LlmAgent`` (MVP: clone of root wiring)."""

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


def build_tutor_agent(deps: AgentDeps) -> LlmAgent:
    return LlmAgent(
        name="educlaw_tutor",
        model=build_model(deps.settings),
        instruction=(
            "You are EduClaw, a patient Socratic tutor. "
            "Use tools when you need IR content, learner memory, or safe shell checks."
        ),
        tools=build_tools(deps),
        before_model_callback=build_before_model_callbacks(deps),
        after_model_callback=build_after_model_callbacks(deps),
        after_agent_callback=build_after_agent_callbacks(deps),
    )
