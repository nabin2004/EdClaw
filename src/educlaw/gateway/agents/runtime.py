from __future__ import annotations

from typing import TYPE_CHECKING

from educlaw.gateway.agents.context import build_prompt

if TYPE_CHECKING:
    from educlaw.gateway.agents.session import AgentSession
    from educlaw.gateway.agents.streaming import Streamer
    from educlaw.gateway.agents.tools.tools import ToolRegistry
    from educlaw.gateway.events.bus import EventBus


class AgentRuntime:
    def __init__(self, tools: ToolRegistry, bus: EventBus) -> None:
        self._tools = tools
        self._bus = bus

    async def run(self, session: AgentSession, msg: str, stream: Streamer) -> None:
        session.add_user_message(msg)
        _ = build_prompt(session)

        reply = "Stub response (no LLM wired yet). Your message is in the session transcript."
        for word in reply.split():
            await stream.token(word + " ")
        session.add_assistant_message(reply)
