#!/usr/bin/env python3
"""
TTS generator wrapper - tries multiple backends
"""
import sys
import json

def main():
    # Load narration
    with open('narration.json', 'r') as f:
        narration = json.load(f)
    
    text = " ".join([item['text'] for item in narration])
    print(f"Generating TTS for {len(text)} characters...")
    
    # Try edge_tts (most common)
    try:
        import edge_tts
        import asyncio
        
        async def run():
            voice = "en-US-GuyNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save("audio.wav")
        
        asyncio.run(run())
        print("Audio generated using edge_tts")
        return
    except Exception as e:
        print(f"edge_tts failed: {e}")
    
    # Try gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
        tts.save("audio_temp.mp3")
        # Convert to wav using ffmpeg
        import subprocess
        subprocess.run(["ffmpeg", "-i", "audio_temp.mp3", "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "1", "audio.wav", "-y"], check=True)
        print("Audio generated using gTTS")
        return
    except Exception as e:
        print(f"gTTS failed: {e}")
    
    # Last resort: create silent audio
    print("Creating silent placeholder audio...")
    import numpy as np
    import struct
    
    sample_rate = 48000
    duration = 25  # seconds
    samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
    
    with open('audio.wav', 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + len(samples) * 2))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', len(samples) * 2))
        f.write(samples.tobytes())
    
    print("Created silent placeholder audio (25 seconds)")

if __name__ == "__main__":
    main()
