#!/usr/bin/env python3
"""Generate TTS audio by combining narration segments."""
import json
import subprocess
import sys
import os

def generate_tts_segment(text, output_file, voice='en-US-Standard-C', speed=1.0):
    """Generate audio for a text segment using available TTS tools."""
    
    # Try espeak-ng first
    if os.system('which espeak-ng > /dev/null 2>&1') == 0:
        cmd = ['espeak-ng', '-w', output_file, text]
        subprocess.run(cmd, check=True)
        return True
    
    # Try espeak
    if os.system('which espeak > /dev/null 2>&1') == 0:
        cmd = ['espeak', '-w', output_file, text]
        subprocess.run(cmd, check=True)
        return True
    
    # Try pico2wave
    if os.system('which pico2wave > /dev/null 2>&1') == 0:
        cmd = ['pico2wave', '-w', output_file, text]
        subprocess.run(cmd, check=True)
        return True
    
    # Try text2wave
    if os.system('which text2wave > /dev/null 2>&1') == 0:
        cmd = ['text2wave', '-o', output_file]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        proc.communicate(text.encode())
        return True
    
    return False

def main():
    # Load narration
    with open('narration.json', 'r') as f:
        narration = json.load(f)
    
    # Check for available TTS tools
    tts_tools = []
    for tool in ['espeak-ng', 'espeak', 'pico2wave', 'text2wave', 'flite']:
        if os.system(f'which {tool} > /dev/null 2>&1') == 0:
            tts_tools.append(tool)
    
    print(f"Available TTS tools: {tts_tools}", file=sys.stderr)
    
    if not tts_tools:
        print("No TTS tools available, creating placeholder audio", file=sys.stderr)
        # Create silent/placeholder audio
        import numpy as np
        import wave
        
        duration = len(narration) * 4  # Approx 4 seconds per segment
        sample_rate = 22050
        num_samples = int(duration * sample_rate)
        
        # Create a low-volume sine wave tone
        t = np.linspace(0, duration, num_samples, False)
        audio = 0.05 * np.sin(2 * np.pi * 440 * t)
        audio = (audio * 32767).astype(np.int16)
        
        with wave.open('audio.wav', 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(audio.tobytes())
        return
    
    # Generate audio for each segment
    segment_files = []
    for i, item in enumerate(narration):
        segment_file = f'segment_{i:03d}.wav'
        text = item['text']
        voice = item.get('voice', 'en-US-Standard-C')
        speed = item.get('speed', 1.0)
        
        try:
            if generate_tts_segment(text, segment_file, voice, speed):
                segment_files.append(segment_file)
                print(f"Generated segment {i}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to generate segment {i}: {e}", file=sys.stderr)
    
    if segment_files:
        # Concatenate segments using ffmpeg
        with open('segments.txt', 'w') as f:
            for sf in segment_files:
                f.write(f"file '{sf}'\n")
        
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'segments.txt', '-c', 'copy', 'audio.wav']
        subprocess.run(cmd, check=True)
        
        # Cleanup
        os.remove('segments.txt')
        for sf in segment_files:
            os.remove(sf)
        
        print("Audio generated successfully: audio.wav", file=sys.stderr)
    else:
        print("No audio segments generated", file=sys.stderr)

if __name__ == '__main__':
    main()
