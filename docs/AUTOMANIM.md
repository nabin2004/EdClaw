# AutoManim

**AutoManim** turns lecture Markdown (plus IR-shaped YAML frontmatter) into **Manim Community Edition** scenes and **MP4** artifacts. It is built from **Google ADK** `LlmAgent` instances (planner + codegen) plus a deterministic **render** step (local `manim` subprocess or **Docker** one-shot). A **static critic** loop rewrites bad codegen before render; an optional **LLM critic** adds a second Ollama pass.

## Package layout (`src/educlaw/automanim/`)

| Area | Path | Role |
|------|------|------|
| **Production render** | [`adk/`](../../src/educlaw/automanim/adk/) | Ollama ADK planner/codegen/critic + `run_automanim` (CLI, gateway WS, autocourse) |
| **Dataset factory** | [`src/`](../../src/educlaw/automanim/src/) (TypeScript) | pi-coding-agent episode generator (`npm run generate`) |
| **Training data** | [`dataset/`](../../src/educlaw/automanim/dataset/), [`sft_dataset.jsonl`](../../src/educlaw/automanim/sft_dataset.jsonl) | Bundled teacher traces; build JSONL with `educlaw train dataset automanim` |

Run TypeScript tools from `src/educlaw/automanim/` (**Node.js 20+** required — `pi-coding-agent` does not run on Node 18; use `nvm use` with [`.nvmrc`](../../src/educlaw/automanim/.nvmrc) or install Node 22). Then `npm install`, `npm run dev` or `npm run generate`. See [training/automanim/README.md](../training/automanim/README.md) for SFT.

### Dataset factory audio (Kitten TTS)

Episodes produced by `npm run generate` get **deterministic narration** after the coding agent finishes: the pipeline reads `narration.json`, synthesizes each segment with **Kitten TTS**, concatenates to `audio.wav`, writes `subtitles.srt`, and merges into `final.mp4` when a Manim video exists.

**Prerequisites** (repo venv):

```bash
pip install 'educlaw[tts-kitten]'
# Warm the model once (downloads ~25–80 MB); see docs/TTS.md
python -c "from kittentts import KittenTTS; KittenTTS('KittenML/kitten-tts-nano-0.8-int8', cache_dir=str(__import__('pathlib').Path.home()/'.educlaw/tts'))"
```

Optional env vars when running from `src/educlaw/automanim/`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `AUTOMANIM_TTS_MODEL_ID` | `KittenML/kitten-tts-nano-0.8-int8` | Hugging Face Kitten model id |
| `AUTOMANIM_TTS_VOICE` | `Jasper` | Default voice when narration uses `"default"` |
| `AUTOMANIM_TTS_CACHE_DIR` | `~/.educlaw/tts` | Model cache directory |
| `AUTOMANIM_PYTHON` | `python3` | Python executable for `kitten_runner.py` |

The agent must **not** generate silent placeholder audio; TTS failures fail the episode (no `anullsrc` fallback).

## Architecture

1. **Shield** — classifies lecture text once (`ALLOW` / `BLOCK`), same policy as chat/autocourse.
2. **Planner agent** (`automanim_planner`) — JSON `VizPlan` with 1–`automanim_max_scenes_per_lecture` `SceneSpec` entries.
3. **Codegen agent** (`automanim_codegen`) — Manim CE Python, one `Scene` subclass per scene.
4. **Critic** — `syntax_ok`, `Scene` subclass, size cap, ManimGL pattern ban; optional `automanim_llm_critic` via Ollama.
5. **Render** — `LocalRenderBackend` (`educlaw.viz.render_to_mp4`) or `DockerRenderBackend` (`docker run --rm --network=none` + `educlaw/manim:latest`).

Optional **ADK** `SequentialAgent` factory: `educlaw.automanim.build_planner_codegen_sequential` (for experiments; the default orchestrator runs planner/codegen in separate invocations so each scene can be revised independently).

## Settings (`profiles/local.toml` / env `EDUCLAW_*`)

| Key | Default | Purpose |
|-----|---------|---------|
| `automanim_enabled` | `false` | When `true`, `run_autocourse()` (Python) and scripts such as `run_full_course_pipeline.py` run AutoManim after each lecture; **not** used by gateway WebSocket chat. |
| `automanim_backend` | `local` | `local` or `docker`. |
| `automanim_image` | `educlaw/manim:latest` | Docker image for `docker` backend. |
| `automanim_quality` | `l` | Maps to `-ql` … `-qk`. |
| `automanim_timeout_sec` | `180` | Per-scene render wall time. |
| `automanim_max_attempts` | `3` | Codegen/critic retries per scene. |
| `automanim_max_scenes_per_lecture` | `6` | Hard cap on planner scenes. |
| `automanim_output_dir` | `{data_dir}/automanim` | Default artifact root (CLI uses `videos/` under the series dir). |
| `automanim_llm_critic` | `false` | Extra Ollama review pass. |
| `automanim_max_source_bytes` | `200000` | Reject oversized sources. |

## CLI

From repo root (venv with `educlaw` installed):

```bash
educlaw automanim run content/ir/series/my-course-8
```

Writes:

- `content/ir/series/my-course-8/videos/<lecture-id>/*.mp4`
- `content/ir/series/my-course-8/videos/manifest.json`

