"""IR index + slice_for_learner (SQLAlchemy async, shared metadata with memory)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from educlaw.ir.loader import load_all
from educlaw.ir.schema import IrNode
from educlaw.memory.models import IrNodeRow


class IrStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def reindex_disk(self, root: Path) -> int:
        nodes = load_all(root)
        async with self._sf() as s, s.begin():
            await s.execute(delete(IrNodeRow))
            for n in nodes:
                s.add(
                    IrNodeRow(
                        id=n.id,
                        title=n.title,
                        objective=n.objective,
                        difficulty=n.difficulty,
                        yaml_blob="",
                    )
                )
        return len(nodes)

    async def get(self, node_id: str) -> IrNode | None:
        async with self._sf() as s:
            row = await s.scalar(select(IrNodeRow).where(IrNodeRow.id == node_id))
            if not row:
                return None
            return IrNode(
                id=row.id,
                title=row.title,
                objective=row.objective,
                difficulty=row.difficulty,
                modality=["text"],
            )

    async def slice_for_learner(self, learner_id: str, query: str | None) -> str:
        async with self._sf() as s:
            rows = (await s.scalars(select(IrNodeRow).limit(5))).all()
        parts = [f"[IR] {r.id}: {r.title} — {r.objective[:200]}" for r in rows]
        q = (query or "")[:500]
        return "\n".join(
            [
                f"Learner: {learner_id}",
                f"Latest query: {q}",
                "Relevant IR nodes:",
                *parts,
            ]
        )
