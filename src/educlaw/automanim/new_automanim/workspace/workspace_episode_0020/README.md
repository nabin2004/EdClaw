# Mini-Batch Gradient Noise Visualization

This animation visualizes how different mini-batch sizes affect optimization paths on a loss surface.

## Files
- `scene.py` - Manim animation code
- `narration.json` - Narration segments with timing
- `run.sh` - Script to automate the full pipeline
- `generate_audio.py` - Python script to generate TTS audio (requires edge-tts)

## Requirements

```bash
pip install manim edge-tts ffmpeg-python
```

## Steps to Generate Final Video

### Method 1: Using the run.sh script

```bash
chmod +x run.sh
./run.sh
```

### Method 2: Step by Step

1. **Render Manim video:**
```bash
manim -pql scene.py AutoScene
```

2. **Generate audio with edge-tts:**
```bash
edge-tts --text "In this visualization, we explore how mini-batch size affects optimization on a loss surface. The surface shows a typical optimization landscape with local variations. With batch size one, the gradient estimate has high variance, causing a noisy, zigzag path toward the minimum. With batch size thirty two, the gradient is more stable, resulting in a smoother optimization path. With the full dataset, the gradient is exact, producing the smoothest descent path. Note that smaller batches add noise, but this can actually help escape local minima and saddle points." --voice en-US-AriaNeural --rate +0% -o audio.wav
```

3. **Copy video:**
```bash
cp media/videos/scene/480p15/AutoScene.mp4 video.mp4
```

4. **Merge video and audio:**
```bash
ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -shortest final.mp4
```

## Output
- `final.mp4` - The final merged video with narration

## Preview

The animation shows:
- A 3D loss surface with bowl shape and local variations
- Three optimization paths starting from the same point
- Red: Batch size 1 (noisy, high variance path)
- Green: Batch size 32 (moderate variance)
- Gold: Full batch (smooth, direct path)
