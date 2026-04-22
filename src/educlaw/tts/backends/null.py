from __future__ import annotations

import io
import wave

from educlaw.config.settings import Settings
from educlaw.tts.contract import TTSAudio, TTSBackend, TTSRequest
from educlaw.tts.registry import register


def _silent_wav_pcm16_mono(sample_rate: int, duration_s: float = 1.0) -> bytes:
    buf = io.BytesIO()
    n_frames = max(1, int(sample_rate * duration_s))
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)
    return buf.getvalue()


class NullTTSBackend:
    """Returns short silent WAV audio (no external deps). Useful for tests and CI."""

    name = "null"

    def __init__(self) -> None:
        self.available_voices: list[str] = ["(silent)"]

    async def synthesize(self, req: TTSRequest) -> TTSAudio:
        sr = req.sample_rate
        data = _silent_wav_pcm16_mono(sr, duration_s=0.5)
        return TTSAudio(audio_bytes=data, sample_rate=sr, voice=req.voice, format="wav")

    async def close(self) -> None:
        return None


def factory(_settings: Settings) -> TTSBackend:
    return NullTTSBackend()


register("null", factory)
