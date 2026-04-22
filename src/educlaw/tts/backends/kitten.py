from __future__ import annotations

import io
from typing import Any

import anyio

from educlaw.config.settings import Settings
from educlaw.tts.contract import TTSAudio, TTSBackend, TTSRequest
from educlaw.tts.registry import register


class KittenTTSBackend:
    """Kitten TTS (ONNX, CPU). Requires ``pip install 'educlaw[tts-kitten]'`` and a model id."""

    name = "kitten"

    def __init__(self, settings: Settings) -> None:
        import numpy as np  # noqa: PLC0415
        from kittentts import KittenTTS  # type: ignore[import-not-found]

        model_id = settings.tts_model_id
        if not model_id:
            raise RuntimeError("tts_model_id is required for the kitten backend")
        cache = settings.tts_cache_dir or (settings.data_dir / "tts")
        cache.mkdir(parents=True, exist_ok=True)
        self._np = np
        self._model: Any = KittenTTS(model_id, cache_dir=str(cache))
        voices = getattr(self._model, "available_voices", None)
        self.available_voices: list[str] = list(voices) if voices else []
        self._default_voice = settings.tts_voice

    async def synthesize(self, req: TTSRequest) -> TTSAudio:
        import soundfile as sf  # type: ignore[import-not-found]

        voice = req.voice or self._default_voice
        if not voice:
            voice = self.available_voices[0] if self.available_voices else "Jasper"
        speed = req.speed

        def _run() -> tuple[Any, int]:
            audio = self._model.generate(req.text, voice=voice, speed=speed)
            arr = self._np.asarray(audio, dtype=self._np.float32)
            return arr, 24000

        samples, sr = await anyio.to_thread.run_sync(_run)

        buf = io.BytesIO()
        sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
        wav_bytes = buf.getvalue()
        return TTSAudio(audio_bytes=wav_bytes, sample_rate=sr, voice=voice, format="wav")

    async def close(self) -> None:
        return None


def factory(settings: Settings) -> TTSBackend:
    return KittenTTSBackend(settings)


register("kitten", factory)
