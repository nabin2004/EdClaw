#!/usr/bin/env python3
"""Generate TTS audio for narration.json using gTTS."""

import json
import subprocess
import os
from gtts import gTTS


# Read narration
with open("narration.json", "r") as f:
    narrations = json.load(f)

# Generate audio for each segment
segment_files = []
for i, seg in enumerate(narrations):
    output_file = f"segment_{i:03d}.mp3"
    segment_files.append(output_file)

    # gTTS doesn't support speed directly, but we can vary the speed via ffmpeg later
    # Use the text and convert
    tts = gTTS(text=seg["text"], lang="en", slow=False)
    tts.save(output_file)
    print(f"Generated: {output_file}")

# Concatenate all segments using ffmpeg
concat_list = "concat_list.txt"
with open(concat_list, "w") as f:
    for seg_file in segment_files:
        f.write(f"file '{seg_file}'\n")

# Convert mp3 to wav for final output
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", concat_list, "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
    "audio.wav"
], check=True)

print("Generated: audio.wav")

# Cleanup temporary files
for f in segment_files + [concat_list]:
    if os.path.exists(f):
        os.remove(f)

print("Audio generation complete!")
