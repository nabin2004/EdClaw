import pytest

import educlaw.tts  # noqa: F401 — register built-in backends
from educlaw.config.settings import Settings
from educlaw.tts.contract import TTSBackend, TTSRequest
from educlaw.tts.registry import build_backend, known_backends, register


def test_known_backends_includes_builtins() -> None:
    names = known_backends()
    assert "null" in names
    assert "kitten" in names


def test_build_backend_returns_none_when_disabled() -> None:
    s = Settings(tts_enabled=False)
    assert build_backend(s) is None


def test_build_backend_kitten_requires_model_id() -> None:
    s = Settings(tts_enabled=True, tts_backend="kitten", tts_model_id=None)
    with pytest.raises(RuntimeError, match="tts_model_id"):
        build_backend(s)


def test_build_backend_unknown_name() -> None:
    s = Settings(tts_enabled=True, tts_backend="no_such_backend", tts_model_id="x")
    with pytest.raises(RuntimeError, match="Unknown TTS backend"):
        build_backend(s)


def test_register_custom_backend() -> None:
    class _Echo:
        name = "echo"
        available_voices = ["e"]

        async def synthesize(self, req: TTSRequest):
            from educlaw.tts.contract import TTSAudio

            return TTSAudio(
                audio_bytes=b"RIFF....WAVE",
                sample_rate=req.sample_rate,
                voice=req.voice,
                format="wav",
            )

        async def close(self) -> None:
            return None

    def _factory(_s: Settings) -> TTSBackend:
        return _Echo()  # type: ignore[return-value]

    register("echo_test_backend", _factory)
    s = Settings(tts_enabled=True, tts_backend="echo_test_backend", tts_model_id="ignored")
    b = build_backend(s)
    assert b is not None
    assert b.name == "echo"
