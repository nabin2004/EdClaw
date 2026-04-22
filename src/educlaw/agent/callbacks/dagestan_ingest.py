"""Persist session into Dagestan via ADK memory service."""

from __future__ import annotations

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from educlaw.agent.deps import AgentDeps


def make(_deps: AgentDeps):
    async def after_agent(callback_context: CallbackContext) -> types.Content | None:
        await callback_context.add_session_to_memory()
        return None

    return after_agent
