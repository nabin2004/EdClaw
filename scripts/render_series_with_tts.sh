#!/usr/bin/env bash
# Manim per lecture + chunked TTS + ffmpeg mux → <series>/final/lecture-*-with-audio.mp4
# Usage: ./scripts/render_series_with_tts.sh content/ir/series/my-course --shield-model gemma4:e2b
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" "$ROOT/scripts/render_series_with_tts.py" "$@"
fi
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$ROOT/scripts/render_series_with_tts.py" "$@"
