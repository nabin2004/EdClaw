"""Gateway AgentRuntime + execution engines."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from educlaw.config.settings import Settings
from educlaw.gateway.agents.execution.base import StubExecutionEngine
from educlaw.gateway.agents.execution.factory import build_execution_engine
from educlaw.gateway.agents.execution.ollama_chat_engine import OllamaChatExecutionEngine
from educlaw.gateway.agents.runtime import AgentRuntime
from educlaw.gateway.agents.session import AgentSession
from educlaw.gateway.agents.tools import create_default_tools
from educlaw.gateway.events.bus import EventBus
from educlaw.gateway.storage.session_store import SessionStore


class FakeStreamer:
    def __init__(self) -> None:
        self.tokens: list[str] = []
        self.events: list[tuple[str, object]] = []

    async def token(self, t: str) -> None:
        self.tokens.append(t)

    async def event(self, event_type: str, data: object) -> None:
        self.events.append((event_type, data))


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
    assert [e[0] for e in stream.events] == ["assistant.status", "assistant.status"]
    assert stream.events[0][1] == {"phase": "start"}
    assert stream.events[-1][1] == {"phase": "end"}


@pytest.mark.asyncio
async def test_ollama_chat_engine_streams_and_returns() -> None:
    chunks = [
        json.dumps({"message": {"content": "Hel"}}),
        json.dumps({"message": {"content": "lo"}}),
    ]

    class FakeResponse:
        status_code = 200

        async def aiter_lines(self):
            for line in chunks:
                yield line

    class FakeStreamCm:
        def __init__(self) -> None:
            self.response = FakeResponse()

        async def __aenter__(self) -> FakeResponse:
            return self.response

        async def __aexit__(self, *_args: object) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, *_a: object, **_kw: object) -> None:
            pass

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def stream(
            self,
            _method: str,
            _url: str,
            json: object | None = None,
        ) -> FakeStreamCm:
            assert isinstance(json, dict)
            assert json.get("think") is False
            assert json.get("model") == "m1"
            return FakeStreamCm()

    stream = FakeStreamer()
    eng = OllamaChatExecutionEngine(
        Settings(
            gateway_execution_engine="ollama",
            model_id="m1",
            ollama_url="http://127.0.0.1:11434",
            ollama_chat_think=False,
        ),
    )
    store = SessionStore()
    sess = AgentSession(store, "o1")
    sess.add_user_message("hi")
    tools = create_default_tools()

    with patch(
        "educlaw.gateway.agents.execution.ollama_chat_engine.httpx.AsyncClient",
        FakeAsyncClient,
    ):
        text = await eng.run(sess, "hi", tools, stream)

    assert text == "Hello"
    assert stream.tokens == ["Hel", "lo"]


@pytest.mark.asyncio
async def test_ollama_chat_engine_http_error_raises() -> None:
    class ErrResponse:
        status_code = 500

        async def aread(self) -> bytes:
            return b"nope"

    class FakeStreamCm:
        async def __aenter__(self) -> ErrResponse:
            return ErrResponse()

        async def __aexit__(self, *_args: object) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, *_a: object, **_kw: object) -> None:
            pass

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def stream(self, *_a: object, **_kw: object) -> FakeStreamCm:
            return FakeStreamCm()

    eng = OllamaChatExecutionEngine(
        Settings(model_id="m1", ollama_url="http://127.0.0.1:11434"),
    )
    store = SessionStore()
    sess = AgentSession(store, "o2")
    sess.add_user_message("x")
    tools = create_default_tools()
    stream = FakeStreamer()

    with patch(
        "educlaw.gateway.agents.execution.ollama_chat_engine.httpx.AsyncClient",
        FakeAsyncClient,
    ):
        with pytest.raises(RuntimeError, match="HTTP 500"):
            await eng.run(sess, "x", tools, stream)


def test_build_execution_engine_selects_ollama() -> None:
    eng = build_execution_engine(Settings(gateway_execution_engine="ollama"))
    assert isinstance(eng, OllamaChatExecutionEngine)
