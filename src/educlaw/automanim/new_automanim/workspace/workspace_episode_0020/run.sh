#!/bin/bash
# Script to render and produce final video

echo "Step 1: Rendering Manim scene..."
manim -pql scene.py AutoScene

echo "Step 2: Video is at media/videos/scene/480p15/AutoScene.mp4"
echo "Copying to video.mp4"
cp media/videos/scene/480p15/AutoScene.mp4 video.mp4

echo "Step 3: Generating TTS audio (requires azure or edge-tts)..."
echo "Install edge-tts: pip install edge-tts"
echo "Or use: pip install azure-cognitiveservices-speech"

# Option using edge-tts (recommended, free)
# edge-tts --text "In this visualization, we explore how mini-batch size affects optimization on a loss surface. The surface shows a typical optimization landscape with local variations. With batch size one, the gradient estimate has high variance, causing a noisy, zigzag path toward the minimum. With batch size thirty two, the gradient is more stable, resulting in a smoother optimization path. With the full dataset, the gradient is exact, producing the smoothest descent path. Note that smaller batches add noise, but this can actually help escape local minima and saddle points." --voice en-US-AriaNeural --rate medium -o audio.wav

echo "Step 4: Merging video and audio..."
ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -shortest final.mp4

echo "Done! final.mp4 created."
