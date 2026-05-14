import os
import sys

# Add workspace to path
sys.path.insert(0, '/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015')

# Import manim
from manim import config, tempconfig, logger
from scene import AutoScene

# Set up config
config.media_dir = '/home/nabin2004/Desktop/EdClaw/src/educlaw/automanim/new_automanim/workspace/workspace_episode_0015/media'
config.output_file = 'AutoScene.mp4'
config.preview = False
config.quality = 'low_quality'
config.save_last_frame = False
config.format = 'mp4'

# Render
print("Starting render...")
scene = AutoScene()
scene.render()
print("Render complete!")
print(f"Output at: {config.output_file}")
