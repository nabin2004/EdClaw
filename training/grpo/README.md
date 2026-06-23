# GRPO Manim training (Gemma-4 dual LoRA)

Frozen SFT adapter (`nabin2004/EduClaw-Gemma4-it`) plus a trainable `manim` LoRA on `google/gemma-4-E2B-it`, with ManiBench composite rewards.

## Prerequisites

- **Python ≥ 3.11**, **NVIDIA CUDA** (Gemma-4-E2B GRPO does not run on CPU)
- **`uv`** (recommended) — script uses PEP 723 for an isolated env with **transformers ≥ 5.5** (required for Gemma 4)
- **`HF_TOKEN`** — gated base model and SFT adapter on the Hub

Do **not** rely on the repo root `.venv` alone; it pins transformers 4.x for `educlaw serve` / vLLM.

## Quick start (GPU server)

```bash
cd training/grpo
export HF_TOKEN=...   # or: huggingface-cli login

# One-step smoke test
uv run main.py --smoke

# Full training
uv run main.py --output-dir ./grpo_manim_modular
```

Windows (PowerShell):

```powershell
cd training\grpo
$env:HF_TOKEN = "..."
uv run main.py --smoke
```

## Flags

| Flag | Purpose |
|------|---------|
| `--smoke` | `max_steps=1`, `num_generations=2`, `max_completion_length=256`, batch size 1 |
| `--max-steps N` | Cap optimizer steps (overrides epochs) |
| `--output-dir` | Where to save the `manim` adapter (default `./grpo_manim_modular`) |
| `--no-render` | Keep executability reward heuristic-only (default) |

## Rewards

- **Default:** syntax + Manim `Scene` heuristics for executability (fast).
- **Full render:** `MANIBENCH_GRPO_RENDER=1 uv run main.py` — runs `manim -pql` per completion (slow).

Dataset: [nabin2004/ManiBench](https://huggingface.co/datasets/nabin2004/ManiBench) (`ManiBench_Pilot_Dataset.json`), cached on first run. Optional local copy: `ManiBench/ManiBench_Pilot_Dataset.json`.

## OOM tuning

Lower VRAM use on smaller GPUs:

```bash
uv run main.py --smoke --max-steps 5
```

Edit `make_training_args()` in `main.py` for `max_completion_length`, `num_generations`, or batch size.

See also [docs/MANIBENCH_RUNBOOK.md](../../docs/MANIBENCH_RUNBOOK.md) and [training/manibench/scripts/train_grpo_pass.py](../manibench/scripts/train_grpo_pass.py).
