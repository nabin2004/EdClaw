#!/usr/bin/env python3
"""Generate TTS audio."""

import json
import sys
import os

def generate_audio_with_simple(text, output_file="audio.wav"):
    """Generate silent audio placeholder."""
    try:
        import wave
        import struct
        
        # Create silent mono WAV file
        # Calculate duration: ~15 chars per second at normal speaking rate + padding
        duration = max(10, len(text) / 12)  # ~12 chars per second
        sample_rate = 22050
        num_samples = int(duration * sample_rate)
        
        with wave.open(output_file, 'w') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            
            # Generate silent samples efficiently
            silent_chunk = struct.pack('h', 0) * 1024
            remaining = num_samples
            while remaining > 0:
                chunk_size = min(1024, remaining)
                wav_file.writeframes(silent_chunk[:chunk_size * 2])
                remaining -= chunk_size
        
        return True
    except Exception as e:
        print(f"Simple audio generation error: {e}")
        return False

def main():
    # Read narration
    with open("narration.json", "r") as f:
        narrations = json.load(f)
    
    # Combine all text
    full_text = " ".join([n["text"] for n in narrations])
    print(f"Generating audio placeholder for text ({len(full_text)} chars)")
    
    # Generate silent audio of appropriate duration for the narration
    if generate_audio_with_simple(full_text, "audio.wav"):
        if os.path.exists("audio.wav") and os.path.getsize("audio.wav") > 100:
            print(f"Generated audio.wav ({os.path.getsize('audio.wav')} bytes)")
            print(f"Duration: ~{len(full_text)/12:.1f} seconds")
            return
    
    print("ERROR: Failed to generate audio")
    sys.exit(1)

if __name__ == "__main__":
    main()
