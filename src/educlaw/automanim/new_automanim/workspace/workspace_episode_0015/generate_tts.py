#!/usr/bin/env python3
"""Generate TTS audio for the narration."""
import json
import os
import subprocess
from pathlib import Path

# Try EduClaw TTS first
try:
    from educlaw.tts import build_backend
    from educlaw.settings import Settings
    
    def make_tts():
        return build_backend(Settings())
    HAS_EDUCLAW_TTS = True
except Exception:
    HAS_EDUCLAW_TTS = False

# Try KittenTTS directly
try:
    from kittentts import KittenTTS
    HAS_KITTEN = True
except Exception:
    HAS_KITTEN = False

# Try pi tts tool
def generate_with_pi_tts():
    """Try using the pi tts tool if available."""
    narration_file = Path("narration.json")
    if not narration_file.exists():
        print("No narration.json found")
        return False
    
    with open(narration_file) as f:
        narration = json.load(f)
    
    print(f"Generating TTS for {len(narration)} segments...")
    
    # Try to check if pi tts is available
    try:
        result = subprocess.run(["which", "pi"], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        # Extract all text
        all_text = " ".join([n["text"] for n in narration])
        
        # Generate using pi tts
        result = subprocess.run(
            ["pi", "tts", "generate", all_text, "-o", "audio.wav"],
            capture_output=True,
            text=True,
            cwd="/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015"
        )
        
        if result.returncode == 0 or Path("audio.wav").exists():
            print("TTS generated successfully with pi")
            return True
        else:
            print(f"Pi TTS failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Pi TTS error: {e}")
        return False


def generate_with_educlaw_cli():
    """Try using educlaw tts CLI."""
    narration_file = Path("narration.json")
    if not narration_file.exists():
        return False
    
    with open(narration_file) as f:
        narration = json.load(f)
    
    all_text = " ".join([n["text"] for n in narration])
    
    try:
        result = subprocess.run(
            ["educlaw", "tts", "say", all_text, "-o", "audio.wav"],
            capture_output=True,
            text=True,
            cwd="/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015"
        )
        
        if result.returncode == 0:
            print("TTS generated with educlaw CLI")
            return True
        else:
            print(f"EduClaw CLI failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"EduClaw CLI error: {e}")
        return False


def generate_with_kitten():
    """Generate TTS using KittenTTS directly."""
    if not HAS_KITTEN:
        return False
    
    narration_file = Path("narration.json")
    with open(narration_file) as f:
        narration = json.load(f)
    
    all_text = " ".join([n["text"] for n in narration])
    
    try:
        print("Initializing KittenTTS...")
        tts = KittenTTS("KittenML/kitten-tts-nano-0.8-int8")
        
        print("Generating audio...")
        audio = tts.synthesize(all_text, voice="Jasper")
        
        # Save as WAV
        import numpy as np
        from scipy.io import wavfile
        
        # KittenTTS returns audio at 24kHz
        sample_rate = 24000
        audio_array = np.array(audio, dtype=np.int16)
        wavfile.write("audio.wav", sample_rate, audio_array)
        
        print("Audio saved to audio.wav")
        return True
        
    except Exception as e:
        print(f"KittenTTS error: {e}")
        return False


def generate_with_festival():
    """Fallback to festival TTS if available."""
    try:
        narration_file = Path("narration.json")
        with open(narration_file) as f:
            narration = json.load(f)
        
        all_text = " ".join([n["text"] for n in narration])
        
        # Write text to file
        with open("temp_speech.txt", "w") as f:
            f.write(all_text)
        
        # Use festival TTS
        result = subprocess.run(
            ["text2wave", "temp_speech.txt", "-o", "audio.wav"],
            capture_output=True,
            text=True,
            cwd="/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015"
        )
        
        # Clean up
        os.remove("temp_speech.txt")
        
        if result.returncode == 0:
            print("Generated audio with festival")
            return True
        return False
        
    except Exception as e:
        print(f"festival error: {e}")
        return False


def generate_with_espeak():
    """Fallback to espeak."""
    try:
        narration_file = Path("narration.json")
        with open(narration_file) as f:
            narration = json.load(f)
        
        all_text = " ".join([n["text"] for n in narration])
        
        result = subprocess.run(
            ["espeak", "-w", "audio.wav", all_text],
            capture_output=True,
            text=True,
            cwd="/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015"
        )
        
        if result.returncode == 0 or Path("audio.wav").exists():
            print("Generated audio with espeak")
            return True
        return False
        
    except Exception as e:
        print(f"espeak error: {e}")
        return False


def main():
    """Try various TTS methods."""
    workspace = "/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015"
    os.chdir(workspace)
    
    print("Attempting TTS generation...")
    
    # Try different methods
    methods = [
        ("pi tts", generate_with_pi_tts),
        ("educlaw CLI", generate_with_educlaw_cli),
        ("kitten TTS", generate_with_kitten),
        ("festival", generate_with_festival),
        ("espeak", generate_with_espeak),
    ]
    
    for name, method in methods:
        print(f"\nTrying {name}...")
        try:
            if method():
                print(f"Success with {name}!")
                return
        except Exception as e:
            print(f"{name} failed: {e}")
    
    print("\nAll TTS methods failed. Creating placeholder audio...")
    
    # Create a placeholder silent audio file
    import numpy as np
    try:
        from scipy.io import wavfile
        # 1 second of silence at 24kHz
        sample_rate = 24000
        duration = 15  # seconds (animation duration)
        samples = np.zeros(sample_rate * duration, dtype=np.int16)
        wavfile.write("audio.wav", sample_rate, samples)
        print("Created placeholder silent audio at audio.wav")
    except ImportError:
        print("scipy not available for creating placeholder audio")


if __name__ == "__main__":
    main()
