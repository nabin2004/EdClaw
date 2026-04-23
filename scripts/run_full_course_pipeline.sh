#!/usr/bin/env bash
# Run autocourse + autolecture + optional AutoManim + optional TTS.
# Usage: ./scripts/run_full_course_pipeline.sh "Your topic" --lectures 4
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" "$ROOT/scripts/run_full_course_pipeline.py" "$@"
fi
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$ROOT/scripts/run_full_course_pipeline.py" "$@"
