#!/usr/bin/env python3
"""Create audio from narration using edge-tts or alternative"""
import asyncio
import json

async def generate_audio():
    """Generate audio using edge-tts if available"""
    try:
        import edge_tts
        
        with open('narration.json', 'r') as f:
            narration = json.load(f)
        
        combined_text = " ".join([item['text'] for item in narration])
        print(f"Generating audio for: {combined_text[:50]}...")
        
        voice = "en-GB-SoniaNeural"
        communicate = edge_tts.Communicate(text=combined_text, voice=voice, rate="-5%")
        await communicate.save("audio.wav")
        print("Audio saved as audio.wav")
        return True
    except ImportError:
        print("edge_tts not available")
        return False

if __name__ == "__main__":
    # Run async function
    try:
        result = asyncio.run(generate_audio())
        if not result:
            print("Could not generate audio - TTS library not available")
            # Create placeholder silent audio using numpy
            print("Creating silent placeholder audio...")
            import numpy as np
            # Create 25 seconds of silence at 48000 Hz, 16-bit
            sample_rate = 48000
            duration = 25
            samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
            
            # Simple WAV header and data
            import struct
            with open('audio.wav', 'wb') as f:
                # RIFF header
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(samples) * 2))
                f.write(b'WAVE')
                # fmt chunk
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))  # Chunk size
                f.write(struct.pack('<H', 1))   # Audio format (PCM)
                f.write(struct.pack('<H', 1))   # Num channels (mono)
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))   # Block align
                f.write(struct.pack('<H', 16))  # Bits per sample
                # data chunk
                f.write(b'data')
                f.write(struct.pack('<I', len(samples) * 2))
                f.write(samples.tobytes())
            print("Created silent placeholder audio")
    except Exception as e:
        print(f"Error: {e}")
