#!/usr/bin/env python3
"""Generate TTS audio from narration.json"""
import json
import asyncio
import subprocess

with open('narration.json') as f:
    narrations = json.load(f)

# Combine narration segments with pauses
segments = []
for n in narrations:
    segments.append(n['text'])

full_text = ' '.join(segments)

# Use tts command if available, otherwise create a script for manual audio
print(f"Generating TTS for: {full_text[:100]}...")

# Try edge-tts via subprocess
async def generate_tts():
    try:
        import edge_tts
        communicate = edge_tts.Communicate(full_text, "en-US-AriaNeural", rate="+10%")
        await communicate.save("audio.wav")
        print("Generated audio.wav")
    except Exception as e:
        print(f"TTS failed: {e}")
        # Create a placeholder
        print("Creating silent audio placeholder")
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "25", "-acodec", "pcm_s16le", "audio.wav",
            "-y"
        ], capture_output=True)

asyncio.run(generate_tts())
