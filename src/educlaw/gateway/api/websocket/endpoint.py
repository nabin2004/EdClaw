from fastapi import WebSocket, WebSocketDisconnect

from educlaw.gateway.agents.session import AgentSession
from educlaw.gateway.agents.streaming import Streamer


class WebSocketEndpoint:
    def __init__(self, store, runtime, orchestrator):
        self.store = store
        self.runtime = runtime
        self.orchestrator = orchestrator

    async def handler(self, ws: WebSocket):
        await ws.accept()

        session_id = str(id(ws))
        session = AgentSession(self.store, session_id)
        stream = Streamer(ws)

        try:
            while True:
                msg = await ws.receive_text()

                await self.orchestrator.acquire(session_id)

                try:
                    await self.runtime.run(session, msg, stream)
                finally:
                    self.orchestrator.release(session_id)

        except WebSocketDisconnect:
            pass
