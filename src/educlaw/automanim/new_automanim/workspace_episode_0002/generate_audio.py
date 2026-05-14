import json
import asyncio
import subprocess
import os
from educlaw.tts import build_backend, TTSRequest
from educlaw.config.settings import Settings
from educlaw.tts.contract import TTSAudio

async def main():
    # Force enable TTS and set backend for this script
    # Since we can't easily modify the Settings object after it's loaded in a way that's reliable,
    # we will try to override the environment variables that Settings uses.
    os.environ["EDUCLAW_TTS_ENABLED"] = "true"
    os.environ["EDUCLAW_TTS_BACKEND"] = "kitten"
    # We need a model_id for kitten
    os.environ["EDUCLAW_TTS_MODEL_ID"] = "KittenML/kitten-tts-nano-0.8-int8"

    settings = Settings()
    backend = build_backend(settings)
    if not backend:
        print(f"TTS backend not available. Settings: tts_enabled={settings.tts_enabled}, backend={settings.tts_backend}")
        return

    with open("narration.json", "r") as f:
        narration = json.load(f)

    all_audio_segments = []

    for entry in narration:
        print(f"Generating audio for: {entry['text']}")
        request = TTSRequest(
            text=entry["text"],
            voice=entry.get("voice"),
            speed=entry.get("speed", 1.0)
        )
        try:
            audio: TTSAudio = await backend.synthesize(request)
            all_audio_segments.append(audio)
        except Exception as e:
            print(f"Error synthesizing: {e}")

    if not all_audio_segments:
        print("No audio segments generated.")
        return

    # Save each segment to a temporary file
    for i, audio in enumerate(all_audio_segments):
        filename = f"segment_{i}.wav"
        with open(filename, "wb") as f:
            f.write(audio.audio_bytes)
        print(f"Saved {filename}")

    # Use ffmpeg to concatenate the wav files
    with open("concat_list.txt", "w") as f:
        for i in range(len(all_audio_segments)):
            f.write(f"file 'segment_{i}.wav'\n")

    try:
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_list.txt", "-c", "copy", "audio.wav"], check=True)
        print("Successfully created audio.wav")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
