"""Gateway ``/ws``: plain text in; JSON ``assistant.status`` + ``assistant.delta`` out."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from educlaw.gateway.app import app
from educlaw.gateway.agents.execution.base import StubExecutionEngine


@pytest.fixture
def stub_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    import educlaw.gateway.run as gw_run

    monkeypatch.setattr(gw_run.runtime, "_engine", StubExecutionEngine())


def test_ws_plain_chat_streams_status_and_deltas(stub_engine: None) -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_text("hello")
            frames: list[object] = []
            while True:
                frames.append(ws.receive_json())
                last = frames[-1]
                if (
                    isinstance(last, dict)
                    and last.get("type") == "assistant.status"
                    and last.get("data", {}).get("phase") == "end"
                ):
                    break
                assert len(frames) < 200

    assert frames[0] == {"type": "assistant.status", "data": {"phase": "start"}}
    assert frames[-1] == {"type": "assistant.status", "data": {"phase": "end"}}
    types = [f.get("type") for f in frames if isinstance(f, dict)]
    assert "assistant.delta" in types


def test_ws_automanim_json_streams_progress_and_done(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_handle(session, stream, settings, payload):  # noqa: ANN001
        del session, settings, payload
        await stream.event("automanim.progress", {"kind": "plan", "message": "1 scene(s)"})
        await stream.event(
            "automanim.done",
            {
                "success": True,
                "output_dir": "/tmp/out",
                "artifact_paths": ["/tmp/a.mp4"],
                "artifact_urls": ["/artifacts/manim/ws-1/a.mp4"],
                "error": None,
            },
        )

    monkeypatch.setattr(
        "educlaw.gateway.api.websocket.automanim_handler.handle_automanim_ws",
        fake_handle,
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(
                json.dumps({"type": "automanim", "markdown": "# T\n\nbody", "metadata": {}}),
            )
            frames: list[dict] = []
            for _ in range(20):
                f = ws.receive_json()
                assert isinstance(f, dict)
                frames.append(f)
                if f.get("type") == "automanim.done":
                    break

    kinds = [f.get("type") for f in frames]
    assert "automanim.progress" in kinds
    assert "automanim.done" in kinds
    done = next(f for f in frames if f.get("type") == "automanim.done")
    assert done.get("data", {}).get("success") is True


def test_ws_unknown_json_type_routes_to_chat(stub_engine: None) -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_text('{"type":"other"}')
            deltas: list[str] = []
            while True:
                msg = ws.receive_json()
                if msg.get("type") == "assistant.delta" and isinstance(msg.get("token"), str):
                    deltas.append(msg["token"])
                if (
                    msg.get("type") == "assistant.status"
                    and msg.get("data", {}).get("phase") == "end"
                ):
                    break
    assert "Stub response" in "".join(deltas)


def test_ws_engine_failure_emits_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    class BoomEngine:
        async def run(self, session, input_text, tools, stream):  # noqa: ANN001
            del session, input_text, tools, stream
            raise RuntimeError("boom")

    import educlaw.gateway.run as gw_run

    monkeypatch.setattr(gw_run.runtime, "_engine", BoomEngine())

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_text("x")
            saw_error = False
            for _ in range(50):
                msg = ws.receive_json()
                if not isinstance(msg, dict):
                    continue
                if msg.get("type") == "assistant.status" and msg.get("data", {}).get(
                    "phase",
                ) == "error":
                    saw_error = True
                    assert "boom" in str(msg.get("data", {}).get("message", ""))
                if msg.get("type") == "assistant.status" and msg.get("data", {}).get(
                    "phase",
                ) == "end":
                    break
            assert saw_error
