"""
Future improvements:
1. real streaming LLM (OpenAI / local model)
2. proper tool schema (JSON tool calls)
3. cancellation support (stop generation)
4. multi-session scaling
5. queue lanes per session (like OpenClaw)
"""


from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse

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

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        media_type="text/html; charset=utf-8",
    )

store = SessionStore()
tools = create_default_tools()
bus = EventBus()
orchestrator = Orchestrator()

runtime = AgentRuntime(tools, bus, build_execution_engine(_settings))
ws_handler = WebSocketEndpoint(store, runtime, orchestrator)


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws_handler.handler(ws)
