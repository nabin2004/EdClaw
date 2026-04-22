#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip install -e ".[dev]" || python3 -m pip install -e .
if command -v ollama >/dev/null 2>&1; then
  ./scripts/pull_models.sh || true
fi
if command -v docker >/dev/null 2>&1; then
  docker build -f docker/runner.Dockerfile -t educlaw/runner:latest . || true
  docker build -f docker/manim.Dockerfile -t educlaw/manim:latest . || true
fi
echo "Bootstrap complete."
