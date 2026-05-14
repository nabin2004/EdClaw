#!/usr/bin/env python3
"""Generate TTS audio for the narration using various methods."""
import json
import os
from pathlib import Path

os.chdir('/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015')

# Load narration
with open("narration.json") as f:
    narration = json.load(f)

all_text = " ".join([n["text"] for n in narration])
print(f"TTS text ({len(all_text)} chars): {all_text[:100]}...")

# Try espeak first
import subprocess

try:
    result = subprocess.run(
        ["espeak", "-w", "audio.wav", all_text],
        capture_output=True,
        text=True,
        check=True
    )
    print("Generated audio with espeak")
except Exception as e:
    print(f"espeak failed: {e}")
    
    # Create silent placeholder
    import numpy as np
    
    # Try scipy first
    try:
        from scipy.io import wavfile
    except ImportError:
        # Manual WAV header creation
        print("scipy not available, creating manual WAV")
        sample_rate = 24000
        duration = 15
        n_samples = sample_rate * duration
        
        # Create WAV header + data
        header = b'RIFF'
        fmt_chunk = b'WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
        header += (36 + n_samples * 2).to_bytes(4, 'little')  # file size - 8
        header += fmt_chunk
        header += sample_rate.to_bytes(4, 'little')
        header += sample_rate.to_bytes(4, 'little')  # byte rate
        header += b'\x02\x00\x10\x00'  # block align, bits per sample
        header += b'data' + (n_samples * 2).to_bytes(4, 'little')
        
        with open("audio.wav", "wb") as f:
            f.write(header)
            f.write(b'\x00' * (n_samples * 2))
        print("Created placeholder silent audio")
    else:
        sample_rate = 24000
        duration = 15
        samples = np.zeros(sample_rate * duration, dtype=np.int16)
        wavfile.write("audio.wav", sample_rate, samples)
        print("Created placeholder silent audio with scipy")
