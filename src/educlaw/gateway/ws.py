"""WebSocket bridge: JSON frames ↔ ``Runner.run_async`` or autocourse pipeline."""

from __future__ import annotations

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


def _user_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def _autocourse_wire(event_payload: dict) -> dict:
    return {"type": "autocourse_event", "payload": event_payload}


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
        if frame.get("type") != "message":
            continue
        idem = frame.get("idempotency_key")
        ck = f"{client.user_id}:{client.session_id}"
        if idem:
            cached = idempotency_get(ck, idem)
            if cached is not None:
                await ws.send_json(cached)
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
