#!/usr/bin/env bash
set -euo pipefail
ollama pull gemma3:latest || true
ollama pull embeddinggemma || true
# Shield uses model_id from profile (no separate shieldgemma pull by default).
echo "Model pulls finished (see docker/modelfiles for tool-enabled Gemma)."
