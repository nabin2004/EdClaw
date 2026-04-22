#!/usr/bin/env bash
set -euo pipefail
ollama pull gemma3:latest || true
ollama pull embeddinggemma || true
ollama pull shieldgemma:2b || true
echo "Model pulls finished (see docker/modelfiles for tool-enabled Gemma)."
