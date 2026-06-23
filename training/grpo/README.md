# GRPO Manim training (Unsloth Gemma-4 stacked LoRA)

Loads the SFT adapter (`nabin2004/EduClaw-Gemma4-it`) via **Unsloth** `FastVisionModel`, stacks a trainable GRPO LoRA on top, and trains with ManiBench composite rewards. Model loading and memory optimizations go through Unsloth; `trl.GRPOTrainer` is still used but patched by Unsloth on import.

## Prerequisites

- **Python 3.11 or 3.12** (not 3.13 — Unsloth/transformers 5.x are not reliable on 3.13 yet), **NVIDIA CUDA**
- **`uv`** (recommended) — `training/grpo/pyproject.toml` pins **Unsloth (git)**, **transformers 5.5**, **trl ≥ 0.28** (overrides unsloth-zoo’s trl≤0.24 pin)
- **`HF_TOKEN`** — gated SFT adapter on the Hub

Do **not** rely on the repo root `.venv` alone; it pins transformers 4.x for `educlaw serve` / vLLM.

If your shell shows Python 3.13, create a 3.12 venv first:

```bash
uv python install 3.12
cd training/grpo
uv sync --python 3.12
uv run --python 3.12 python main.py --smoke
```

## Quick start (GPU server)

```bash
cd training/grpo
export HF_TOKEN=...   # or: huggingface-cli login

# First time (or after dep changes)
uv sync --python 3.12

# One-step smoke test
uv run python main.py --smoke

# Full training
uv run python main.py --output-dir ./grpo_manim_modular
```

Windows (PowerShell):

```powershell
cd training\grpo
uv sync --python 3.12
$env:HF_TOKEN = "..."
uv run python main.py --smoke
```

## Flags

| Flag | Purpose |
|------|---------|
| `--smoke` | `max_steps=1`, `num_generations=2`, caps completion length at 256 |
| `--max-steps N` | Cap optimizer steps (overrides epochs) |
| `--output-dir` | Where to save the GRPO LoRA (default `./grpo_manim_modular`) |
| `--sft-lora` | Hub path or local dir for frozen SFT checkpoint (default `nabin2004/EduClaw-Gemma4-it`) |
| `--max-seq-length` | Unsloth context window (default 4096) |
| `--max-completion-length` | Cap generated tokens (default: `max_seq_length` − longest prompt) |
| `--load-in-4bit` | 4-bit load for OOM / 4-bit SFT checkpoints |
| `--no-render` | Keep executability reward heuristic-only (default) |

## Rewards

- **Default:** syntax + Manim `Scene` heuristics for executability (fast).
- **Full render:** `MANIBENCH_GRPO_RENDER=1 uv run main.py` — runs `manim -pql` per completion (slow).

Dataset: [nabin2004/ManiBench](https://huggingface.co/datasets/nabin2004/ManiBench) (`ManiBench_Pilot_Dataset.json`), cached on first run. Optional local copy: `ManiBench/ManiBench_Pilot_Dataset.json`.

## OOM tuning

Lower VRAM use on smaller GPUs:

```bash
uv run python main.py --smoke --max-steps 5
uv run python main.py --max-completion-length 512 --load-in-4bit
```

Edit `make_training_args()` in `main.py` for `num_generations` or batch size.

## Troubleshooting

### `trl` / `unsloth-zoo` dependency conflict

`unsloth-zoo` declares `trl<=0.24` but Gemma 4 GRPO needs `trl>=0.28`. [pyproject.toml](pyproject.toml) uses `[tool.uv] override-dependencies` (same idea as the Unsloth notebook’s `pip install --no-deps`). Run from `training/grpo`:

```bash
cd training/grpo
uv sync --python 3.12
uv run python main.py --smoke
```

### `NameError: name 'auto_docstring' is not defined`

PyPI `unsloth` is too old for **transformers 5.x** (Gemma 4). Use git pins via `uv sync` above (clears stale script envs):

```bash
rm -rf ~/.cache/uv/environments-v2/main-*
cd training/grpo
uv sync --python 3.12
uv run --python 3.12 python main.py --smoke
```

### Gemma-4 GRPO log-prob shape errors

Same git upgrade as above (needs recent `unsloth-zoo` compiler fixes).

See [Unsloth RL docs](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide) and [docs/MANIBENCH_RUNBOOK.md](../../docs/MANIBENCH_RUNBOOK.md).
