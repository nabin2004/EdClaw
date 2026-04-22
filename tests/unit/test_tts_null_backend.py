import io
import wave

import pytest

from educlaw.tts.backends.null import NullTTSBackend
from educlaw.tts.contract import TTSRequest


@pytest.mark.asyncio
async def test_null_tts_produces_valid_wav() -> None:
    b = NullTTSBackend()
    req = TTSRequest(text="x", sample_rate=16000)
    out = await b.synthesize(req)
    await b.close()
    buf = io.BytesIO(out.audio_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == 16000
        assert wf.getsampwidth() == 2
