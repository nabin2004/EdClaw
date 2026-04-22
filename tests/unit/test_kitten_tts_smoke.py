"""Opt-in smoke test when ``kittentts`` is installed (``educlaw[tts-kitten]``)."""

import os

import pytest


@pytest.mark.asyncio
async def test_kitten_backend_import_and_register() -> None:
    pytest.importorskip("kittentts")
    if os.environ.get("EDUCLAW_KITTEN_SMOKE") != "1":
        pytest.skip("Set EDUCLAW_KITTEN_SMOKE=1 to run (may download ~25MB model).")
    import educlaw.tts  # noqa: F401
    from educlaw.config.settings import Settings
    from educlaw.tts.registry import build_backend

    s = Settings(
        tts_enabled=True,
        tts_backend="kitten",
        tts_model_id="KittenML/kitten-tts-nano-0.8-int8",
        tts_voice="Jasper",
    )
    b = build_backend(s)
    assert b is not None
    assert b.name == "kitten"
    voices = getattr(b, "available_voices", [])
    assert isinstance(voices, list)
    await b.close()
