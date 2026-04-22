import io
import wave
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from educlaw.gateway.app import app
from educlaw.safety.shield import Shield, Verdict
from educlaw.tts.contract import TTSAudio, TTSRequest


def _tiny_wav(sr: int = 8000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b"\x00\x00" * 80)
    return buf.getvalue()


class _FakeTTS:
    name = "fake"
    available_voices = ["A"]

    async def synthesize(self, req: TTSRequest) -> TTSAudio:
        return TTSAudio(
            audio_bytes=_tiny_wav(req.sample_rate),
            sample_rate=req.sample_rate,
            voice=req.voice or "A",
            format="wav",
        )

    async def close(self) -> None:
        return None


def test_ws_tts_streams_audio_and_done(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Shield, "classify", AsyncMock(return_value=Verdict.ALLOW))

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "connect", "token": "u:tts-test"})
            assert ws.receive_json()["type"] == "connected"
            client.app.state.deps.tts = _FakeTTS()
            ws.send_json({"type": "tts", "text": "Hello"})
            first = ws.receive_json()
            assert first["type"] == "tts_event"
            assert first["payload"]["kind"] == "audio"
            assert first["payload"]["format"] == "wav"
            assert first["payload"]["bytes_b64"]
            second = ws.receive_json()
            assert second["type"] == "tts_event"
            assert second["payload"]["kind"] == "done"


def test_ws_tts_disabled_when_no_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Shield, "classify", AsyncMock(return_value=Verdict.ALLOW))

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "connect", "token": "u:tts-test2"})
            ws.receive_json()
            client.app.state.deps.tts = None
            ws.send_json({"type": "tts", "text": "Hello"})
            msg = ws.receive_json()
            assert msg["type"] == "tts_event"
            assert msg["payload"]["kind"] == "error"
            assert "disabled" in msg["payload"]["message"].lower()


def test_ws_tts_empty_text_errors() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "connect", "token": "u:tts-test3"})
            ws.receive_json()
            ws.send_json({"type": "tts", "text": "  "})
            msg = ws.receive_json()
            assert msg["payload"]["kind"] == "error"
