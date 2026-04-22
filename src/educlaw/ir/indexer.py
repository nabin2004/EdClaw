"""CLI helper: embed IR objectives into vector store (embed once, search many)."""

from __future__ import annotations

from pathlib import Path

from educlaw.memory.embeddings import EmbeddingClient
from educlaw.memory.vec_store import VecStore


async def build_ir_vector_index(
    *,
    ir_root: Path,
    out_db: Path,
    model: str,
    embed_client: EmbeddingClient,
) -> int:
    from educlaw.ir.loader import load_all

    nodes = load_all(ir_root)
    if not nodes:
        return 0
    texts = [n.objective for n in nodes]
    vectors = await embed_client.embed(model, texts)
    dim = len(vectors[0])
    store = VecStore(out_db, dim)
    for n, vec in zip(nodes, vectors, strict=True):
        store.upsert(key=n.id, vec=vec, payload=n.title)
    return len(nodes)
