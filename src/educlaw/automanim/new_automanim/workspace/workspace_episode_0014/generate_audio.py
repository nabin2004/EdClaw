#!/usr/bin/env python3
"""
Generate audio from narration.json using available TTS tools.
Falls back to ffmpeg-generated silence if no TTS is available.
"""

import json
import subprocess
import os
import sys

def generate_audio():
    # Load narration
    with open('narration.json', 'r') as f:
        narration = json.load(f)
    
    # Calculate total duration based on text (roughly 150 words per minute)
    total_words = sum(len(item['text'].split()) for item in narration)
    estimated_duration = max(30, total_words / 150 * 60)  # At least 30 seconds
    
    print(f"Total words: {total_words}, Estimated duration: {estimated_duration:.1f}s")
    
    # Try to use a TTS tool, otherwise create silence
    audio_files = []
    
    # Check for available TTS tools
    have_tts = False
    
    # Try edge-tts
    try:
        result = subprocess.run(['edge-tts', '--help'], capture_output=True, text=True)
        if result.returncode == 0 or 'edge' in result.stderr.lower():
            have_tts = True
            print("Found edge-tts")
    except:
        pass
    
    # Try gtts-cli
    if not have_tts:
        try:
            result = subprocess.run(['gtts-cli', '--help'], capture_output=True, text=True)
            if result.returncode == 0:
                have_tts = True
                print("Found gtts-cli")
        except:
            pass
    
    # Try espeak
    if not have_tts:
        try:
            result = subprocess.run(['espeak', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                have_tts = True
                print("Found espeak")
        except:
            pass
    
    if have_tts:
        print("Generating TTS audio...")
        # Generate audio for each segment
        for idx, item in enumerate(narration):
            text = item['text']
            output_file = f'audio_{idx:03d}.mp3'
            audio_files.append(output_file)
            
            # Try edge-tts first
            try:
                voice = item.get('voice', 'en-US-Standard-C')
                result = subprocess.run([
                    'edge-tts', '--voice', voice,
                    '--text', text, '--write-media', output_file
                ], capture_output=True, timeout=60)
                if result.returncode != 0:
                    raise Exception(f"edge-tts failed: {result.stderr}")
                continue
            except Exception as e:
                pass
            
            # Try gtts-cli
            try:
                result = subprocess.run([
                    'gtts-cli', text, '-o', output_file
                ], capture_output=True, timeout=60)
                if result.returncode != 0:
                    raise Exception(f"gtts failed: {result.stderr}")
                continue
            except Exception as e:
                pass
            
            # Try espeak
            try:
                result = subprocess.run([
                    'espeak', '-w', output_file.replace('.mp3', '.wav'), text
                ], capture_output=True, timeout=30)
                # Convert wav to mp3
                subprocess.run(['ffmpeg', '-y', '-i', 
                    output_file.replace('.mp3', '.wav'), 
                    output_file], capture_output=True, timeout=30)
                os.remove(output_file.replace('.mp3', '.wav'))
                continue
            except Exception as e:
                print(f"TTS failed for segment {idx}: {e}")
                # Create silence as fallback
                create_silence(output_file, 5)
    else:
        print("No TTS tool available. Creating placeholder audio with ffmpeg...")
        # Create a single silent audio file of estimated duration
        create_silence('audio_silent.wav', int(estimated_duration))
        audio_files = ['audio_silent.wav']
    
    # Concatenate all audio files
    print("Concatenating audio files...")
    if len(audio_files) == 1:
        # Just rename/copy
        if audio_files[0].endswith('.mp3'):
            subprocess.run(['ffmpeg', '-y', '-i', audio_files[0], 'audio.wav'], 
                capture_output=True, timeout=30)
        else:
            os.rename(audio_files[0], 'audio.wav')
    else:
        # Create ffmpeg concat list
        with open('concat_list.txt', 'w') as f:
            for af in audio_files:
                f.write(f"file '{af}'\n")
        
        # Concatenate using ffmpeg
        result = subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
            '-i', 'concat_list.txt', '-acodec', 'pcm_s16le', '-ar', '44100', 
            'audio.wav'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"FFmpeg concat failed: {result.stderr}")
            # Fallback: just use the first audio file
            if audio_files:
                if audio_files[0].endswith('.mp3'):
                    subprocess.run(['ffmpeg', '-y', '-i', audio_files[0], 'audio.wav'], 
                        capture_output=True, timeout=30)
                else:
                    os.rename(audio_files[0], 'audio.wav')
    
    # Cleanup temp files
    for af in audio_files:
        if os.path.exists(af):
            os.remove(af)
    if os.path.exists('concat_list.txt'):
        os.remove('concat_list.txt')
    
    print("Audio generation complete: audio.wav")
    return True

def create_silence(output_file, duration_sec):
    """Create silent audio using ffmpeg."""
    result = subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 
        f'anullsrc=r=44100:cl=mono', '-t', str(duration_sec),
        '-acodec', 'pcm_s16le', output_file
    ], capture_output=True, timeout=30)
    if result.returncode != 0:
        # If that fails, try a simpler approach
        result = subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 
            f'sine=frequency=0:duration={duration_sec}',
            '-acodec', 'pcm_s16le', output_file
        ], capture_output=True, timeout=30)

if __name__ == '__main__':
    try:
        success = generate_audio()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
