# Unsloth Studio presets (AutoManim SFT)

Checked-in YAML mirrors the defaults in [`../scripts/train_gemma4_sft.py`](../scripts/train_gemma4_sft.py).

## Quick workflow

1. **Install Studio** (one-time, separate from EdClaw venv):

   ```bash
   educlaw train studio --install
   ```

2. **Build JSONL** from episode traces:

   ```bash
   educlaw train dataset automanim
   ```

3. **Launch Studio**:

   ```bash
   educlaw train studio
   ```

   Open `http://127.0.0.1:8888`, set a password on first run.

4. In Studio:
   - **Model:** `google/gemma-4-E2B-it`, method **QLoRA** (paste `HF_TOKEN` if gated).
   - **Dataset:** upload `src/educlaw/automanim/sft_dataset.jsonl` (Local tab).
   - **Config:** Training card → **Upload** → select [`automanim-gemma4-e2b-qlora.yaml`](automanim-gemma4-e2b-qlora.yaml).
   - Verify **Train on Completions** uses `<|turn>user\n` / `<|turn>model\n`.
   - **Start Training** and monitor loss / GPU charts.

5. **Export:** Studio **Export** tab → GGUF or safetensors for Ollama / llama.cpp (see [../README.md](../README.md) §4).

## Regenerate preset

From repo root:

```bash
python training/automanim/studio/export_config.py \
  --output training/automanim/studio/automanim-gemma4-e2b-qlora.yaml
```

Or export from a training run:

```bash
uv run training/automanim/scripts/train_gemma4_sft.py \
  --train-jsonl src/educlaw/automanim/sft_dataset.jsonl \
  --export-studio-config ./my-run-config.yaml \
  --max-steps 0
```

**Note:** Unsloth Studio uses its own Python stack from the official installer. EdClaw’s `[automanim-training]` extra is for CLI / `uv run` only.
