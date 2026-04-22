# ManiBench training (Gemma-4-E2B-it)

Implements the attached plan: **Stage A** static SFT, **Stage B** iterative rejection-sampling SFT + periodic DPO, **Stage C** GRPO with ManiBench composite reward.

**Full command-by-command guide (datasets, eval, train, report):** [docs/MANIBENCH_RUNBOOK.md](../../docs/MANIBENCH_RUNBOOK.md).

## Layout

| Path | Purpose |
|------|---------|
| [`manibench/eval/`](manibench/eval/) | Executability (optional `manim render`), VCER regex, alignment/coverage heuristics |
| [`manibench/gl_ce_catalog.py`](manibench/gl_ce_catalog.py) | ≥145 GL→CE + gallery seed rows |
| [`manibench/leakage.py`](manibench/leakage.py) | Pilot prompt SHA256 guards vs `data/manibench_eval_hashes.json` |
| [`scripts/`](scripts/) | Dataset builders, UV/HF Jobs training scripts, eval |

## Prerequisites

```bash
cd training/manibench
export PYTHONPATH="$(pwd)"
pip install datasets  # optional: parquet export + Hub push
pip install -e ../../.[training]   # TRL stack from repo root
```

Refresh pilot hashes after syncing real prompts from [`nabin2004/ManiBench`](https://huggingface.co/datasets/nabin2004/ManiBench):

```bash
python scripts/refresh_eval_hashes.py
# Edit manibench/data/pilot_prompts.json so full_prompt matches Hub, then rerun.
```

## Build datasets

```bash
python scripts/build_sft_core_dataset.py --out ./out/manibench-sft-core
python scripts/build_preference_dataset.py --out ./out/manibench-preference.jsonl
python scripts/synthetic_expand.py --out ./out/manibench-synthetic-sft.jsonl
python scripts/merge_sft_jsonl.py --inputs out/manibench-sft-core.jsonl out/manibench-synthetic-sft.jsonl \
  --out ./out/manibench-sft-merged.jsonl
```

Push to Hub (`HF_TOKEN` write scope):

```bash
export HF_TOKEN=...
python scripts/push_hub.py --repo-id YOURNAME/manibench-sft-core --jsonl ./out/manibench-sft-core.jsonl
```

## Evaluation (`manim` in PATH)

```bash
python -c "
from manibench.eval.harness import evaluate_sample
print(evaluate_sample(open('sample.py').read()))
"
```

Self-contained evaluator for **HF Jobs** (upload one file — no checkout):

```bash
uv run scripts/eval_uv_standalone.py --in rollouts.jsonl --out scored.jsonl --no-render
# Full executability:
uv run scripts/eval_uv_standalone.py --in rollouts.jsonl --out scored.jsonl
```

## Stage A — SFT

Use PEP 723 script (see [`SUBMIT_HF_JOBS.md`](SUBMIT_HF_JOBS.md)) or locally:

```bash
uv run scripts/train_stage_a_sft.py \
  --train-jsonl ./out/manibench-sft-merged.jsonl \
  --hub-model-id YOURNAME/manibench-gemma4-sft-stageA \
  --eval-hashes-json manibench/data/manibench_eval_hashes.json
```

## Stage B — Iterative loop + DPO every 5 loops

1. Roll + score:

```bash
export PYTHONPATH="$(pwd)"
python scripts/iterative_sft_loop.py \
  --prompts-jsonl ./out/manibench-synthetic-sft.jsonl \
  --out-buffer ./out/iter_buffer.jsonl \
  --require-exec --max-rows 1000
```

2. Train one epoch on buffer (+ optional 10% core mix):

```bash
uv run scripts/train_incremental_sft.py \
  --train-jsonl ./out/iter_buffer.jsonl \
  --mix-jsonl ./out/manibench-sft-core.jsonl \
  --hub-model-id YOURNAME/manibench-gemma4-sft-iter5 \
  --eval-hashes-json manibench/data/manibench_eval_hashes.json
```

3. **Every 5 iterations**, run DPO:

```bash
uv run scripts/train_dpo_pass.py \
  --dataset-jsonl ./out/manibench-preference.jsonl \
  --hub-model-id YOURNAME/manibench-gemma4-dpo-round2
```

Wire real rollouts via `MANIBENCH_ROLLOUT_CMD` (stdin prompt → stdout completion).

## Stage C — GRPO

```bash
export MANIBENCH_GRPO_RENDER=0   # set 1 for full manim reward (slow)
uv run scripts/train_grpo_pass.py \
  --model YOURNAME/manibench-gemma4-sft-iterFINAL \
  --prompts-jsonl ./out/train_prompts.jsonl
```

## Final report

```bash
python scripts/final_eval_report.py \
  --runs stageA=scores_stageA.jsonl stageB=scores_stageB.jsonl stageC=scores_stageC.jsonl \
  --out-md ../../manibench_ablation.md
```

## Orchestration note

HF Jobs requires **push_to_hub** + `secrets={"HF_TOKEN":"$HF_TOKEN"}`. Inline UV scripts cannot read local paths — paste script contents or host raw URLs (see `SUBMIT_HF_JOBS.md`).
