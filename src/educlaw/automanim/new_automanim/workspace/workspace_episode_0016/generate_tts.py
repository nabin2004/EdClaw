#!/usr/bin/env python3
"""Generate TTS audio using OpenAI API."""

import sys
import json
from openai import OpenAI


def main():
    # Read narration
    with open("narration.json", "r") as f:
        narrations = json.load(f)
    
    # Combine all text
    full_text = " ".join([n["text"] for n in narrations])
    
    # Default voice
    voice = "alloy"
    
    # Check if API key is available
    client = OpenAI()
    
    print(f"Generating TTS with voice {voice}...")
    print(f"Text length: {len(full_text)} characters")
    
    # Generate audio
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=full_text,
    )
    
    # Save to file
    response.stream_to_file("audio.wav")
    print("Saved audio to audio.wav")


if __name__ == "__main__":
    main()
