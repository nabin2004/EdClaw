"""Kitten TTS subprocess runner for AutoManim (invoked from kitten.ts)."""
from __future__ import annotations

import os
import sys

import soundfile as sf
from kittentts import KittenTTS

text = sys.argv[1]
output_path = sys.argv[2]
voice = sys.argv[3]
speed = float(sys.argv[4])

model_id = os.environ.get(
    "AUTOMANIM_TTS_MODEL_ID", "KittenML/kitten-tts-nano-0.8-int8"
)
cache_dir = os.environ.get(
    "AUTOMANIM_TTS_CACHE_DIR",
    os.path.expanduser("~/.educlaw/tts"),
)
os.makedirs(cache_dir, exist_ok=True)

model = KittenTTS(model_id, cache_dir=cache_dir)

audio = model.generate(text, voice=voice, speed=speed)

sf.write(output_path, audio, 24000)

print("done")
