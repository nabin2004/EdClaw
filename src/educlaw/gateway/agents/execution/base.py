"""Execution engine protocol: EduClaw owns sessions and lifecycle; engines run the agent loop."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from educlaw.gateway.agents.session import AgentSession
    from educlaw.gateway.agents.streaming import Streamer
    from educlaw.gateway.agents.tools.tools import ToolRegistry


class ExecutionEngine(Protocol):
    """Contract: ``AgentRuntime`` calls ``run`` after persisting the user turn."""

    async def run(
        self,
        session: AgentSession,
        input_text: str,
        tools: ToolRegistry,
        stream: Streamer,
    ) -> str:
        """Execute one user turn; return final assistant text for the transcript."""
        ...


class StubExecutionEngine:
    """Default engine when no LLM loop is configured (CI / local stub)."""

    async def run(
        self,
        session: AgentSession,
        input_text: str,
        tools: ToolRegistry,
        stream: Streamer,
    ) -> str:
        del session, input_text, tools
        reply = "Stub response (no LLM wired yet). Your message is in the session transcript."
        for word in reply.split():
            await stream.token(word + " ")
        return reply
