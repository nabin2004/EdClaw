# AutoManim Gemma-4 E2B SFT pipeline

Rebuild **teacher traces** (`metadata.json` per episode) into Gemma-style **training text**, then LoRA‑fine‑tune `google/gemma-4-E2B-it` with **Unsloth** on a single **local CUDA** GPU.

**Layout**

| Path | Role |
|------|------|
| [`automanim_sft/template.py`](automanim_sft/template.py) | Jinja template + `render_episode()` |
| [`automanim_sft/build_dataset.py`](automanim_sft/build_dataset.py) | JSONL emission + stats |
| [`scripts/build_sft_jsonl.py`](scripts/build_sft_jsonl.py) | Dataset → `sft_dataset.jsonl` |
| [`scripts/train_gemma4_sft.py`](scripts/train_gemma4_sft.py) | Unsloth `FastModel` + TRL `SFTTrainer` |
| [`scripts/smoke_infer.py`](scripts/smoke_infer.py) | One generation from a saved LoRA folder |
| [`studio/automanim-gemma4-e2b-qlora.yaml`](studio/automanim-gemma4-e2b-qlora.yaml) | Unsloth Studio preset (matches CLI defaults) |
| [`studio/export_config.py`](studio/export_config.py) | Regenerate Studio YAML from CLI parameters |

Upstream episode data lives at [`src/educlaw/automanim/dataset/`](../../src/educlaw/automanim/dataset). The canonical JSONL lives next door as [`sft_dataset.jsonl`](../../src/educlaw/automanim/sft_dataset.jsonl). You can also run `python ../../src/educlaw/automanim/convert2template.py` from that directory (delegates here).

---

## Prerequisites

- **Python ≥ 3.11**, NVIDIA driver + CUDA, enough VRAM for 4‑bit Gemma‑4‑E2B + LoRA.
- Optional gated base model access: **`HF_TOKEN`** accepted by Transformers Hub.
- From repo root, optional editable install matching your environment:

```bash
pip install -e ".[automanim-training]"
```

Most users rely on PEP 723 and run **`uv run`** on each script instead, or the **`educlaw train`** CLI (see below).

---

## Quick start (`educlaw train`)

| Command | Purpose |
|---------|---------|
| `educlaw train dataset automanim` | Build `sft_dataset.jsonl` from bundled episodes |
| `educlaw train sft automanim` | CLI training via Unsloth Core (CUDA) |
| `educlaw train studio --install` | One-time Unsloth Studio installer |
| `educlaw train studio` | Launch local no-code training UI |

---

## 1. Build JSONL

By default **`--require-generated-code`** skips episodes whose `generated_code` is empty (**33** rows vs **50** total in the bundled dataset).

From **repo root**:

```bash
educlaw train dataset automanim
```

Or with `uv run` directly:

```bash
uv run training/automanim/scripts/build_sft_jsonl.py \
  --dataset-dir src/educlaw/automanim/dataset \
  --output src/educlaw/automanim/sft_dataset.jsonl
```

Useful flags:

- `--episode-id episode_0002` (repeatable) — smoke one episode.
- `--no-require-generated-code` — include failure-only traces.
- `--exclude-failures-without-code` — when not requiring code, drop `status=failure` rows with no code.

Rendered examples are large (long tool logs + scene code): expect aggressive **truncation** at **`--max-seq-length`** during training unless you raise context or shorten traces.

---

## 2. Train (local CUDA)

```bash
educlaw train sft automanim
```

Smoke (~10 optimizer steps):

```bash
educlaw train sft automanim --max-steps 10
```

Or with `uv run` directly — smoke (~10 optimizer steps):

```bash
uv run training/automanim/scripts/train_gemma4_sft.py \
  --train-jsonl src/educlaw/automanim/sft_dataset.jsonl \
  --max-steps 10 \
  --eval-split 0 \
  --output-dir ./out/automanim-gemma4-e2b-smoke
```

Multi‑epoch defaults (`--epochs 5`, **`--eval-split 0.1`**, **`--max-seq-length 8192`**):

```bash
uv run training/automanim/scripts/train_gemma4_sft.py \
  --train-jsonl src/educlaw/automanim/sft_dataset.jsonl \
  --epochs 5 \
  --output-dir ./out/automanim-gemma4-e2b-lora
```

Flags:

| Flag | Meaning |
|------|---------|
| `--eval-split 0` | No held‑out mini split (recommended for smallest runs). |
| `--lr` | Overrides learning rate (`AUTOMANIM_SFT_LR` env fallback). |
| `--report-to wandb` | Needs `wandb login` / `WANDB_API_KEY`. |
| `--hub-model-id org/name` | Pushes adapters after training (**requires `HF_TOKEN`**).
| `--export-studio-config PATH` | Write matching Unsloth Studio YAML (no training).

**OOM tweaks:** `--max-seq-length 4096`, `--batch-size 1`, `--gradient-accumulation 8`.

Training uses **labels only inside `<|turn>model`** spans (`train_on_responses_only` with `instruction_part='<|turn>user\n'` and `response_part='<|turn>model\n'`), aligned with Gemma‑4 turn markers produced by our Jinja.

---

## 2b. Train with Unsloth Studio (no-code UI)

Unsloth **Studio** is a browser-based UI (separate install from EdClaw’s venv). It uses the same model and hyperparameters as the CLI preset in [`studio/automanim-gemma4-e2b-qlora.yaml`](studio/automanim-gemma4-e2b-qlora.yaml).

| | CLI (`educlaw train sft`) | Studio (`educlaw train studio`) |
|--|---------------------------|----------------------------------|
| Install | `pip install -e ".[automanim-training]"` or `uv run` | `educlaw train studio --install` |
| Dataset | `--train-jsonl` path | Upload JSONL in Studio Dataset tab |
| Config | CLI flags | Import preset YAML in Training card |
| Monitoring | wandb / tensorboard optional | Built-in loss charts + GPU stats |
| Export | `trainer.save_model` | Studio Export tab → GGUF / safetensors |

Workflow:

```bash
educlaw train studio --install    # once
educlaw train dataset automanim
educlaw train studio              # opens http://127.0.0.1:8888
```

In Studio: upload `src/educlaw/automanim/sft_dataset.jsonl`, import [`studio/automanim-gemma4-e2b-qlora.yaml`](studio/automanim-gemma4-e2b-qlora.yaml), verify **Train on Completions** markers, then **Start Training**. See [`studio/README.md`](studio/README.md) for details.

**Note:** Studio ships its own Python stack; EdClaw’s `[automanim-training]` extra is for CLI paths only.

---

## 3. Inference smoke test

After a successful run:

```bash
uv run training/automanim/scripts/smoke_infer.py \
  --adapter-dir ./out/automanim-gemma4-e2b-lora \
  --prompt "Animate SGD descending a loss surface."
```

Inference applies Unsloth’s **`get_chat_template(..., chat_template='gemma-4')`**; **training stays on raw pre‑rendered `text`.**

---

## 4. Optional GGUF

Unsloth can export quantized GGUF (see upstream Unsloth docs). This repo pipeline stops at **`trainer.save_model` + tokenizer**; extend locally if you need `llama.cpp` / Ollama artifacts.

---

## Caveats

- **Small dataset (~33 usable rows)** — expect **overfitting**; treat outputs as stylistic imitation of the bundled teacher traces.
- **Security:** Never commit **`HF_TOKEN`**, **`WANDB_API_KEY`**, or long‑lived tokens into notebooks — use **`huggingface_hub login`** / environment variables (`notebook/gemma4sft.ipynb` should read tokens from env only).
