# ManiBench training runbook

Step-by-step commands for **datasets**, **evaluation**, **fine-tuning** (Stages A/B/C), and **reporting**. All paths below are relative to the **repository root** unless noted.

### Related documentation

| Doc | Purpose |
|-----|---------|
| [DEVELOPERS.md](DEVELOPERS.md) | Dev environment, `uv`/venv, `ollama`, Docker images (`educlaw/manim:latest`), gateway |
| [training/manibench/README.md](../training/manibench/README.md) | ManiBench package overview, stages, prerequisites |
| [training/manibench/SUBMIT_HF_JOBS.md](../training/manibench/SUBMIT_HF_JOBS.md) | Hugging Face Jobs (`hf jobs`), MCP `hf_jobs()`, secrets, Trackio |
| [AGENTS.md](../AGENTS.md) | Repo stack conventions (Python 3.11+, optional `training` extras) |

### External resources

- Dataset: [`nabin2004/ManiBench`](https://huggingface.co/datasets/nabin2004/ManiBench) — sync **`full_prompt`** fields into pilot JSON before hashing (below).
- Benchmark / code: [`github.com/nabin2004/ManiBench`](https://github.com/nabin2004/ManiBench) — use the same evaluator semantics as your paper where applicable.

---

## 1. One-time setup

From repo root:

```bash
cd /path/to/EdClaw
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,training]"   # TRL, PEFT, datasets for local training scripts
```

**ManiBench Python path** (required for `import manibench`):

```bash
cd training/manibench
export PYTHONPATH="$(pwd)"
```

Optional: **`datasets` only** if you skip the full training extra:

```bash
pip install datasets
```

For **full executability** scores (subprocess render), install **Manim CE** and ensure `manim` is on `PATH`. You can instead use the Docker image from [DEVELOPERS.md](DEVELOPERS.md) (`docker build -f docker/manim.Dockerfile -t educlaw/manim:latest .`) and run eval inside that container.

---

## 2. Pilot prompts and leakage hashes

Training must **not** duplicate the twelve pilot **`full_prompt`** strings. Repository defaults live in [`training/manibench/manibench/data/pilot_prompts.json`](../training/manibench/manibench/data/pilot_prompts.json). Replace placeholders with text from Hub, then regenerate hashes:

```bash
cd training/manibench
export PYTHONPATH="$(pwd)"
python scripts/refresh_eval_hashes.py
```

This updates [`manibench/data/manibench_eval_hashes.json`](../training/manibench/manibench/data/manibench_eval_hashes.json).

Dataset builders call the leakage guard automatically unless you pass `--skip-leak-check`.

---

## 3. Building datasets (local)

Working directory: **`training/manibench`**, with `PYTHONPATH` set as above.

| What | Command | Output |
|------|---------|--------|
| SFT core (≥145 GL→CE-style + gallery) | `python scripts/build_sft_core_dataset.py --out ./out/manibench-sft-core` | `./out/manibench-sft-core.jsonl` (+ optional `datasets` folder) |
| DPO preference (~2k chosen/rejected) | `python scripts/build_preference_dataset.py --out ./out/manibench-preference.jsonl` | `./out/manibench-preference.jsonl` |
| Synthetic SFT (~5k rows, category mix, stub assistants) | `python scripts/synthetic_expand.py --out ./out/manibench-synthetic-sft.jsonl` | `./out/manibench-synthetic-sft.jsonl` |
| Teacher SFT (LiteLLM: Gemini / OpenAI / Anthropic / Ollama, …) | `python scripts/generate_sft_teacher.py --model gemini/gemini-2.5-pro --count 3000 --out ./out/manibench-sft-teacher.jsonl` | `./out/manibench-sft-teacher.jsonl` (+ optional `--rejected-out`, cache under `./out/_teacher_cache`) |
| Merge SFT sources | `python scripts/merge_sft_jsonl.py --inputs out/manibench-sft-core.jsonl out/manibench-synthetic-sft.jsonl --out ./out/manibench-sft-merged.jsonl` | `./out/manibench-sft-merged.jsonl` |

### 3.1 Teacher-model SFT distillation (strong LLM → JSONL)

Use a **teacher** model via **LiteLLM** so assistant turns are real generations instead of [`synthetic_expand.py`](../training/manibench/scripts/synthetic_expand.py) stubs. Prompts are sampled from the same five ManiBench categories as the stub builder ([`manibench/prompt_seeds.py`](../training/manibench/manibench/prompt_seeds.py)).

**Auth (examples):** set the API key your provider expects, e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENROUTER_API_KEY` (see [`.env.example`](../.env.example)).

From `training/manibench` with `PYTHONPATH` set:

```bash
# Dry-run (no API keys): stub completions, validates leakage + JSONL shape
python scripts/generate_sft_teacher.py --dry-run --count 20 --out ./out/manibench-sft-teacher-smoke.jsonl

# Gemini (example model id — pick the current Pro id supported by LiteLLM)
export GEMINI_API_KEY=...
python scripts/generate_sft_teacher.py \
  --model gemini/gemini-2.5-pro \
  --count 3000 \
  --concurrency 4 \
  --temperature 0.7 \
  --max-tokens 2048 \
  --timeout 120 \
  --cache-dir ./out/_teacher_cache \
  --resume \
  --require-exec \
  --min-composite 0.5 \
  --out ./out/manibench-sft-teacher.jsonl \
  --rejected-out ./out/manibench-sft-teacher-rejected.jsonl

# OpenAI / Anthropic (same script; change --model and env key)
export OPENAI_API_KEY=...
python scripts/generate_sft_teacher.py --model gpt-4o --count 500 --out ./out/manibench-sft-teacher-oai.jsonl

export ANTHROPIC_API_KEY=...
python scripts/generate_sft_teacher.py --model claude-sonnet-4-20250514 --count 500 --out ./out/manibench-sft-teacher-claude.jsonl
```

- **Default eval mode** is fast (no `manim` subprocess): static executability + VCER. Add **`--render-eval`** for full subprocess executability (requires `manim` on `PATH`).
- **`--resume`**: skips user prompts already present in `--out` (append mode; does not truncate an existing output file).
- **Optional `--prompts-jsonl`**: each line is a JSON object with either `messages` (first user turn used), or `user` / `prompt` plus optional `task_type`.

Merge teacher data with core (and optional stub synthetic) before Stage A:

```bash
python scripts/merge_sft_jsonl.py \
  --inputs out/manibench-sft-core.jsonl out/manibench-sft-teacher.jsonl \
  --out ./out/manibench-sft-merged.jsonl
```

Smaller smoke runs:

```bash
python scripts/build_preference_dataset.py --pairs 500 --out ./out/manibench-preference-small.jsonl
python scripts/synthetic_expand.py --count 500 --out ./out/manibench-synthetic-sft-small.jsonl
```

---

## 4. Pushing datasets to Hugging Face Hub

Requires **`HF_TOKEN`** with write access.

```bash
cd training/manibench
export HF_TOKEN=hf_...
python scripts/push_hub.py --repo-id YOUR_ORG/manibench-sft-core --jsonl ./out/manibench-sft-core.jsonl
python scripts/push_hub.py --repo-id YOUR_ORG/manibench-sft-merged --jsonl ./out/manibench-sft-merged.jsonl
```

See [training/manibench/README.md](../training/manibench/README.md) for naming alignment with your plan (`manibench-sft-core`, `manibench-preference`, `manibench-rollouts`).

---

## 5. Evaluation (no training)

### 5.1 In-repo harness (Python API)

```bash
cd training/manibench
export PYTHONPATH="$(pwd)"
python -c "
from manibench.eval.harness import evaluate_sample
print(evaluate_sample(open('path/to/scene_output.txt').read(), run_render=False))
"
```

- `run_render=False`: fast — syntax, VCER, heuristics (no `manim` subprocess).
- `run_render=True`: full **executability** — needs working `manim` and a valid `Scene` subclass in the extracted code.

### 5.2 Batch JSONL (standalone script, HF Jobs–friendly)

From `training/manibench`:

```bash
# Heuristic / static (no manim): good for CI
uv run scripts/eval_uv_standalone.py --in rollouts.jsonl --out scored.jsonl --no-render

# With subprocess render (manim required)
uv run scripts/eval_uv_standalone.py --in rollouts.jsonl --out scored.jsonl
```

Input rows can include a `completion` field, top-level assistant text, or `messages` with an assistant turn (see script help).

Details and Job deployment: [SUBMIT_HF_JOBS.md](../training/manibench/SUBMIT_HF_JOBS.md).

### 5.3 Unit tests

From repo root:

```bash
pytest tests/test_manibench_eval.py -q
```

---

## 6. Training — Stage A (static SFT)

Uses **`uv`** to resolve PEP 723 dependencies inside each script (install [uv](https://docs.astral.sh/uv/) if needed).

From `training/manibench`:

```bash
uv run scripts/train_stage_a_sft.py \
  --train-jsonl ./out/manibench-sft-merged.jsonl \
  --hub-model-id YOUR_ORG/manibench-gemma4-sft-stageA \
  --eval-hashes-json manibench/data/manibench_eval_hashes.json \
  --epochs 3
```

Or load from Hub after pushing a dataset (adjust `train_stage_a_sft.py` / use `--dataset` if you extend the script).

**Cloud GPUs:** upload the script and run via HF Jobs — see [SUBMIT_HF_JOBS.md](../training/manibench/SUBMIT_HF_JOBS.md) (`a10g-large`, `timeout`, `secrets`).

---

## 7. Training — Stage B (iterative SFT + DPO every 5 loops)

### 7.1 Roll out, score, write buffer

```bash
cd training/manibench
export PYTHONPATH="$(pwd)"

# Optional: shell command — stdin = user prompt, stdout = model completion
export MANIBENCH_ROLLOUT_CMD='your_inference_command_here'

python scripts/iterative_sft_loop.py \
  --prompts-jsonl ./out/manibench-synthetic-sft.jsonl \
  --out-buffer ./out/iter_buffer.jsonl \
  --require-exec \
  --max-rows 1000
```

Use `--no-render-eval` for faster VCER-only filtering when `manim` is unavailable.

### 7.2 One epoch on buffer (+ optional core mix)

```bash
uv run scripts/train_incremental_sft.py \
  --train-jsonl ./out/iter_buffer.jsonl \
  --mix-jsonl ./out/manibench-sft-core.jsonl \
  --hub-model-id YOUR_ORG/manibench-gemma4-sft-iterN \
  --eval-hashes-json manibench/data/manibench_eval_hashes.json
```

### 7.3 DPO pass (every 5 iterations in the paper plan)

```bash
uv run scripts/train_dpo_pass.py \
  --dataset-jsonl ./out/manibench-preference.jsonl \
  --hub-model-id YOUR_ORG/manibench-gemma4-dpo-roundK
```

### 7.4 Shell orchestration example

[`training/manibench/scripts/orchestrate_stage_b.sh`](../training/manibench/scripts/orchestrate_stage_b.sh) loops iterations and triggers DPO every fifth step (adjust paths and Hub IDs).

---

## 8. Training — Stage C (GRPO)

Composite reward matches `manibench.eval.harness.composite_reward` (executability, VCER, coverage, alignment).

```bash
cd training/manibench

# Optional: include real manim in reward (slow)
export MANIBENCH_GRPO_RENDER=1   # default 0 = heuristic-only reward in subprocess

uv run scripts/train_grpo_pass.py \
  --model YOUR_ORG/manibench-gemma4-sft-iterFINAL \
  --prompts-jsonl ./out/train_prompts.jsonl \
  --hub-model-id YOUR_ORG/manibench-gemma4-grpo
```

Use a merged or adapter Hub id for `--model` per your TRL/PEFT workflow. Larger GPU flavors (e.g. `a100-large`) are typical for GRPO — see [SUBMIT_HF_JOBS.md](../training/manibench/SUBMIT_HF_JOBS.md).

---

## 9. Ablation / final metrics table

Collect JSONL files where each line has been through the evaluator (`metrics` key from `eval_uv_standalone` or harness).

From `training/manibench`:

```bash
python scripts/final_eval_report.py \
  --runs stageA=path/to/scores_stageA.jsonl stageB=path/to/scores_stageB.jsonl \
  --out-md ../../manibench_ablation.md
```

---

## 10. Quick reference — scripts

| Script | Role |
|--------|------|
| `scripts/refresh_eval_hashes.py` | Regenerate pilot SHA256 file |
| `scripts/build_sft_core_dataset.py` | SFT core JSONL (+ optional `datasets` save) |
| `scripts/build_preference_dataset.py` | DPO JSONL |
| `scripts/synthetic_expand.py` | Synthetic SFT JSONL (stub assistants; shared prompts with teacher path) |
| `scripts/generate_sft_teacher.py` | Teacher LLM SFT JSONL (LiteLLM, cache, eval gates, `--resume`) |
| `scripts/merge_sft_jsonl.py` | Concatenate JSONL with leak check |
| `scripts/push_hub.py` | Push JSONL as Hub dataset |
| `scripts/eval_uv_standalone.py` | Batch scoring (HF Jobs) |
| `scripts/train_stage_a_sft.py` | Stage A SFT (PEP 723) |
| `scripts/train_incremental_sft.py` | Stage B incremental SFT (PEP 723) |
| `scripts/train_dpo_pass.py` | DPO (PEP 723) |
| `scripts/train_grpo_pass.py` | GRPO (PEP 723) |
| `scripts/iterative_sft_loop.py` | Rollout + filter buffer |
| `scripts/final_eval_report.py` | Markdown ablation table |
| `scripts/orchestrate_stage_b.sh` | Example multi-iter shell loop |

---

## 11. Troubleshooting

| Issue | What to check |
|-------|----------------|
| `Import manibench failed` | `cd training/manibench` and `export PYTHONPATH="$(pwd)"` |
| `ModuleNotFoundError: trl` / `datasets` | `pip install -e ".[training]"` from repo root |
| Executability always 0 with `run_render=True` | `manim` not installed, scene class not named `class X(Scene)`, or timeout (increase in harness / standalone script) |
| Hub push 401/403 | `HF_TOKEN`, repo permissions, `huggingface-cli login` |
| Leakage assert trips | Pilot `full_prompt` in training data — fix sources and refresh hashes |

For gateway, IR, Docker runner, and Ollama: [DEVELOPERS.md](DEVELOPERS.md).
