# GRPO Manim training (Unsloth Gemma-4 stacked LoRA)

Loads the SFT adapter via **Unsloth** `FastVisionModel` on the Gemma-4 base, stacks a frozen `sft` LoRA plus trainable `grpo` LoRA (PEFT `add_adapter`), and trains with ManiBench composite rewards. Model loading and memory optimizations go through Unsloth; `trl.GRPOTrainer` is still used but patched by Unsloth on import.

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

# Phase 1 training (heuristic executability, 16GB-friendly)
uv run python main.py \
  --output-dir ./grpo_manim_modular_v2 \
  --num-generations 4 \
  --max-completion-length 512 \
  --reward-debug
```

Windows (PowerShell):

```powershell
cd training\grpo
uv sync --python 3.12
$env:HF_TOKEN = "..."
uv run python main.py --smoke
```

## Phased training

### Phase 1 — fast sanity (default)

Heuristic executability (`0.3` partial credit for syntax + `Scene`; full `1.0` only after real render). No `manim` subprocess.

```bash
uv run python main.py \
  --output-dir ./grpo_manim_modular_v2 \
  --num-generations 4 \
  --max-completion-length 512 \
  --reward-debug
```

**Healthy metrics within ~10 steps:**

| Metric | Target |
|--------|--------|
| `rewards/combined_reward/std` | > 0.05 (ideally 0.1+) |
| `frac_reward_zero_std` | < 0.3 |
| `completions/clipped_ratio` | < 0.5 |
| `completions/mean_terminated_length` | > 0 |
| `train_loss` | well above 1e-6 |

Reward mean may drop to 0.2–0.4 initially — that means bad outputs are being penalized.

### Phase 2 — real executability (slow)

Enable `manim` render in the reward. On 16GB, lower `num_generations` if OOM.

```bash
uv run python main.py \
  --render \
  --sft-lora ./grpo_manim_modular_v2 \
  --num-generations 2 \
  --max-completion-length 512 \
  --output-dir ./grpo_manim_modular_render
```

Or: `MANIBENCH_GRPO_RENDER=1 uv run python main.py ...`

Once `clipped_ratio` stays below ~0.3, you can experiment with `mask_truncated_completions=True` in `main.py` (currently `False` to avoid zero gradient when every completion hits max length).

## Flags

| Flag | Purpose |
|------|---------|
| `--smoke` | `max_steps=1`, caps completion length at 256 |
| `--max-steps N` | Cap optimizer steps (overrides epochs) |
| `--output-dir` | Where to save the `grpo` adapter (default `./grpo_manim_modular`) |
| `--base-model` | Override base model (default: from SFT `adapter_config.json`) |
| `--sft-lora` | Hub path or local dir for frozen SFT checkpoint (default `nabin2004/EduClaw-Gemma4-it`) |
| `--max-seq-length` | Unsloth context window (default **2048**) |
| `--max-prompt-length` | Truncate prompts for GRPO (default **1024**) |
| `--max-completion-length` | Cap generated tokens (default **512**) |
| `--num-generations` | GRPO samples per prompt (default **4**) |
| `--full-precision` | 16-bit base load (default is **4-bit** for ≤16GB GPUs) |
| `--no-render` | Heuristic executability only (default) |
| `--render` | Run `manim -pql` per completion in executability reward |
| `--grpo-only` | Train GRPO LoRA on base only (skip frozen SFT stack) |
| `--reward-debug` | Print per-step reward component stats to stderr |
| `--length-penalty` | Length penalty coefficient (default **0.001**) |

## Rewards

Hierarchical weighting: **0.50** executability, **0.25** alignment, **0.15** VCER, **0.10** coverage.

- **Phase 1 (default):** syntax + Manim `Scene` → `0.3` partial; `0.0` on failure.
- **Phase 2 (`--render`):** full `1.0` only when `manim -pql` succeeds.
- **Alignment:** no partial credit for undetectable events.
- **Length penalty:** subtracts `length_penalty × (tokens / max_completion_length)` from combined score.

Dataset: [nabin2004/ManiBench](https://huggingface.co/datasets/nabin2004/ManiBench) (`ManiBench_Pilot_Dataset.json`), cached on first run. Optional local copy: `ManiBench/ManiBench_Pilot_Dataset.json`.

### GRPO hyperparameters (defaults)

| Parameter | Value |
|-----------|-------|
| `learning_rate` | `1e-4` |
| `temperature` | `1.0` |
| `beta` (KL) | `0.001` |
| `num_generations` | `4` |
| `mask_truncated_completions` | `False` |

## OOM tuning (16GB GPUs, e.g. RTX 5060 Ti)

Defaults are tuned for ~16GB: **4-bit base**, `max_seq_length=2048`, `max_completion_length=512`, `num_generations=4`.

If you hit OOM during the GRPO log-prob step:

```bash
uv run python main.py \
  --max-seq-length 1536 \
  --max-prompt-length 768 \
  --max-completion-length 384 \
  --num-generations 2 \
  --output-dir ./grpo_manim_modular
```

For a simpler first run without stacked SFT+GRPO adapters:

```bash
uv run python main.py --grpo-only --num-generations 2 --max-completion-length 384
```

Kill other GPU processes first (`nvidia-smi`). Unsloth writes `unsloth_compiled_cache/` locally (gitignored).

For 24GB+ GPUs you can raise limits, use `--num-generations 6`, or pass `--full-precision`.

## Unit tests (no GPU)

```bash
cd training/grpo
uv run pytest test_rewards.py -v
```

## Troubleshooting

### Flat rewards (~0.48–0.51) and no learning

Check trainer logs for `completions/clipped_ratio: 1` and `frac_reward_zero_std` near 1.0. Use `--reward-debug`, keep `--max-completion-length 512`, and verify reward std > 0.05 before long runs.

### `RuntimeError: You already added LoRA adapters to your model!`

Unsloth `get_peft_model()` cannot run on a checkpoint that already has LoRA. `main.py` loads the **base model** first, attaches the frozen SFT adapter via PEFT, then adds a separate `grpo` adapter. Use `--grpo-only` to skip the SFT stack.

### Processor warning: `Kwargs passed to processor.__call__`

Harmless Unsloth/TRL + transformers 5.x warning during generation. Ensure `uv sync --python 3.12` (pins `transformers>=5.5.2`).

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

### Gemma-4 `shared-KV` / two forward passes error

If you see `cannot run two forward passes before a single backward` with gradient checkpointing, upgrade deps (needs **transformers ≥ 5.5.2**):

```bash
cd training/grpo
uv sync --python 3.12
```

### Gemma-4 GRPO log-prob shape errors

Same git upgrade as above (needs recent `unsloth-zoo` compiler fixes).

See [Unsloth RL docs](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide) and [docs/MANIBENCH_RUNBOOK.md](../../docs/MANIBENCH_RUNBOOK.md).
