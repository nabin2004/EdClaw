# AutoManim

**AutoManim** turns lecture Markdown (plus IR-shaped YAML frontmatter) into **Manim Community Edition** scenes and **MP4** artifacts. It is built from **Google ADK** `LlmAgent` instances (planner + codegen) plus a deterministic **render** step (local `manim` subprocess or **Docker** one-shot). A **static critic** loop rewrites bad codegen before render; an optional **LLM critic** adds a second Ollama pass.

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
| `automanim_enabled` | `false` | When `true`, `run_autocourse` emits `automanim` events after each `lecture_done`. |
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

## WebSocket / Autocourse

When `automanim_enabled` is true, the autocourse stream includes frames:

```json
{"type": "autocourse_event", "payload": {"kind": "automanim", "lecture_index": 1, "automanim": {"kind": "scene_done", "artifact": {"artifact_path": "...", "scene_name": "..."}, ...}}}
```

Failures are **non-fatal** for the rest of the course: the orchestrator yields an `error` `AutocourseEvent` and continues with the next lecture.

## Docker image

```bash
docker build -f docker/manim.Dockerfile -t educlaw/manim:latest .
```

## Shared viz module

`educlaw.viz` centralizes `scene_class_name`, `extract_python`, `render_executable`, and `render_to_mp4`. ManiBench’s harness re-imports these for a single command shape — see [MANIM_PIPELINE.md](MANIM_PIPELINE.md).

## Security

Treat generated Python as **untrusted**. Prefer `automanim_backend = "docker"` with `--network=none` for isolation. Local mode runs `manim` in a temp directory on the host process.
