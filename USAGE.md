# EdClaw — Usage Guide

## Installation

```bash
pip install -e ".[dev]"
ollama pull gemma3:4b        # main LLM
ollama pull nomic-embed-text # embeddings (optional)
```

---

## `educlaw course generate` — Full Course Pipeline

Generate a complete course from a single topic: outlines → Markdown lectures → subtitle blocks (SRT/VTT) → Manim video scenes with audio.

```
educlaw course generate TOPIC [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `TOPIC` | *(required)* | What to teach, e.g. `"Introduction to Linear Algebra"` |
| `--lectures N` / `-n N` | `4` | Number of lectures (2–8) |
| `--out DIR` / `-o DIR` | `content/courses/YYYY-MM-DD-slug/` | Output directory |
| `--tts` / `--no-tts` | on | Synthesize per-block TTS audio |
| `--automanim` / `--no-automanim` | on | Generate Manim video scenes |
| `--shield` / `--no-shield` | on | Safety-check Manim code before rendering |
| `--automanim-backend` | *(settings)* | `local` or `docker` |
| `--automanim-out DIR` | `<out>/videos/` | Override video output directory |
| `--site` / `--no-site` | off | Build Jekyll site after generation |
| `--site-out DIR` | — | Parent directory for Jekyll site |
| `--continue-on-error` | on | Keep going if a lecture phase fails |

### Examples

```bash
# Minimal: 4 lectures, all features on
educlaw course generate "Introduction to Linear Algebra"

# 2 lectures, skip TTS and Manim (fast, Markdown only)
educlaw course generate "Python data structures" --lectures 2 --no-tts --no-automanim

# 6 lectures, render Manim with Docker, also build the site
educlaw course generate "Calculus basics" --lectures 6 \
    --automanim-backend docker --site

# Custom output directory
educlaw course generate "Reinforcement Learning" --lectures 4 \
    --out /tmp/rl-course
```

### Output structure

```
content/courses/2025-01-15-introduction-to-linear-algebra/
├── outline.json          # Generated topic outline
├── 01-vectors/
│   ├── lecture.md        # Generated Markdown
│   ├── subtitles.srt     # SRT subtitle file
│   ├── subtitles.vtt     # WebVTT subtitle file
│   └── audio_NN.wav      # Per-block TTS audio (if --tts)
├── 02-matrices/
│   └── ...
└── videos/               # Manim renders (if --automanim)
    ├── 01-vectors/
    └── 02-matrices/
