# Autocourse and Autolecture

EduClaw can generate a **full multi-lecture course** from a user topic without going through the main ADK tutor. The pipeline is **not** ADK-based: the gateway calls Ollama directly.

## Modules

| Path | Role |
|------|------|
| `src/educlaw/autocourse/` | `run_autocourse()`: plans a `CoursePlan` (JSON from the chat model, `format="json"`), then drives one full lecture per outline. |
| `src/educlaw/autolecture/` | `generate_lecture()`: given a `LectureOutline`, produces a complete Markdown lecture (hook, explanation, example, recap, check-your-understanding). |

See [`orchestrator.py`](../src/educlaw/autocourse/orchestrator.py) and [`generator.py`](../src/educlaw/autolecture/generator.py) for prompts and event kinds.

## Requirements

- Same **Ollama** host as the rest of the stack (`EDUCLAW_OLLAMA_URL` / `profiles/local.toml` `ollama_url`).
- Chat `model_id` from settings is used for both the JSON course plan and each lecture.
- **Shield** classifies the user’s topic string before any generation (same as normal chat: `BLOCK` stops the run with an `AutocourseEvent` error).

## Gateway WebSocket vs autocourse

The live gateway (`educlaw serve`) exposes **`/ws` for plain-text turns only**: send a string, receive `assistant.status` and `assistant.delta` JSON frames (see [DEVELOPERS.md](DEVELOPERS.md)). There is **no** `mode: "autocourse"` multiplex on that socket today.

To run autocourse, call **`run_autocourse()`** from Python (async iterator of `AutocourseEvent`) or use **`scripts/run_full_course_pipeline.py`** / `scripts/run_full_course_pipeline.sh`. Event kinds include `plan`, `lecture_start`, `lecture_done`, `done`, `error`, and `automanim` when `automanim_enabled` is true. See [AUTOMANIM.md](AUTOMANIM.md).

- `lecture_done` events carry the generated lecture (`result` with Markdown and optional `ir_suggestion` metadata).
- A final `kind: "done"` indicates the course finished successfully.

## Course plan shape

The planner returns JSON matching `CoursePlan`: `title`, `audience`, and a list of `LectureOutline` (title, objectives, key_topics, optional `estimated_minutes`). The orchestrator **caps** the number of lectures at 8 to avoid unbounded work.

## Full local pipeline (CLI script)

To generate Markdown, optional Manim videos, and optional TTS audio in one run (no gateway), use:

```bash
./scripts/run_full_course_pipeline.sh "Your course topic" --lectures 4
```

Requires Ollama; enable TTS and AutoManim in `profiles/local.toml` or pass **`--no-tts`**, **`--no-automanim`**, or **`--no-shield`** (no Ollama call for the AutoManim pre-scene classifier; uses `NoopShield`). The script runs **each lecture in order**: write Markdown, then optional chunked TTS WAV, then optional AutoManim, before starting the next lecture.

Output defaults to `content/ir/series/<date>-slug/`. See [scripts/run_full_course_pipeline.py](../scripts/run_full_course_pipeline.py). In `run_autocourse()`, `shield_enabled` controls whether AutoManim uses a real `Shield` or `NoopShield` when classifying lecture text; set `shield_enabled = false` if you want `NoopShield` for that path without an Ollama classify call.

## Site generation

After generating a lecture series (via the CLI script or WebSocket), you can scaffold a full Jekyll course website from the output:

```bash
educlaw site generate content/ir/series/2026-04-23-intro-linear-algebra-8
```

Or pass `--generate-site` to the pipeline script to do it in one step:

```bash
python scripts/run_full_course_pipeline.py "Linear Algebra" --lectures 4 --generate-site
```

See [SITE_GENERATION.md](SITE_GENERATION.md) for template variables, customization, and the course catalog.

## See also

- [DEVELOPERS.md](DEVELOPERS.md) — WebSocket protocol and CLI overview.
- [EduClaw_Concepts_Explained.md](EduClaw_Concepts_Explained.md) — subsystem table.
- [AUTOMANIM.md](AUTOMANIM.md) — optional Manim video generation after each lecture.
- [TTS.md](TTS.md) — `educlaw tts` CLI and TTS API; combine with generated lecture text outside `/ws` if you need speech.
- [SITE_GENERATION.md](SITE_GENERATION.md) — Copier-based course site scaffolding and catalog.
