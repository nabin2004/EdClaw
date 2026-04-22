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
- **Shield** classifies the user’s topic string before any generation (same as normal chat: `BLOCK` stops the run with an `autocourse_event` error).

## WebSocket protocol

Connect as usual, then send:

```json
{"type": "message", "mode": "autocourse", "text": "Teach me linear algebra for beginners", "idempotency_key": "optional"}
```

Add `"mode": "autocourse"` on the **same** `type: "message"` frame used for chat. Without that field (or with any other `mode`), the gateway runs the normal ADK tutor instead.

The server streams JSON frames:

- `{"type": "autocourse_event", "payload": { ... }}`

`payload.kind` is one of: `plan`, `lecture_start`, `lecture_done`, `done`, `error`.

- `lecture_done` includes the generated lecture (`result` with Markdown and optional `ir_suggestion` metadata for a future IR export).
- A final `kind: "done"` indicates the course finished successfully.

## Course plan shape

The planner returns JSON matching `CoursePlan`: `title`, `audience`, and a list of `LectureOutline` (title, objectives, key_topics, optional `estimated_minutes`). The orchestrator **caps** the number of lectures at 8 to avoid unbounded work.

## See also

- [DEVELOPERS.md](DEVELOPERS.md) — WebSocket protocol and CLI overview.
- [EduClaw_Concepts_Explained.md](EduClaw_Concepts_Explained.md) — subsystem table.
- [TTS.md](TTS.md) — separate `type: "tts"` frames; generated lecture text can be passed to TTS on the client or a future combined mode.
