"""Discover TTS backends via entry points and in-process registration."""

from __future__ import annotations

import importlib.metadata

from educlaw.config.settings import Settings
from educlaw.tts.contract import TTSBackend, TTSBackendFactory

_BUILTIN: dict[str, TTSBackendFactory] = {}


def register(name: str, factory: TTSBackendFactory) -> TTSBackendFactory:
    """Register a built-in backend factory (in-process)."""
    _BUILTIN[name] = factory
    return factory


def load_tts_factories(group: str = "educlaw.tts") -> dict[str, TTSBackendFactory]:
    eps = importlib.metadata.entry_points()
    if hasattr(eps, "select"):
        selected = list(eps.select(group=group))
    else:
        raw = eps.get(group)
        selected = list(raw) if raw is not None else []
    out: dict[str, TTSBackendFactory] = {}
    for ep in selected:
        out[ep.name] = ep.load()  # type: ignore[assignment]
    return out


def known_backends() -> dict[str, TTSBackendFactory]:
    """Merge built-ins with entry points; entry points override same name."""
    merged = dict(_BUILTIN)
    merged.update(load_tts_factories())
    return merged


def build_backend(settings: Settings) -> TTSBackend | None:
    """Instantiate the configured backend, or ``None`` if TTS is disabled."""
    if not settings.tts_enabled:
        return None
    if not settings.tts_model_id and settings.tts_backend == "kitten":
        raise RuntimeError(
            "TTS is enabled with backend 'kitten' but tts_model_id is unset. "
            "Set educlaw.tts_model_id (or EDUCLAW_TTS_MODEL_ID) to a Hugging Face repo id, "
            "e.g. KittenML/kitten-tts-nano-0.8-int8."
        )
    factories = known_backends()
    name = settings.tts_backend
    if name not in factories:
        keys = ", ".join(sorted(factories)) or "(none)"
        raise RuntimeError(f"Unknown TTS backend {name!r}. Known backends: {keys}")
    return factories[name](settings)
