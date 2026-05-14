import sys
import soundfile as sf
from kittentts import KittenTTS

text = sys.argv[1]
output_path = sys.argv[2]
voice = sys.argv[3]
speed = float(sys.argv[4])

model = KittenTTS("KittenML/kitten-tts-mini-0.8")

audio = model.generate(
    text,
    voice=voice,
    speed=speed
)

sf.write(output_path, audio, 24000)

print("done")