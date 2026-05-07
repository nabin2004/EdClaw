"""Gateway AgentRuntime + execution engines."""

from __future__ import annotations

import pytest

from educlaw.gateway.agents.execution.base import StubExecutionEngine
from educlaw.gateway.agents.runtime import AgentRuntime
from educlaw.gateway.agents.session import AgentSession
from educlaw.gateway.agents.tools import create_default_tools
from educlaw.gateway.events.bus import EventBus
from educlaw.gateway.storage.session_store import SessionStore


class FakeStreamer:
    def __init__(self) -> None:
        self.tokens: list[str] = []

    async def token(self, t: str) -> None:
        self.tokens.append(t)

    async def event(self, event_type: str, data: object) -> None:
        del event_type, data


@pytest.mark.asyncio
async def test_stub_execution_engine_streams_and_returns() -> None:
    stream = FakeStreamer()
    eng = StubExecutionEngine()
    store = SessionStore()
    sess = AgentSession(store, "s1")
    tools = create_default_tools()
    text = await eng.run(sess, "hello", tools, stream)
    assert "Stub response" in text
    assert stream.tokens


@pytest.mark.asyncio
async def test_agent_runtime_delegates_to_engine() -> None:
    stream = FakeStreamer()
    store = SessionStore()
    sess = AgentSession(store, "s2")
    tools = create_default_tools()
    bus = EventBus()
    rt = AgentRuntime(tools, bus, StubExecutionEngine())
    await rt.run(sess, "ping", stream)

    roles = [m["role"] for m in sess.messages]
    assert roles == ["user", "assistant"]
    assert sess.messages[0]["content"] == "ping"
    assert "Stub response" in sess.messages[1]["content"]
