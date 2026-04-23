"""Safety classifier via Ollama ``generate`` (temperature 0, short completion)."""

from __future__ import annotations

from enum import StrEnum

from ollama import AsyncClient


class Verdict(StrEnum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


_PROMPT = """You are a safety classifier. Categories:
- dangerous_content
- harassment
- hate_speech
- sexually_explicit
Text:
\"\"\"{text}\"\"\"
Respond with EXACTLY one token: ALLOW, REVIEW, or BLOCK."""


class Shield:
    def __init__(self, client: AsyncClient | None = None, model: str = "gemma3:latest") -> None:
        self._client = client or AsyncClient(host="http://127.0.0.1:11434")
        self._model = model

    async def classify(self, text: str) -> Verdict:
        out = await self._client.generate(
            model=self._model,
            prompt=_PROMPT.format(text=text),
            options={"temperature": 0, "num_predict": 8},
        )
        token = (out.get("response") or "").strip().upper().split()[:1]
        match token:
            case ["BLOCK"]:
                return Verdict.BLOCK
            case ["REVIEW"]:
                return Verdict.REVIEW
            case _:
                return Verdict.ALLOW
