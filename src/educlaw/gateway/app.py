"""FastAPI gateway: HTTP + WebSocket on one port."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from ollama import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from educlaw.agent.deps import AgentDeps
from educlaw.agent.root import build_root_agent
from educlaw.config.settings import load_settings
from educlaw.config.strict_local import assert_strict_local
from educlaw.gateway import webhooks
from educlaw.gateway.ws import handle_ws
from educlaw.ir.store import IrStore
from educlaw.memory.adk_memory_service import DagestanMemoryService
from educlaw.memory.dagestan import Dagestan
from educlaw.memory.embeddings import EmbeddingClient
from educlaw.memory.models import Base as OrmBase
from educlaw.memory.vec_store import VecStore
from educlaw.safety.shield import Shield


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    if settings.strict_local:
        assert_strict_local(settings.ollama_url)

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    ir_root = settings.ir_root or (settings.data_dir / "ir")
    ir_root.mkdir(parents=True, exist_ok=True)

    sqlite_url = f"sqlite+aiosqlite:///{settings.sqlite_path}"
    engine = create_async_engine(sqlite_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(OrmBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    ir = IrStore(session_factory)
    await ir.reindex_disk(ir_root)

    embed = EmbeddingClient(settings.ollama_url)
    try:
        dim = len((await embed.embed(settings.embedding_model, ["__dim_probe__"]))[0])
    except Exception:
        dim = settings.embedding_dim
    vec_path = settings.vec_sqlite_path or (settings.data_dir / "vectors.sqlite")
    vec = VecStore(vec_path, dim)
    dagestan = Dagestan(
        session_factory,
        vec,
        embed,
        settings.embedding_model,
    )

    shield = Shield(AsyncClient(host=settings.ollama_url), model=settings.shield_model)

    from educlaw.sandbox.null_sandbox import NullSandbox

    sandbox: Any = NullSandbox()

    deps = AgentDeps(
        settings=settings,
        ir=ir,
        dagestan=dagestan,
        shield=shield,
        sandbox=sandbox,
    )
    agent = build_root_agent(deps)
    session_service = InMemorySessionService()
    memory_service = DagestanMemoryService(dagestan)
    runner = Runner(
        app_name=settings.app_name,
        agent=agent,
        session_service=session_service,
        memory_service=memory_service,
        auto_create_session=True,
    )

    app.state.settings = settings
    app.state.runner = runner
    app.state.engine = engine
    yield
    await engine.dispose()


app = FastAPI(title="EduClaw Gateway", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    runner: Runner = ws.app.state.runner
    settings = ws.app.state.settings
    await handle_ws(ws, runner, settings)


app.include_router(webhooks.router)
