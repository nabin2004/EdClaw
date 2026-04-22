"""EmbeddingGemma (and others) via Ollama async client."""

from __future__ import annotations

from ollama import AsyncClient


class EmbeddingClient:
    def __init__(self, host: str = "http://127.0.0.1:11434") -> None:
        self._client = AsyncClient(host=host)

    async def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        out = await self._client.embed(model=model, input=inputs)
        return list(out["embeddings"])
