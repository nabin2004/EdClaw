"""LiteLLM + Ollama chat adapter for ADK."""

from __future__ import annotations

from google.adk.models.lite_llm import LiteLlm

from educlaw.config.settings import Settings


def _is_openrouter_model(model_id: str) -> bool:
    return model_id.lower().startswith("openrouter/")


def build_model(settings: Settings) -> LiteLlm:
    if _is_openrouter_model(settings.model_id):
        return LiteLlm(model=settings.model_id)
    return LiteLlm(
        model=f"ollama_chat/{settings.model_id}",
        api_base=settings.ollama_url,
    )
