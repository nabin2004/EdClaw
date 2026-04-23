"""ADK composite agents (used for extension / tests)."""

from __future__ import annotations

from google.adk.agents import SequentialAgent

from educlaw.automanim.codegen import build_codegen_agent
from educlaw.automanim.planner import build_planner_agent
from educlaw.config.settings import Settings


def build_planner_codegen_sequential(settings: Settings) -> SequentialAgent:
    """Planner then codegen in one ADK session (single user turn).

    The orchestrator normally calls planner and codegen in separate invocations
    so each scene can be revised independently; this composite is available for
    experiments and unit tests.
    """
    return SequentialAgent(
        name="automanim_planner_codegen_seq",
        sub_agents=[build_planner_agent(settings), build_codegen_agent(settings)],
    )
