#!/usr/bin/env python3
"""Generate TTS audio from narration.json using OpenAI API."""

import os
import json
from openai import OpenAI


def generate_tts():
    # Read narration
    with open("narration.json", "r") as f:
        narrations = json.load(f)
    
    # Combine all text with natural pauses
    client = OpenAI()
    
    # Generate TTS for full narration with pauses between sentences
    full_text = " ".join([n["text"] for n in narrations])
    voice = narrations[0].get("voice", "alloy")
    if voice == "default" or voice == "fable":
        voice = "alloy"  # Default OpenAI voice
    
    print(f"Generating TTS with voice '{voice}'...")
    print(f"Text length: {len(full_text)} characters")
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=full_text,
    )
    
    response.stream_to_file("audio.wav")
    print("Generated audio.wav")


if __name__ == "__main__":
    generate_tts()
