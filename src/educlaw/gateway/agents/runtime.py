from __future__ import annotations

from typing import TYPE_CHECKING

from educlaw.gateway.agents.execution.base import ExecutionEngine

if TYPE_CHECKING:
    from educlaw.gateway.agents.session import AgentSession
    from educlaw.gateway.agents.streaming import Streamer
    from educlaw.gateway.agents.tools.tools import ToolRegistry
    from educlaw.gateway.events.bus import EventBus


class AgentRuntime:
    def __init__(
        self,
        tools: ToolRegistry,
        bus: EventBus,
        execution_engine: ExecutionEngine,
    ) -> None:
        self._tools = tools
        self._bus = bus
        self._engine = execution_engine

    async def run(self, session: AgentSession, msg: str, stream: Streamer) -> None:
        await self._bus.emit("gateway.turn.start", {"session_id": session.session_id})
        session.add_user_message(msg)
        await stream.event("assistant.status", {"phase": "start"})
        try:
            reply = await self._engine.run(session, msg, self._tools, stream)
        except Exception as e:
            await stream.event("assistant.status", {"phase": "error", "message": str(e)})
        else:
            session.add_assistant_message(reply)
        finally:
            await stream.event("assistant.status", {"phase": "end"})
            await self._bus.emit("gateway.turn.end", {"session_id": session.session_id})
