"""
Future improvements:
1. real streaming LLM (OpenAI / local model)
2. proper tool schema (JSON tool calls)
3. cancellation support (stop generation)
4. multi-session scaling
5. queue lanes per session (like OpenClaw)
"""


from fastapi import FastAPI, WebSocket

from educlaw.config.settings import load_settings
from educlaw.gateway.agents.execution.factory import build_execution_engine
from educlaw.gateway.agents.orchestrator import Orchestrator
from educlaw.gateway.agents.runtime import AgentRuntime
from educlaw.gateway.agents.tools import create_default_tools
from educlaw.gateway.api.websocket.endpoint import WebSocketEndpoint
from educlaw.gateway.events.bus import EventBus
from educlaw.gateway.storage.session_store import SessionStore

_settings = load_settings()
app = FastAPI()

store = SessionStore()
tools = create_default_tools()
bus = EventBus()
orchestrator = Orchestrator()

runtime = AgentRuntime(tools, bus, build_execution_engine(_settings))
ws_handler = WebSocketEndpoint(store, runtime, orchestrator)


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws_handler.handler(ws)