```

---

## `educlaw dataset generate` — SFT Dataset via Teacher Models

Generate a ShareGPT-format JSONL dataset by calling a large teacher model (OpenRouter, LiteLLM, or any OpenAI-compatible API) for knowledge distillation.

```
educlaw dataset generate [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--runs N` / `-r N` | `100` | Number of topics to generate |
| `--model ID` / `-m ID` | `anthropic/claude-sonnet-4-5` | Teacher model slug |
| `--api-key KEY` | `$OPENROUTER_API_KEY` | API key |
| `--base-url URL` | `https://openrouter.ai/api/v1` | API endpoint (swap for LiteLLM) |
| `--out FILE` / `-o FILE` | `dataset/sft.jsonl` | JSONL output path |
| `--topics "A,B,C"` | *(built-in pool)* | Comma-separated topic overrides |
| `--topics-file FILE` | — | Text file with one topic per line |
| `--lectures N` / `-n N` | `3` | Lectures per topic |
| `--workers N` / `-w N` | `4` | Parallel API requests |
| `--manim` / `--no-manim` | off | Also generate Manim codegen pairs |
| `--resume` | off | Skip topics already in the output file |

### Generated pair types per lecture

| Type | Input → Output |
|---|---|
| `lecture_generation` | topic title → Markdown lecture |
| `subtitle_generation` | lecture markdown → subtitle segments JSON |
| `manim_codegen` | scene spec → Manim CE Python (if `--manim`) |

Each record is ShareGPT format:
```json
{
  "conversations": [
    {"role": "system", "value": "..."},
    {"role": "user",   "value": "..."},
    {"role": "assistant", "value": "..."}
  ],
  "source": "distill/anthropic/claude-sonnet-4-5",
  "type": "lecture_generation",
  "topic": "Linear Algebra",
  "lecture_title": "Vectors and Vector Spaces"
}
```

### Examples

```bash
# OpenRouter with default model (100 topics, built-in pool)
export OPENROUTER_API_KEY=sk-or-...
educlaw dataset generate --runs 50

# Use a specific model, more lectures, include Manim pairs
educlaw dataset generate \
    --model google/gemini-2.5-pro \
    --runs 200 \
    --lectures 5 \
    --manim \
    --out dataset/gemini-sft.jsonl

# Use a local LiteLLM proxy (free, no API key needed for ollama)
litellm --model ollama/gemma3:27b --port 4000
educlaw dataset generate \
    --base-url http://localhost:4000 \
    --model ollama/gemma3:27b \
    --api-key dummy \
    --runs 20

# Custom topics
educlaw dataset generate \
    --topics "Quantum Computing,Fourier Transforms,Bayesian Statistics" \
    --runs 30

# Topics from file (one per line)
educlaw dataset generate --topics-file my_topics.txt --runs 100

# Resume an interrupted run
educlaw dataset generate --runs 500 --resume --out dataset/sft.jsonl
```

---

---

## Manim SFT → LoRA → GRPO Pipeline

End-to-end workflow for building a Gemma4 model that generates Manim CE animation code.

```
generate_manim_dataset.py          (OpenRouter API  →  dataset/manim_sft.jsonl)
        ↓
educlaw dataset push-manim-sft     (HuggingFace Hub)
        ↓
train_gemma4_sft.py                (Unsloth LoRA SFT on GPU)
        ↓
train_grpo_pass.py                 (GRPO with ManiBench reward)
```

---

### Step 1 — Generate the Manim SFT dataset

Uses an OpenRouter model (teacher) to generate (prompt → Manim code) pairs in Gemma4 `messages` format.

```bash
export OPENROUTER_API_KEY=sk-or-...

# 100 topics, 4 scenes each = ~400 training records
python scripts/generate_manim_dataset.py --runs 100 --workers 4

# Larger run — 500 topics, 5 scenes each
python scripts/generate_manim_dataset.py \
    --runs 500 \
    --scenes-per-topic 5 \
    --workers 8 \
    --model moonshotai/kimi-k2.5 \
    --dataset-out dataset/manim_sft.jsonl

# Custom topic list
python scripts/generate_manim_dataset.py \
    --topics "Eigenvalues,Fourier Transform,Gradient Descent" \
    --runs 30 \
    --scenes-per-topic 4
```

| Flag | Default | Description |
|---|---|---|
| `--runs N` | `100` | Topics to process |
| `--scenes-per-topic N` | `4` | Manim scenes generated per topic |
| `--workers N` | `4` | Concurrent API requests |
| `--model ID` | `moonshotai/kimi-k2.5` | Teacher model (or `$OPENROUTER_MODEL`) |
| `--dataset-out FILE` | `dataset/manim_sft.jsonl` | Output JSONL path |

Each output record:
```json
{
  "messages": [
    {"role": "system",    "content": "You write Manim Community Edition..."},
    {"role": "user",      "content": "Write a Manim scene titled 'EigenvalueScene'..."},
    {"role": "assistant", "content": "from manim import *\n\nclass EigenvalueScene(Scene):..."}
  ],
  "topic": "Eigenvalues and Eigenvectors",
  "scene_title": "EigenvalueScene",
  "source": "manim_sft/moonshotai/kimi-k2.5"
}
```

The `messages` format is directly compatible with Gemma4's chat template — no conversion needed.

---

### Step 2 — Push to HuggingFace Hub

```bash
export HF_TOKEN=hf_...

# Push with default path (dataset/manim_sft.jsonl)
educlaw dataset push-manim-sft nabin2004/educlaw-manim-sft

# Public dataset with 5% eval split
educlaw dataset push-manim-sft nabin2004/educlaw-manim-sft \
    --public \
    --test-size 0.05

# Custom JSONL path
educlaw dataset push-manim-sft nabin2004/educlaw-manim-sft \
    --jsonl dataset/manim_sft.jsonl \
    --token hf_...
```

On success, prints a stats summary:

```
Dataset pushed (private): https://huggingface.co/datasets/nabin2004/educlaw-manim-sft
  Records   : 400 training examples
  Topics    : 68 unique
  Avg code  : 2341 chars/scene
  Skipped   : 0 malformed lines
```

The command validates every record has the correct `role`/`content` structure before uploading.

---

### Step 3 — SFT with Unsloth LoRA (requires CUDA)

Install training dependencies:

```bash
pip install -e ".[automanim-training]"
# or: pip install unsloth trl>=0.12 peft accelerate datasets
```

Run SFT (the script expects the dataset already on disk; download from Hub or use local):

```bash
python training/automanim/scripts/train_gemma4_sft.py \
    --train-jsonl dataset/manim_sft.jsonl \
    --model-name google/gemma-4-E2B-it \
    --epochs 3 \
    --batch-size 1 \
    --gradient-accumulation 4 \
    --output-dir out/manim-gemma4-lora
```

To also push the LoRA adapters to the Hub when done:

```bash
python training/automanim/scripts/train_gemma4_sft.py \
    --train-jsonl dataset/manim_sft.jsonl \
    --hub-model-id nabin2004/manim-gemma4-e2b-lora \
    --epochs 3
```

Smoke test (10 steps only, for checking the pipeline works):

```bash
python training/automanim/scripts/train_gemma4_sft.py \
    --train-jsonl dataset/manim_sft.jsonl \
    --max-steps 10 \
    --output-dir out/smoke-test
```

Via the CLI shortcut:

```bash
educlaw train sft automanim \
    --train-jsonl dataset/manim_sft.jsonl \
    --output-dir out/manim-gemma4-lora
```

**LoRA configuration used:**

| Parameter | Value |
|---|---|
| Base model | `google/gemma-4-E2B-it` |
| LoRA rank `r` | 8 |
| LoRA alpha | 8 |
| Target modules | attention + MLP |
| 4-bit quantization | yes (QLoRA via Unsloth) |
| Loss masking | responses only (`<\|turn>model\n` tokens) |
| Optimizer | `adamw_8bit` |
| LR | `2e-4` |

The trainer uses `train_on_responses_only` with `instruction_part="<|turn>user\n"` and `response_part="<|turn>model\n"`, so **only the Manim code tokens** contribute to the loss — not the system prompt or user request.

> **Dataset format note:** `train_gemma4_sft.py` expects rows with a `"text"` field (pre-formatted).
> To use `manim_sft.jsonl` directly, preprocess it first:
> ```python
> from transformers import AutoTokenizer
> from datasets import load_dataset
> import json
>
> tok = AutoTokenizer.from_pretrained("google/gemma-4-E2B-it")
> ds = load_dataset("json", data_files="dataset/manim_sft.jsonl", split="train")
> with open("dataset/manim_sft_text.jsonl", "w") as f:
>     for row in ds:
>         text = tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False)
>         f.write(json.dumps({"text": text}) + "\n")
> ```
> Then pass `--train-jsonl dataset/manim_sft_text.jsonl`.

---

### Step 4 — GRPO with ManiBench reward (requires CUDA)

GRPO refines the SFT adapter using a reward signal that measures actual Manim code quality — no human labels needed.

Install:
```bash
pip install trl>=0.12 peft>=0.13 datasets transformers accelerate
```

Run GRPO (start from the SFT adapter or the base model):

```bash
# From base model (or replace with your SFT Hub id)
python training/manibench/scripts/train_grpo_pass.py \
    --model google/gemma-4-E2B-it \
    --prompts-jsonl dataset/manim_sft.jsonl \
    --output-dir out/manim-gemma4-grpo \
    --hub-model-id nabin2004/manim-gemma4-e2b-grpo

# From your SFT adapter
python training/manibench/scripts/train_grpo_pass.py \
    --model nabin2004/manim-gemma4-e2b-lora \
    --prompts-jsonl dataset/manim_sft.jsonl \
    --hub-model-id nabin2004/manim-gemma4-e2b-grpo

# Save locally only (no Hub push)
python training/manibench/scripts/train_grpo_pass.py \
    --model google/gemma-4-E2B-it \
    --prompts-jsonl dataset/manim_sft.jsonl \
    --no-push \
    --output-dir out/grpo-local

# Enable live Manim rendering inside the reward (slow but accurate)
MANIBENCH_GRPO_RENDER=1 python training/manibench/scripts/train_grpo_pass.py \
    --model google/gemma-4-E2B-it \
    --prompts-jsonl dataset/manim_sft.jsonl \
    --hub-model-id nabin2004/manim-gemma4-e2b-grpo

# Reduce VRAM usage
python training/manibench/scripts/train_grpo_pass.py \
    --model google/gemma-4-E2B-it \
    --prompts-jsonl dataset/manim_sft.jsonl \
    --per-device-train-batch-size 1 \
    --max-length 4096 \
    --hub-model-id nabin2004/manim-gemma4-e2b-grpo
```

**How the GRPO reward works:**

The `manim_sft.jsonl` `messages` format is read natively by the GRPO script — it extracts the `user` turn as the prompt, generates completions, then scores them with `composite_reward`:

```
Reward = 0.4 × Exec  +  0.3 × (1 − VCER)  +  0.2 × Coverage  +  0.1 × Alignment
```

| Component | Weight | What it measures |
|---|---|---|
| **Exec** | 0.40 | Code renders without error (`manim render -ql`) |
| **VCER** | 0.30 | Absence of ManimGL-only APIs (e.g. `ShowCreation`, `CONFIG`, `TexMobject`) |
| **Coverage** | 0.20 | Visual richness: math objects, colors, arrows, axes present |
| **Alignment** | 0.10 | Fraction of expected animation events found (`play(`, `wait(`, `Create(`, …) |

By default (`MANIBENCH_GRPO_RENDER=0`) the Exec score is computed statically (no subprocess render), making VCER the dominant signal. Set `MANIBENCH_GRPO_RENDER=1` to enable live rendering — slower but gives accurate executability scores.

**LoRA config used in GRPO:**

| Parameter | Value |
|---|---|
| LoRA rank `r` | 16 |
| LoRA alpha | 32 |
| Target modules | `all-linear` |
| Gradient accumulation | 32 |
| Max completion length | 8192 tokens |
| Precision | `bf16` |

---

### Step 5 — Evaluate with ManiBench

Run the full evaluation suite against the 12-problem ManiBench benchmark:

```bash
export OPENROUTER_API_KEY=sk-or-...

# Evaluate your fine-tuned model via inference.net
python -m training.grpo.ManiBench.evaluation \
    --provider inference \
    --model nabin2004/manim-gemma4-e2b-grpo

# Zero-shot baseline comparison (OpenRouter models)
python -m training.grpo.ManiBench.evaluation \
    --provider openrouter \
    --model claude-sonnet-4
```

---

### Quick-start one-liner (full pipeline)

```bash
# 1. Generate
export OPENROUTER_API_KEY=sk-or-...
python scripts/generate_manim_dataset.py --runs 200 --workers 4

# 2. Push
export HF_TOKEN=hf_...
educlaw dataset push-manim-sft nabin2004/educlaw-manim-sft

# 3. Convert messages→text (for SFT script)
python -c "
from transformers import AutoTokenizer
from datasets import load_dataset
import json
tok = AutoTokenizer.from_pretrained('google/gemma-4-E2B-it')
ds = load_dataset('json', data_files='dataset/manim_sft.jsonl', split='train')
with open('dataset/manim_sft_text.jsonl', 'w') as f:
    for row in ds:
        text = tok.apply_chat_template(row['messages'], tokenize=False, add_generation_prompt=False)
        f.write(json.dumps({'text': text}) + '\n')
"

# 4. SFT
python training/automanim/scripts/train_gemma4_sft.py \
    --train-jsonl dataset/manim_sft_text.jsonl \
    --epochs 3 \
    --hub-model-id nabin2004/manim-gemma4-e2b-lora

# 5. GRPO
python training/manibench/scripts/train_grpo_pass.py \
    --model nabin2004/manim-gemma4-e2b-lora \
    --prompts-jsonl dataset/manim_sft.jsonl \
    --hub-model-id nabin2004/manim-gemma4-e2b-grpo
```

---

## Other useful commands

```bash
educlaw autocourse generate "Topic" --lectures 4   # older subcommand (same pipeline)
educlaw pull-models                                # pull all default Ollama models
educlaw automanim plan lecture.md                  # plan Manim scenes for one lecture
educlaw automanim render scene_spec.json           # render one scene
```

---

## Environment variables

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | API key for OpenRouter (dataset generate) |
| `LITELLM_API_KEY` | Alternative key for LiteLLM proxy |
| `OLLAMA_BASE_URL` | Ollama endpoint (default: `http://localhost:11434`) |
| `EDUCLAW_SETTINGS` | Path to custom settings TOML file |
