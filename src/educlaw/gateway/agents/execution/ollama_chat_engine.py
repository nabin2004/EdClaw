"""Gateway execution engine: plain Ollama ``/api/chat`` NDJSON streaming."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from educlaw.config.settings import Settings
    from educlaw.gateway.agents.session import AgentSession
    from educlaw.gateway.agents.streaming import Streamer
    from educlaw.gateway.agents.tools.tools import ToolRegistry


class OllamaChatExecutionEngine:
    """One user turn via Ollama chat API; streams text chunks to the WebSocket."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(
        self,
        session: AgentSession,
        input_text: str,
        tools: ToolRegistry,
        stream: Streamer,
    ) -> str:
        del input_text, tools
        base = self._settings.ollama_url.rstrip("/")
        url = f"{base}/api/chat"
        messages: list[dict[str, Any]] = list(session.backing.messages)

        payload: dict[str, Any] = {
            "model": self._settings.model_id,
            "messages": messages,
            "stream": True,
        }
        if self._settings.ollama_chat_think is not None:
            payload["think"] = self._settings.ollama_chat_think

        accumulated = ""
        timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode(errors="replace")[:2000]
                    raise RuntimeError(
                        f"Ollama /api/chat HTTP {response.status_code}: {body or '(empty body)'}",
                    )
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError as e:
                        raise RuntimeError(f"Ollama stream: invalid JSON line: {line[:200]}") from e
                    msg = chunk.get("message") or {}
                    frag = msg.get("content") or ""
                    if frag:
                        accumulated += frag
                        await stream.token(frag)

        return accumulated if accumulated else "(no text)"
