"""LiteLLM + Ollama chat adapter for ADK."""

from __future__ import annotations

from google.adk.models.lite_llm import LiteLlm

from educlaw.config.settings import Settings


def build_model(settings: Settings) -> LiteLlm:
    return LiteLlm(
        model=f"ollama_chat/{settings.model_id}",
        api_base=settings.ollama_url,
    )
