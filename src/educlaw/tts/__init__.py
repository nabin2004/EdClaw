"""Text-to-speech backends and registry (offline-friendly, pluggable)."""

# Register built-ins and load entry-point modules (side effects)
from educlaw.tts.backends import kitten as _kitten  # noqa: F401
from educlaw.tts.backends import null as _null  # noqa: F401
from educlaw.tts.contract import TTSAudio, TTSBackend, TTSRequest
from educlaw.tts.registry import build_backend, known_backends, load_tts_factories, register

__all__ = [
    "TTSAudio",
    "TTSBackend",
    "TTSRequest",
    "build_backend",
    "known_backends",
    "load_tts_factories",
    "register",
]
