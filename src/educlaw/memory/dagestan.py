"""Hybrid temporal memory (facts + embedded logs)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from educlaw.memory.models import EmbeddedLog, Fact

if TYPE_CHECKING:
    from educlaw.memory.embeddings import EmbeddingClient
    from educlaw.memory.vec_store import VecStore


class Dagestan:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        vec: VecStore,
        embed: EmbeddingClient,
        embedding_model: str,
    ) -> None:
        self._sf = session_factory
        self._vec = vec
        self._embed = embed
        self._emb_model = embedding_model

    async def snapshot(self, subject: str, at: datetime | None = None) -> list[Fact]:
        at = at or datetime.now(UTC)
        async with self._sf() as s:
            stmt = select(Fact).where(
                and_(
                    Fact.subject == subject,
                    Fact.valid_from <= at,
                    or_(Fact.valid_until.is_(None), Fact.valid_until > at),
                )
            )
            return list((await s.scalars(stmt)).all())

    async def assert_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        confidence: float,
        source_log_id: str | None = None,
    ) -> Fact:
        async with self._sf() as s, s.begin():
            now = datetime.now(UTC)
            existing = await s.scalar(
                select(Fact).where(
                    and_(
                        Fact.subject == subject,
                        Fact.predicate == predicate,
                        Fact.object == object,
                        Fact.valid_until.is_(None),
                    )
                )
            )
            new = Fact(
                id=str(uuid.uuid4()),
                subject=subject,
                predicate=predicate,
                object=object,
                valid_from=now,
                valid_until=None,
                confidence=confidence,
                source_log_id=source_log_id,
            )
            s.add(new)
            if existing:
                existing.valid_until = now
                existing.superseded_by = new.id
            await s.flush()
            return new

    async def ingest_log(self, session_id: str, role: str, text: str) -> str:
        log_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        async with self._sf() as s, s.begin():
            s.add(EmbeddedLog(id=log_id, session_id=session_id, role=role, ts=now, text=text))
        if text.strip():
            vec = (await self._embed.embed(self._emb_model, [text]))[0]
            self._vec.upsert(key=log_id, vec=vec, payload=session_id)
        return log_id

    async def recall(self, query_text: str, k: int = 6) -> list[tuple[str, str]]:
        qvec = (await self._embed.embed(self._emb_model, [query_text]))[0]
        return [(key, payload) for key, payload, _ in self._vec.top_k(qvec, k=k)]
