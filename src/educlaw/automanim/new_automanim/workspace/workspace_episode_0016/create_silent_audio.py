#!/usr/bin/env python3
"""Create a silent WAV file for merging with video."""

import wave
import struct


def create_silent_wav(duration_seconds=30, output_file="audio.wav"):
    """Create a silent WAV file of specified duration."""
    sample_rate = 22050  # Hz
    num_samples = sample_rate * duration_seconds
    
    # Open file
    with wave.open(output_file, 'w') as wav_file:
        # Set parameters
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Create silent samples (all zeros)
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('h', 0))
    
    print(f"Created silent audio: {output_file} ({duration_seconds}s)")


if __name__ == "__main__":
    # Check video duration first (approx)
    create_silent_wav(duration_seconds=19, output_file="audio.wav")
