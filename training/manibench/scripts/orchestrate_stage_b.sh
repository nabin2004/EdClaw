#!/usr/bin/env bash
# Example: Stage B outer loop — run iterative_sft_loop + incremental SFT;
# every 5th iteration, call train_dpo_pass.py (submit as separate HF Jobs).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT"

PROMPTS="${1:?prompts jsonl}"
MAX_ITERS="${2:-12}"

for ((i=1; i<=MAX_ITERS; i++)); do
  echo "=== Iteration $i ==="
  python "$ROOT/scripts/iterative_sft_loop.py" \
    --prompts-jsonl "$PROMPTS" \
    --out-buffer "$ROOT/out/iter_buffer_$i.jsonl" \
    --require-exec --max-rows 1000 || true

  EXTRA_ARGS=()
  if [[ -f "$ROOT/manibench/data/manibench_eval_hashes.json" ]]; then
    EXTRA_ARGS+=(--eval-hashes-json "$ROOT/manibench/data/manibench_eval_hashes.json")
  fi
  uv run "$ROOT/scripts/train_incremental_sft.py" \
    --train-jsonl "$ROOT/out/iter_buffer_$i.jsonl" \
    --mix-jsonl "$ROOT/out/manibench-sft-core.jsonl" \
    --hub-model-id "${MANIBENCH_HUB_ITER:-nabin2004/manibench-gemma4-sft-iter$i}" \
    "${EXTRA_ARGS[@]}"

  if (( i % 5 == 0 )); then
    uv run "$ROOT/scripts/train_dpo_pass.py" \
      --dataset-jsonl "$ROOT/out/manibench-preference.jsonl" \
      --hub-model-id "${MANIBENCH_HUB_DPO:-nabin2004/manibench-gemma4-dpo}-iter$i"
  fi
done
