from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from educlaw.autocourse.schema import AutocourseEvent
from educlaw.gateway.app import app
from educlaw.safety.shield import Shield, Verdict


class _OllamaNoNet:
    async def close(self) -> None:
        return None


def test_ws_autocourse_mode_streams_events(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run(user_prompt: str, settings: object, client: object):
        yield AutocourseEvent(
            kind="plan",
            course_title="Intro ML",
            lecture_count=1,
            audience="devs",
        )
        yield AutocourseEvent(
            kind="done",
            course_title="Intro ML",
            lecture_count=1,
            message="ok",
        )

    monkeypatch.setattr("educlaw.gateway.ws.run_autocourse", fake_run)
    monkeypatch.setattr(Shield, "classify", AsyncMock(return_value=Verdict.ALLOW))
    monkeypatch.setattr("educlaw.gateway.ws.AsyncClient", lambda *a, **k: _OllamaNoNet())

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "connect", "token": "u:pytest-session"})
            assert ws.receive_json()["type"] == "connected"
            ws.send_json({"type": "message", "mode": "autocourse", "text": "Teach me tensors"})
            first = ws.receive_json()
            assert first["type"] == "autocourse_event"
            assert first["payload"]["kind"] == "plan"
            second = ws.receive_json()
            assert second["type"] == "autocourse_event"
            assert second["payload"]["kind"] == "done"


def test_ws_autocourse_blocked_when_shield_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    async def should_not_run(*_a, **_k):
        msg = "run_autocourse should not be called when shield blocks"
        raise AssertionError(msg)
        yield AutocourseEvent(kind="plan", course_title="nope", lecture_count=0)  # pragma: no cover

    monkeypatch.setattr("educlaw.gateway.ws.run_autocourse", should_not_run)
    monkeypatch.setattr(Shield, "classify", AsyncMock(return_value=Verdict.BLOCK))

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "connect", "token": "u:pytest-session-2"})
            ws.receive_json()
            ws.send_json({"type": "message", "mode": "autocourse", "text": "bad"})
            msg = ws.receive_json()
            assert msg["type"] == "autocourse_event"
            assert msg["payload"]["kind"] == "error"
