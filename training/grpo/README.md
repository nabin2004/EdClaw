# GRPO Manim training (Unsloth Gemma-4 stacked LoRA)

Loads the SFT adapter (`nabin2004/EduClaw-Gemma4-it`) via **Unsloth** `FastVisionModel`, stacks a trainable GRPO LoRA on top, and trains with ManiBench composite rewards. Model loading and memory optimizations go through Unsloth; `trl.GRPOTrainer` is still used but patched by Unsloth on import.

## Prerequisites

- **Python 3.11 or 3.12** (not 3.13 — Unsloth/transformers 5.x are not reliable on 3.13 yet), **NVIDIA CUDA**
- **`uv`** (recommended) — script uses PEP 723 for an isolated env with **Unsloth (git)**, **transformers ≥ 5.5**, **trl ≥ 0.28**
- **`HF_TOKEN`** — gated SFT adapter on the Hub

Do **not** rely on the repo root `.venv` alone; it pins transformers 4.x for `educlaw serve` / vLLM.

If your shell shows Python 3.13, create a 3.12 venv first:

```bash
uv python install 3.12
cd training/grpo
uv run --python 3.12 main.py --smoke
```

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
uv run main.py --smoke --max-steps 5
uv run main.py --max-completion-length 512 --load-in-4bit
```

Edit `make_training_args()` in `main.py` for `num_generations` or batch size.

## Troubleshooting

### `NameError: name 'auto_docstring' is not defined`

PyPI `unsloth` is too old for **transformers 5.x** (Gemma 4). The script now pins Unsloth from git. Clear the cached env and rerun with **Python 3.12**:

```bash
rm -rf ~/.cache/uv/environments-v2/main-*
uv python install 3.12
cd training/grpo
uv run --python 3.12 main.py --smoke
```

Or upgrade manually inside the uv env:

```bash
uv pip install --upgrade --force-reinstall --no-cache-dir --no-deps \
  "unsloth @ git+https://github.com/unslothai/unsloth" \
  "unsloth-zoo @ git+https://github.com/unslothai/unsloth-zoo"
```

### Gemma-4 GRPO log-prob shape errors

Same git upgrade as above (needs recent `unsloth-zoo` compiler fixes).

See [Unsloth RL docs](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide) and [docs/MANIBENCH_RUNBOOK.md](../../docs/MANIBENCH_RUNBOOK.md).
