#!/usr/bin/env python3
"""Generate TTS audio from narration segments."""
import json
import subprocess
import sys

def generate_audio():
    with open('narration.json', 'r') as f:
        narration = json.load(f)
    
    # Combine all segments
    full_text = ' '.join([item['text'] for item in narration])
    
    # Use first voice and speed setting
    voice = narration[0]['voice']
    speed = narration[0]['speed']
    
    # Map speed to rate
    rate_map = {'slow': '-10%', 'medium': '+0%', 'fast': '+10%'}
    rate = rate_map.get(speed, '+0%')
    
    print(f"Generating audio with voice: {voice}")
    print(f"Text: {full_text[:100]}...")
    
    # Generate using edge-tts
    cmd = [
        'edge-tts',
        '--text', full_text,
        '--voice', voice,
        '--rate', rate,
        '-o', 'audio.wav'
    ]
    
    subprocess.run(cmd, check=True)
    print("Audio generated: audio.wav")

if __name__ == '__main__':
    generate_audio()
