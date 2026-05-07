"""
Future improvements:
1. real streaming LLM (OpenAI / local model)
2. proper tool schema (JSON tool calls)
3. cancellation support (stop generation)
4. multi-session scaling
5. queue lanes per session (like OpenClaw)
"""


import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import FileResponse

from educlaw.config.settings import load_settings
from educlaw.gateway.agents.execution.factory import build_execution_engine
from educlaw.gateway.agents.orchestrator import Orchestrator
from educlaw.gateway.agents.runtime import AgentRuntime
from educlaw.gateway.agents.tools import create_default_tools
from educlaw.gateway.api.websocket.endpoint import WebSocketEndpoint
from educlaw.gateway.events.bus import EventBus
from educlaw.gateway.storage.session_store import SessionStore


def _ensure_automanim_gateway_logging() -> None:
    log = logging.getLogger("educlaw.automanim")
    if log.handlers:
        return
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    log.addHandler(handler)
    log.propagate = False


_ensure_automanim_gateway_logging()

_settings = load_settings()
app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _safe_path_under_base(base: Path, relative: str) -> Path | None:
    root = base.expanduser().resolve()
    rel = relative.lstrip("/")
    if not rel or ".." in Path(rel).parts:
        return None
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/artifacts/manim/{file_path:path}")
async def manim_artifact(file_path: str) -> FileResponse:
    safe = _safe_path_under_base(Path(_settings.automanim_output_dir), file_path)
    if safe is None:
        raise HTTPException(status_code=404, detail="Not found")
    media = (
        "video/mp4"
        if safe.suffix.lower() == ".mp4"
        else "application/octet-stream"
    )
    return FileResponse(safe, media_type=media)


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
ws_handler = WebSocketEndpoint(store, runtime, orchestrator, _settings)


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws_handler.handler(ws)
