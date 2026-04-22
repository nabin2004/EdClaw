# Submitting ManiBench jobs to Hugging Face Jobs

Training runs on ephemeral GPUs — **always** pass `secrets={"HF_TOKEN":"$HF_TOKEN"}` and enable `push_to_hub`.

## Prerequisites

- HF Pro/Team (Jobs), `huggingface-cli login`
- Dataset repos created or push permissions for `nabin2004/*` namespaces you own

## Stage A — upload script then run by URL

After pushing `train_stage_a_sft.py` to a Hub model repo:

```bash
hf jobs uv run \
  --flavor a10g-large \
  --timeout 3h \
  --secrets HF_TOKEN \
  "https://huggingface.co/YOURNAME/manibench-scripts/resolve/main/train_stage_a_sft.py" \
  -- \
  --train-jsonl /dev/stdin
```

Or use the MCP tool pattern (Cursor Hugging Face plugin):

```python
hf_jobs("uv", {
    "script": open("training/manibench/scripts/train_stage_a_sft.py").read(),
    "flavor": "a10g-large",
    "timeout": "3h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"},
})
```

**Important:** MCP `hf_jobs()` cannot read local paths — pass **inline script string** or a **public raw URL**.

## Dataset hosting

Push merged JSONL first:

```bash
python scripts/push_hub.py --repo-id YOURNAME/manibench-sft-merged --jsonl ./out/manibench-sft-merged.jsonl
```

Then change `train_stage_a_sft.py` to `load_dataset("YOURNAME/manibench-sft-merged")` or pass `--dataset`.

## Evaluator-only job (CPU ok)

Upload [`scripts/eval_uv_standalone.py`](scripts/eval_uv_standalone.py) and run:

```bash
hf jobs uv run --flavor cpu-upgrade --timeout 30m --secrets HF_TOKEN \
  "https://huggingface.co/YOURNAME/manibench-scripts/resolve/main/eval_uv_standalone.py" \
  -- --in s3://...  # use Hub dataset path inside script instead for portability
```

For sandboxed Manim renders, use a Docker image with `manim` + ffmpeg preinstalled (`--image` / custom UV image).

## Trackio

Set `REPORT_TO=trackio` and configure Trackio credentials per [HF Trackio docs](https://huggingface.co/docs/trackio).

## Iterative loop scheduling

Use `hf jobs scheduled uv` with `scripts/train_incremental_sft.py` + rolled buffer uploaded as a dataset revision, **or** trigger via webhooks when `manibench-rollouts` updates.