Each `lecture-*.md` is parsed with **YAML frontmatter** (metadata becomes `ir_suggestion`; body is the lecture Markdown).

`educlaw automanim plan` and `educlaw automanim render` are **placeholders** — use `run` for production renders.

## Running independently (verification)

Use this section to smoke-test the production render pipeline without autocourse or the full course pipeline.

### Prerequisites

```bash
export EDUCLAW_PROFILE_PATH=profiles/local.toml   # optional
export OLLAMA_API_BASE=http://127.0.0.1:11434
ollama pull gemma4:e2b                            # or your profile model_id
pip install -e ".[automanim]"                     # Manim CE for local backend
educlaw doctor                                    # warns if Manim missing when automanim_backend=local
```

`automanim_enabled` in the profile is **not required** for `educlaw automanim run` — it only gates `run_autocourse()` and scripts such as `run_full_course_pipeline.py`.

### CLI smoke test (recommended)

Create a minimal series directory with one lecture and run:

```bash
mkdir -p /tmp/automanim-smoke
cp content/ir/series/2026-04-23-linear-algebra-e2e-tts/lecture-01-vectors-and-vector-spaces.md \
   /tmp/automanim-smoke/

educlaw automanim run /tmp/automanim-smoke
```

The CLI is **quiet during the run** — it only prints yellow `error` lines and a green manifest path at the end. Progress is not streamed to the terminal.

**What to inspect after success:**

| Artifact | Path | What it tells you |
|----------|------|-------------------|
| MP4s | `<series-dir>/videos/<lecture-id>/*.mp4` | Render succeeded |
| Manifest | `<series-dir>/videos/manifest.json` | Per-scene `exit_code`, `artifact_path`, `log_path` |
| Scene workspace | paths in manifest `scene_dir` / `source_path` | Generated Manim Python + render logs |

### Live progress via WebSocket

To watch **phase / plan / codegen / critic / render** events as they happen, use the gateway WebSocket (see [DEVELOPERS.md](DEVELOPERS.md) § WebSocket):

```bash
educlaw serve
```

Send one JSON frame to `ws://127.0.0.1:18789/ws`:

```json
{"type":"automanim","markdown":"# Dot product\n\nExplain dot product with a 2D example.","metadata":{"id":"smoke-1","title":"Dot product"}}
```

With [websocat](https://github.com/vi/websocat) installed:

```bash
printf '%s\n' '{"type":"automanim","markdown":"# Dot product\n\nExplain dot product with a 2D example.","metadata":{"id":"smoke-1","title":"Dot product"}}' \
  | websocat -n1 ws://127.0.0.1:18789/ws
```

Watch for frames:

- `automanim.progress` — `kind`: `phase`, `plan`, `scene_start`, `codegen`, `critic`, `render`, `scene_done`, `done`, `error`
- `automanim.done` — `success`, `artifact_paths`, `artifact_urls` (served under `GET /artifacts/manim/...`)

Output lands in `~/.educlaw/automanim/ws-<session-id>/` (from `automanim_output_dir`).

### Automated checks (pytest)

For CI-style verification without calling Ollama on every run:

```bash
# Unit tests (mocked LLM + render) — fast
pytest tests/unit/test_automanim_orchestrator.py tests/unit/test_automanim_planner.py \
       tests/unit/test_automanim_critic.py tests/unit/test_automanim_render_local.py -q

# Real Manim subprocess — slow, skipped if manim not installed
pytest tests/integration/test_automanim_render.py -q -m slow
```

Unit tests validate pipeline wiring; the integration test validates Manim CE install only (no Ollama).

### Tuning for faster iteration

Useful profile knobs in `profiles/local.toml` when checking performance:

- `automanim_quality = "l"` — lowest render quality (fastest)
- `automanim_max_scenes_per_lecture = 1` — cap scenes for smoke runs
- `automanim_timeout_sec` — per-scene wall time
- `automanim_backend = "docker"` — alternative if local Manim install is problematic

### What is not a standalone entry point

- `educlaw automanim plan` / `render` — placeholders only
- `automanim_enabled` — autocourse hook only; not needed for `automanim run`
- Gateway plain-text chat (`Hello`) — does not trigger AutoManim; send a JSON frame with `"type":"automanim"` instead

## Autocourse hook (Python API / CLI scripts)

The gateway **`/ws` chat endpoint does not stream AutoManim** (it is plain Ollama text chat; see [DEVELOPERS.md](DEVELOPERS.md)). When `automanim_enabled` is true, **`run_autocourse()`** yields `AutocourseEvent` objects with `kind="automanim"` after each lecture (for callers that iterate the async generator—e.g. `scripts/run_full_course_pipeline.py`), not WebSocket JSON frames on `/ws`.

Failures are **non-fatal** for the rest of the course: the orchestrator yields an `error` event and continues with the next lecture.

## Docker image

```bash
docker build -f docker/manim.Dockerfile -t educlaw/manim:latest .
```

## Shared viz module

`educlaw.viz` centralizes `scene_class_name`, `extract_python`, `render_executable`, and `render_to_mp4`. ManiBench’s harness re-imports these for a single command shape — see [MANIM_PIPELINE.md](MANIM_PIPELINE.md).

## Security

Treat generated Python as **untrusted**. Prefer `automanim_backend = "docker"` with `--network=none` for isolation. Local mode runs `manim` in a temp directory on the host process.
