"""Async adapter over PyPI `dagestan` temporal-graph memory.

Upstream: https://pypi.org/project/dagestan/ — see docs/DAGESTAN.md.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import anyio
import httpx

from educlaw.config.settings import Settings


@dataclass(frozen=True, slots=True)
class BeliefFact:
    id: str
    predicate: str
    object: str
    confidence: float


def _make_ollama_llm(base_url: str, model: str):
    base = base_url.rstrip("/")

    def call(system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"{base}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message") or {}
        return str(msg.get("content") or "")

    return call


class Dagestan:
    """EduClaw-facing async API; delegates to sync `dagestan.Dagestan` in a worker thread."""

    def __init__(self, settings: Settings) -> None:
        from dagestan import Dagestan as UpstreamDagestan

        path = settings.dagestan_db_path or (settings.data_dir / "dagestan_memory.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        db_path = str(path)

        prov = settings.dagestan_provider
        if prov == "ollama":
            self._mem = UpstreamDagestan(
                db_path=db_path,
                llm_client=_make_ollama_llm(settings.ollama_url, settings.model_id),
            )
        else:
            self._mem = UpstreamDagestan(db_path=db_path, provider=prov)

    def _sync_ingest(self, session_id: str, role: str, text: str) -> None:
        self._mem.ingest([{"role": role, "content": text}], source=session_id)

    async def ingest_log(self, session_id: str, role: str, text: str) -> str:
        log_id = str(uuid.uuid4())
        if text.strip():
            await anyio.to_thread.run_sync(self._sync_ingest, session_id, role, text)
        return log_id

    def _sync_recall(self, query_text: str, k: int) -> list[tuple[str, str]]:
        raw = self._mem.retrieve(query_text, top_k=k, as_text=False)
        if isinstance(raw, str):
            t = raw.strip()
            return [("recall", t)] if t else []
        out: list[tuple[str, str]] = []
        for r in cast(list[Any], raw):
            node = getattr(r, "node", None)
            if node is None:
                continue
            sid = getattr(node, "source", None) or ""
            out.append((str(node.id), str(sid)))
        return out

    async def recall(self, query_text: str, k: int = 6) -> list[tuple[str, str]]:
        return await anyio.to_thread.run_sync(self._sync_recall, query_text, k)

    def _sync_assert_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        confidence: float,
        source_log_id: str | None,
    ) -> BeliefFact:
        from dagestan.graph.schema import Node, NodeType

        for n in self._mem.graph.nodes:
            if n.source != subject or n.type != NodeType.PREFERENCE:
                continue
            if n.label == object and str(n.attributes.get("predicate", "")) == predicate:
                n.confidence_score = float(confidence)
                n.last_reinforced = datetime.now(UTC)
                self._mem.save()
                return BeliefFact(
                    id=n.id,
                    predicate=predicate,
                    object=object,
                    confidence=float(confidence),
                )

        attrs: dict[str, Any] = {"predicate": predicate}
        if source_log_id:
            attrs["source_log_id"] = source_log_id
        node = Node(
            type=NodeType.PREFERENCE,
            label=object,
            confidence_score=float(confidence),
            attributes=attrs,
            source=subject,
        )
        self._mem.add_node(node)
        return BeliefFact(
            id=node.id,
            predicate=predicate,
            object=object,
            confidence=float(confidence),
        )

    async def assert_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        confidence: float,
        source_log_id: str | None = None,
    ) -> BeliefFact:
        return await anyio.to_thread.run_sync(
            self._sync_assert_fact,
            subject,
            predicate,
            object,
            confidence,
            source_log_id,
        )

    def _sync_snapshot(self, subject: str) -> list[BeliefFact]:
        from dagestan.graph.schema import NodeType

        out: list[BeliefFact] = []
        for n in self._mem.graph.nodes:
            if n.source != subject or n.type != NodeType.PREFERENCE:
                continue
            pred = str(n.attributes.get("predicate", "relates_to"))
            out.append(
                BeliefFact(
                    id=n.id,
                    predicate=pred,
                    object=n.label,
                    confidence=float(n.confidence_score),
                )
            )
        out.sort(key=lambda x: x.confidence, reverse=True)
        return out

    async def snapshot(self, subject: str, at: datetime | None = None) -> list[BeliefFact]:
        del at  # reserved for temporal filtering; upstream graph uses live state
        return await anyio.to_thread.run_sync(self._sync_snapshot, subject)
