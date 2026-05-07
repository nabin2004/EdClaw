import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from educlaw.config.settings import Settings
from educlaw.gateway.agents.runtime import AgentRuntime
from educlaw.gateway.agents.session import AgentSession
from educlaw.gateway.agents.streaming import Streamer
from educlaw.gateway.agents.orchestrator import Orchestrator


class WebSocketEndpoint:
    def __init__(
        self,
        store: Any,
        runtime: AgentRuntime,
        orchestrator: Orchestrator,
        settings: Settings,
    ) -> None:
        self.store = store
        self.runtime = runtime
        self.orchestrator = orchestrator
        self._settings = settings

    def _parse_json_envelope(self, text: str) -> dict[str, Any] | None:
        s = text.strip()
        if not s.startswith("{"):
            return None
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            return None
        return obj if isinstance(obj, dict) else None

    async def handler(self, ws: WebSocket) -> None:
        await ws.accept()

        session_id = str(id(ws))
        session = AgentSession(self.store, session_id)
        stream = Streamer(ws)

        try:
            while True:
                msg = await ws.receive_text()

                await self.orchestrator.acquire(session_id)

                try:
                    envelope = self._parse_json_envelope(msg)
                    if envelope and envelope.get("type") == "automanim":
                        from educlaw.gateway.api.websocket.automanim_handler import (
                            handle_automanim_ws,
                        )

                        await handle_automanim_ws(session, stream, self._settings, envelope)
                    else:
                        await self.runtime.run(session, msg, stream)
                finally:
                    self.orchestrator.release(session_id)

        except WebSocketDisconnect:
            pass
