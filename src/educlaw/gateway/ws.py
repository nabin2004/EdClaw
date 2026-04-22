"""WebSocket bridge: JSON frames ↔ ``Runner.run_async``, autocourse, or TTS."""

from __future__ import annotations

import base64
from typing import Any, cast

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.genai import types
from ollama import AsyncClient

from educlaw.agent.deps import AgentDeps
from educlaw.autocourse.orchestrator import run_autocourse
from educlaw.gateway.auth import idempotency_get, idempotency_put, verify_pairing_token
from educlaw.gateway.events_serial import event_to_wire
from educlaw.safety.shield import Verdict
from educlaw.tts.contract import TTSRequest


def _user_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def _autocourse_wire(event_payload: dict) -> dict:
    return {"type": "autocourse_event", "payload": event_payload}


def _tts_wire(event_payload: dict) -> dict:
    return {"type": "tts_event", "payload": event_payload}


async def handle_ws(ws: WebSocket, runner: Runner, deps: AgentDeps) -> None:
    await ws.accept()
    try:
        first = await ws.receive_json()
    except WebSocketDisconnect:
        return
    if first.get("type") != "connect":
        await ws.close(code=4001, reason="first frame must be connect")
        return
    try:
        client = verify_pairing_token(str(first.get("token", "")))
    except ValueError:
        await ws.close(code=4003, reason="invalid token")
        return

    await ws.send_json({"type": "connected", "session_id": client.session_id})

    while True:
        try:
            frame = await ws.receive_json()
        except WebSocketDisconnect:
            break

        idem = frame.get("idempotency_key")
        ck = f"{client.user_id}:{client.session_id}"
        if idem:
            cached = idempotency_get(ck, idem)
            if cached is not None:
                await ws.send_json(cached)
                continue

        if frame.get("type") == "tts":
            tts_batch: list[dict] = []
            text = (frame.get("text") or "").strip()
            if not text:
                wire = _tts_wire({"kind": "error", "message": "Empty text"})
                tts_batch.append(wire)
                await ws.send_json(wire)
            else:
                verdict = await deps.shield.classify(text)
                if verdict == Verdict.BLOCK:
                    wire = _tts_wire(
                        {"kind": "error", "message": "Input blocked by safety policy."}
                    )
                    tts_batch.append(wire)
                    await ws.send_json(wire)
                elif deps.tts is None:
                    wire = _tts_wire({"kind": "error", "message": "TTS disabled"})
                    tts_batch.append(wire)
                    await ws.send_json(wire)
                else:
                    raw_voice = frame.get("voice")
                    voice: str | None = None
                    if isinstance(raw_voice, str) and raw_voice.strip():
                        voice = raw_voice.strip()
                    raw_speed = frame.get("speed")
                    if isinstance(raw_speed, (int, float)):
                        spd = float(raw_speed)
                    else:
                        spd = float(deps.settings.tts_speed)
                    try:
                        req = TTSRequest(
                            text=text,
                            voice=voice or deps.settings.tts_voice,
                            speed=spd,
                            sample_rate=int(deps.settings.tts_sample_rate),
                        )
                        audio = await deps.tts.synthesize(req)
                        wire = _tts_wire(
                            {
                                "kind": "audio",
                                "format": audio.format,
                                "sample_rate": audio.sample_rate,
                                "voice": audio.voice,
                                "bytes_b64": base64.b64encode(audio.audio_bytes).decode("ascii"),
                            }
                        )
                        tts_batch.append(wire)
                        await ws.send_json(wire)
                        done = _tts_wire({"kind": "done"})
                        tts_batch.append(done)
                        await ws.send_json(done)
                    except Exception as e:  # noqa: BLE001 — surface synthesis errors
                        err = _tts_wire({"kind": "error", "message": str(e)})
                        tts_batch.append(err)
                        await ws.send_json(err)
            if idem:
                idempotency_put(ck, idem, {"type": "batch", "events": tts_batch})
            continue

        if frame.get("type") != "message":
            continue

        text = frame.get("text") or ""
        if not text.strip():
            continue
        out_events: list[dict] = []

        if frame.get("mode") == "autocourse":
            verdict = await deps.shield.classify(text)
            if verdict == Verdict.BLOCK:
                wire = _autocourse_wire(
                    {"kind": "error", "message": "Input blocked by safety policy."}
                )
                out_events.append(wire)
                await ws.send_json(wire)
                if idem:
                    idempotency_put(ck, idem, {"type": "batch", "events": out_events})
                continue

            ollama = AsyncClient(host=deps.settings.ollama_url)
            try:
                async for ac_ev in run_autocourse(text, deps.settings, ollama):
                    payload = ac_ev.model_dump(mode="json", exclude_none=True)
                    wire = _autocourse_wire(payload)
                    out_events.append(wire)
                    await ws.send_json(wire)
            finally:
                await cast(Any, ollama).close()
        else:
            async for ev in runner.run_async(
                user_id=client.user_id,
                session_id=client.session_id,
                new_message=_user_message(text),
            ):
                wire = event_to_wire(ev)
                out_events.append(wire)
                await ws.send_json(wire)
        if idem:
            idempotency_put(ck, idem, {"type": "batch", "events": out_events})
