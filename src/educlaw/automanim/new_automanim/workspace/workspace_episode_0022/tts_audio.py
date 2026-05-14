#!/usr/bin/env python3
import wave
import struct
import sys

# Try to use pyttsx3 or similar TTS
audio_data = []

try:
    # First try pyttsx3
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    
    # Read narration
    import json
    with open('narration.json', 'r') as f:
        narrations = json.load(f)
    
    text = " ".join([n['text'] for n in narrations])
    engine.save_to_file(text, 'audio.wav')
    engine.runAndWait()
    print("Generated TTS audio using pyttsx3")
    
except Exception as e:
    print(f"pyttsx3 failed: {e}")
    
    # Fallback: generate silence with duration based on text length
    # This is a placeholder - ideally we'd use actual TTS
    
    import json
    with open('narration.json', 'r') as f:
        narrations = json.load(f)
    
    text = " ".join([n['text'] for n in narrations])
    
    # Estimate duration: ~0.5s per word + 2s buffer
    num_words = len(text.split())
    duration = max(num_words * 0.5 + 2, 20)  # minimum 20 seconds
    sample_rate = 44100
    
    print(f"Generating {duration:.1f}s of placeholder audio (no TTS available)")
    
    w = wave.open('audio.wav', 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sample_rate)
    
    num_samples = int(sample_rate * duration)
    
    # Generate low-volume noise/pulse instead of tone
    import random
    for i in range(num_samples):
        # Very quiet noise
        sample = int(1000 * (random.random() - 0.5))
        w.writeframes(struct.pack('h', sample))
    
    w.close()
    print(f"Created placeholder audio.wav ({duration:.1f}s)")

if __name__ == "__main__":
    pass
