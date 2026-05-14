#!/usr/bin/env python3
"""Generate TTS audio from narration.json"""
from gtts import gTTS
import json

def main():
    # Read narration file
    with open('narration.json', 'r') as f:
        narration = json.load(f)

    # Combine all narration text
    combined_text = " ".join([item['text'] for item in narration])
    print(f"Generating audio for {len(narration)} segments...")
    print(f"Combined text length: {len(combined_text)} characters")
    
    # Generate TTS audio
    tts = gTTS(text=combined_text, lang='en', tld='co.uk', slow=False)
    tts.save('audio.wav')
    print("Audio saved as audio.wav")

if __name__ == "__main__":
    main()
