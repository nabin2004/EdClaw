"""Bridge ADK ``BaseMemoryService`` to Dagestan + sqlite-vec recall."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from google.adk.memory.base_memory_service import BaseMemoryService, SearchMemoryResponse
from google.adk.memory.memory_entry import MemoryEntry
from google.genai import types

if TYPE_CHECKING:
    from google.adk.sessions.session import Session

    from educlaw.memory.dagestan import Dagestan


def _event_text(session: Session) -> str:
    parts: list[str] = []
    for ev in getattr(session, "events", []) or []:
        if getattr(ev, "content", None) and ev.content.parts:
            for p in ev.content.parts:
                if p.text:
                    parts.append(p.text)
    return "\n".join(parts)


class DagestanMemoryService(BaseMemoryService):
    def __init__(self, dagestan: Dagestan) -> None:
        self._dag = dagestan

    async def add_session_to_memory(self, session: Session) -> None:
        text = _event_text(session)
        if text.strip():
            await self._dag.ingest_log(session.id, role="session", text=text)

    async def search_memory(
        self,
        *,
        app_name: str,
        user_id: str,
        query: str,
    ) -> SearchMemoryResponse:
        hits = await self._dag.recall(query, k=8)
        memories: list[MemoryEntry] = []
        for key, payload in hits:
            memories.append(
                MemoryEntry(
                    id=key,
                    content=types.Content(
                        role="user",
                        parts=[types.Part(text=f"[memory:{key}] session={payload}")],
                    ),
                    timestamp=datetime.now(UTC).isoformat(),
                )
            )
        return SearchMemoryResponse(memories=memories)
