#!/usr/bin/env python3
"""Generate TTS audio using available libraries."""
import json
import os
import sys
import subprocess

# Full narration text
NARRATION = """Dropout is a regularization technique used in neural networks to prevent overfitting.
During training, dropout randomly sets a fraction of neuron outputs to zero.
This forces the network to learn robust features that don't rely on any single neuron.
During inference, all neurons are active, but their outputs are scaled down by the dropout rate.
This scaling ensures that the expected output during inference matches the training distribution."""

def check_command(cmd):
    """Check if a command exists."""
    try:
        subprocess.run([cmd, '--help'], capture_output=True, timeout=5)
        return True
    except:
        return False

def generate_with_edge_tts(text, output_file):
    """Try edge-tts."""
    if not check_command('edge-tts'):
        return False
    try:
        cmd = ['edge-tts', '--voice', 'en-US-AvaNeural', '--text', text, '--write-media', output_file]
        subprocess.run(cmd, capture_output=True, timeout=60)
        return os.path.exists(output_file)
    except:
        return False

def generate_with_gtts(text, output_file):
    """Try gTTS."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        return os.path.exists(output_file)
    except ImportError:
        return False
    except:
        return False

def generate_with_pyttsx3(text, output_file):
    """Try pyttsx3."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.save_to_file(text, output_file)
        engine.runAndWait()
        return os.path.exists(output_file)
    except:
        return False

def generate_with_ffmpeg(text, output_file):
    """Generate silence as fallback."""
    try:
        # Generate 30 seconds of silence
        cmd = [
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono',
            '-t', '30', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            output_file
        ]
        subprocess.run(cmd, capture_output=True, timeout=10)
        return os.path.exists(output_file)
    except:
        return False

def main():
    output_file = 'audio.wav'
    
    # Try different TTS methods
    print("Attempting to generate TTS audio...")
    
    if generate_with_edge_tts(NARRATION, output_file):
        print(f"Successfully generated audio with edge-tts: {output_file}")
        return
    
    if generate_with_gtts(NARRATION, output_file):
        print(f"Successfully generated audio with gTTS: {output_file}")
        return
    
    if generate_with_pyttsx3(NARRATION, output_file):
        print(f"Successfully generated audio with pyttsx3: {output_file}")
        return
    
    if generate_with_ffmpeg(None, output_file):
        print(f"Generated fallback silence: {output_file}")
        return
    
    print("Failed to generate audio")
    sys.exit(1)

if __name__ == '__main__':
    main()
