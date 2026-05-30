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
educlaw automanim content/ir/series/my-course-8
```

Writes:

- `content/ir/series/my-course-8/videos/<lecture-id>/*.mp4`
- `content/ir/series/my-course-8/videos/manifest.json`

Each `lecture-*.md` is parsed with **YAML frontmatter** (metadata becomes `ir_suggestion`; body is the lecture Markdown).

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
