#!/usr/bin/env python3
"""Generate TTS audio for narration using CLI tools."""
import json
import subprocess
import os

# Read narration
with open('narration.json') as f:
    narrations = json.load(f)

# Combine all narration text
full_text = " ".join([n['text'] for n in narrations])
print(f"Full narration text length: {len(full_text)} characters")

# Try to use espeak-ng first (usually available)
def generate_with_espeak():
    try:
        # Check if espeak-ng is available
        result = subprocess.run(['which', 'espeak-ng'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Using espeak-ng for TTS generation")
            cmd = ['espeak-ng', '-w', 'audio.wav', full_text]
            subprocess.run(cmd, check=True)
            return True
    except Exception as e:
        print(f"espeak-ng failed: {e}")
    return False

# Try using espeak as fallback
def generate_with_espeak_legacy():
    try:
        result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Using espeak for TTS generation")
            cmd = ['espeak', '-w', 'audio.wav', full_text]
            subprocess.run(cmd, check=True)
            return True
    except Exception as e:
        print(f"espeak failed: {e}")
    return False

# Try piper TTS (if available)
def generate_with_piper():
    try:
        result = subprocess.run(['which', 'piper'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Using piper for TTS generation")
            # Piper requires model download first, but let's try basic invocation
            cmd = f'echo "{full_text}" | piper --output_file audio.wav'
            subprocess.run(cmd, shell=True, check=True)
            return True
    except Exception as e:
        print(f"piper failed: {e}")
    return False

# Try festival TTS
def generate_with_festival():
    try:
        result = subprocess.run(['which', 'text2wave'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Using festival/text2wave for TTS generation")
            
            # Create scheme script
            scheme_cmd = f'(voice_cmu_us_slt_arctic_clunits) (SayText "{full_text}")'
            
            # Use text2wave
            proc1 = subprocess.Popen(['echo', scheme_cmd], stdout=subprocess.PIPE)
            proc2 = subprocess.Popen(['festival', '-b'], stdin=proc1.stdout, stdout=subprocess.PIPE)
            proc1.stdout.close()
            proc2.communicate()
            
            # Alternative: use text2wave directly
            proc1 = subprocess.Popen(['echo', full_text], stdout=subprocess.PIPE)
            with open('audio.wav', 'wb') as f:
                subprocess.run(['text2wave', '-o', 'audio.wav'], stdin=proc1.stdout)
            return True
    except Exception as e:
        print(f"festival failed: {e}")
    return False

# Install and use gTTS
def generate_with_gtts():
    try:
        print("Installing gTTS...")
        subprocess.run(['pip', 'install', '-q', 'gtts'], check=True)
        
        from gtts import gTTS
        print("Using gTTS for generation")
        
        tts = gTTS(text=full_text, lang='en', slow=False)
        tts.save('audio.wav')
        return True
    except Exception as e:
        print(f"gTTS failed: {e}")
    return False

# Try different TTS engines
generated = False

if not generated:
    generated = generate_with_espeak()

if not generated:
    generated = generate_with_espeak_legacy()

if not generated:
    generated = generate_with_festival()

if not generated:
    generated = generate_with_piper()

if not generated:
    generated = generate_with_gtts()

if generated and os.path.exists('audio.wav'):
    size = os.path.getsize('audio.wav')
    print(f"Audio generated successfully: audio.wav ({size} bytes)")
else:
    print("Failed to generate audio with any TTS engine")
    exit(1)
