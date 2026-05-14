#!/usr/bin/env python3
import wave
import struct
import math

# Generate a simple test tone
w = wave.open('audio.wav', 'w')
w.setnchannels(1)  # mono
w.setsampwidth(2)  # 16-bit samples
w.setframerate(44100)  # 44.1 kHz sample rate

duration = 20
num_samples = 44100 * duration

for i in range(num_samples):
    # Generate a 440 Hz sine wave at 30% amplitude
    sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / 44100))
    w.writeframes(struct.pack('h', sample))

w.close()
print("Created audio.wav")
