# Running EdClaw

## Prerequisites

- Python 3.11+ with the project installed (`uv sync` or `pip install -e .`)
- [Ollama](https://ollama.com) running locally (`ollama serve`)
- The model configured in `profiles/local.toml` pulled: `educlaw pull-models`

## Quick health check

```bash
educlaw doctor
```

---

## autocourse — full course pipeline

**Plan only** (preview outline, no files written):
```bash
educlaw autocourse plan --prompt "Introduction to linear algebra" --lectures 4
educlaw autocourse plan -p "Python basics" -n 2 --out plan.json   # also saves JSON
```

**Generate full course** (lectures + optional TTS + optional Manim videos):
```bash
# Minimal: markdown only, no TTS, no animations
educlaw autocourse generate -p "Machine learning fundamentals" --no-tts --no-automanim

# Full pipeline (reads TTS/automanim settings from profiles/local.toml)
educlaw autocourse generate -p "Calculus for beginners" -n 4

# Custom output directory, continue past individual failures
educlaw autocourse generate -p "Data structures" --out content/ir/series/my-run \
  --lectures 6 --continue-on-error

# Skip safety shield, override automanim backend
educlaw autocourse generate -p "Topic" --no-shield --automanim-backend local
```

Output lands in `content/ir/series/YYYY-MM-DD-<slug>/` by default:
```
lecture-01-<slug>.md
lecture-02-<slug>.md
audio/lecture-01.wav          (if TTS on)
videos/<scene>/scene.mp4      (if automanim on)
course-plan.json
pipeline-manifest.json
```

The script `scripts/run_full_course_pipeline.py` runs the **exact same pipeline**:
```bash
python scripts/run_full_course_pipeline.py "Topic" --lectures 4 --no-tts --no-automanim
```

---

## autolecture — single lecture

**Plan outline** (LLM generates title, objectives, key topics — no markdown written):
```bash
educlaw autolecture plan --prompt "Gradient descent"
educlaw autolecture plan -p "Bayes theorem" --out outline.json
```

**Generate lecture markdown**:
```bash
educlaw autolecture generate --prompt "Attention mechanism in transformers"
educlaw autolecture generate -p "Binary search trees" --out lecture-bst.md
```

---

## automanim — Manim scene generation

**Plan scenes** (shows what scenes would be generated, no rendering):
```bash
# From a lecture file
educlaw automanim plan content/ir/series/my-run/lecture-01-*.md
educlaw automanim plan lecture.md --out scenes.json

# From inline text
educlaw automanim plan --prompt "A lecture on vector addition..."
```

**Render a single lecture**:
```bash
educlaw automanim render lecture-01-gradient-descent.md
educlaw automanim render lecture.md --out-dir videos/ --no-shield
```

**Render all lectures in a series**:
```bash
educlaw automanim run content/ir/series/2026-06-20-my-course/
```

---

## TTS

```bash
educlaw tts status                          # check backend
educlaw tts list                            # list registered backends + voices
educlaw tts say "Hello, world" --out hi.wav
educlaw tts speak --text "Hello"            # interactive
```

---

## Other commands

```bash
educlaw serve                               # start FastAPI gateway
educlaw ir lint                             # validate IR graph
educlaw ir index                            # build vector index
educlaw site generate <series-dir>          # generate Jekyll course site
educlaw pull-models                         # pull all configured Ollama models
```

---

## Profile configuration

Edit `profiles/local.toml` to change:
- `model_id` — Ollama chat model
- `tts_enabled`, `tts_backend`, `tts_voice`
- `automanim_enabled`, `automanim_backend` (`"local"` or `"docker"`)
- `shield_enabled`

Override the profile path: `EDUCLAW_PROFILE_PATH=/path/to/profile.toml educlaw ...`
