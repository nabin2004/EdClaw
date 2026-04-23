# Developer guide

How to set up a dev environment, run the gateway, run checks, and use profiles. For architecture and subsystem mapping, see [EduClaw_Concepts_Explained.md](EduClaw_Concepts_Explained.md). For learner graph memory (PyPI `dagestan`), see [DAGESTAN.md](DAGESTAN.md). For multi-lecture generation over WebSocket, see [AUTOCOURSE.md](AUTOCOURSE.md). For optional speech synthesis, see [TTS.md](TTS.md). For future work, see [ROADMAP.md](ROADMAP.md).

For **ManiBench / Manim CE** fine-tuning: step-by-step runbook (every command), see [MANIBENCH_RUNBOOK.md](MANIBENCH_RUNBOOK.md). Package overview and stage summary: [training/manibench/README.md](../training/manibench/README.md). Hugging Face Jobs: [training/manibench/SUBMIT_HF_JOBS.md](../training/manibench/SUBMIT_HF_JOBS.md). For the **gateway Manim tool** (not yet fully wired), see the implementation spec [MANIM_PIPELINE.md](MANIM_PIPELINE.md).

## Prerequisites

- **Python 3.11+** (CI uses 3.12; local 3.14+ works with `uv` if available).
- **Ollama** on the same machine for the default local profile (`http://127.0.0.1:11434`).
- Optional: **Docker** for `DockerSandbox` and building `educlaw/runner:latest` / `educlaw/manim:latest`.
- **Git** and a working shell.

On Debian/Ubuntu, if `python3 -m venv` fails, install `python3-venv` (or use **`uv venv`**, which bundles pip).

## Environment setup

### 1. Clone and enter the repo

```bash
cd /path/to/EdClaw
```

### 2. Create a virtual environment

**Option A — uv (recommended if installed)**

```bash
uv venv
uv pip install -e ".[dev]"
```

**Option B — standard venv**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Option C — helper script**

```bash
./scripts/bootstrap.sh
```

### 3. Environment variables

```bash
cp .env.example .env
# Edit as needed, or set inline:
export EDUCLAW_PROFILE_PATH="$(pwd)/profiles/local.toml"
export OLLAMA_API_BASE="http://127.0.0.1:11434"
```

`OLLAMA_API_BASE` is read by LiteLLM when using the `ollama_chat/...` model id (see ADK Ollama docs). The `profiles/local.toml` `[env]` section can set this for you when using the default profile path logic.

## Running Ollama and models

Install [Ollama](https://ollama.com) and pull the models your profile references (defaults in `profiles/local.toml`):

```bash
ollama pull gemma3:latest
ollama pull embeddinggemma
ollama pull shieldgemma:2b
```

For more reliable **tool calling**, build a custom tag from [docker/modelfiles/gemma3-tool.Modelfile](../docker/modelfiles/gemma3-tool.Modelfile) and point `model_id` at that tag.

## Running the gateway

From the repo root, with the venv activated and `educlaw` on `PATH` (or via `python -m`):

```bash
educlaw serve
# Same as: uvicorn educlaw.gateway.app:app --host 127.0.0.1 --port 18789 --workers 1
```

- HTTP: `http://127.0.0.1:18789/healthz`
- WebSocket: `ws://127.0.0.1:18789/ws`

### WebSocket protocol (smoke test)

1. First message must be a **connect** frame:
   - `{"type": "connect", "token": "local_user:my-session"}`
   - Token is interpreted loosely: if it contains `:`, the parts are `user_id` and `session_id`.
2. Then send user turns:
   - `{"type": "message", "text": "Hello", "idempotency_key": "optional-id"}`
   - Autocourse (orchestrated course + end-to-end lectures via Ollama, not the ADK tutor): add `"mode": "autocourse"` on the same frame. Responses are `{"type": "autocourse_event", "payload": {"kind": "plan" | "lecture_start" | "lecture_done" | "done" | "error", ...}}` streamed in order.
   - TTS: send `{"type": "tts", "text": "…", "voice": "optional", "speed": 1.0}` when `tts_enabled` is true in the profile. Responses are `tts_event` frames (`kind`: `audio` with base64 WAV, then `done` or `error`). See [docs/TTS.md](TTS.md).

You can use any WebSocket client; `wscat` or a small Python script is enough for development.

## CLI reference

| Command | Purpose |
|--------|---------|
| `educlaw serve` | Start FastAPI + WebSocket gateway |
| `educlaw doctor` | Check `strict_local` and (unless offline) Ollama `/api/tags` |
| `educlaw doctor --offline` | CI-friendly: no Ollama HTTP calls |
| `educlaw ir lint` | Lint IR graph under configured `ir_root` |
| `educlaw ir index` | Build / refresh IR vector index (needs Ollama for embeddings) |
| `educlaw pull-models` | Shell out to `ollama pull` for default model set |
| `educlaw tts list` | List TTS backends (and voices when `tts_enabled`) |
| `educlaw tts say "…" -o out.wav` | Synthesize speech to WAV (needs `tts_enabled` + backend) |
| `educlaw automanim <series-dir>` | Render Manim MP4s for `lecture-*.md` (see [AUTOMANIM.md](AUTOMANIM.md)) |

## Configuration

- **TOML profiles**: [profiles/local.toml](../profiles/local.toml) (default), [profiles/cloud.toml](../profiles/cloud.toml) (stub).
- **Override profile path**: `EDUCLAW_PROFILE_PATH` or `educlaw` settings (`EDUCLAW_*` env vars from [settings](../src/educlaw/config/settings.py)).
- **Data directory**: `~/.educlaw` by default (main SQLite for IR index, `vectors.sqlite` for `educlaw ir index`, `dagestan_memory.json` for the temporal graph, default `tts/` cache, audit paths as wired). The repo’s [content/ir/](../content/ir/) is used as `ir_root` when that path exists.
- **Learner memory (Dagestan)**: PyPI package `dagestan` with defaults `dagestan_provider = "stub"` (no external LLM for extraction) and `dagestan_db_path` under `data_dir`. For real conversation ingestion, set `dagestan_provider` to `ollama` (uses `ollama_url` + `model_id`), or `openai` / `anthropic` with the usual API keys. See [DAGESTAN.md](DAGESTAN.md).
- **TTS (optional)**: set `tts_enabled = true` and `tts_backend` / `tts_model_id` (for Kitten) under `[educlaw]` — see [TTS.md](TTS.md). Without TTS, `type: tts` WebSocket frames return an error.
- **Autocourse**: use the WebSocket `mode` field as described in [AUTOCOURSE.md](AUTOCOURSE.md) (uses the same `model_id` and Ollama host as the rest of the app). Optional **AutoManim** after each lecture: set `automanim_enabled = true` under `[educlaw]` — [AUTOMANIM.md](AUTOMANIM.md).

## Tests and quality

```bash
ruff check src tests
mypy src/educlaw
pytest
```

CI (`.github/workflows/ci.yml`) runs the same, plus `educlaw doctor --offline`.

## Docker images (optional)

```bash
docker build -f docker/runner.Dockerfile -t educlaw/runner:latest .
docker build -f docker/manim.Dockerfile -t educlaw/manim:latest .
```

The gateway currently defaults to `NullSandbox` for shell tools unless you wire `DockerSandbox` in code or a future profile flag.

## Troubleshooting

- **`externally-managed-environment` (pip)**: Use a venv or `uv venv` — do not install into system Python.
- **Ollama connection errors**: Ensure Ollama is running and `OLLAMA_API_BASE` matches. Run `educlaw doctor` (without `--offline`).
- **Tool call loops or missing tools**: Use `ollama_chat/` in LiteLLM, not `ollama/`; use a tool-capable Gemma build if the base tag does not support tools.
- **Empty IR**: Set `ir_root` or add Markdown under [content/ir/](../content/ir/); run `educlaw ir lint`.
- **Autocourse errors** (`autocourse_event` with `kind: error`): invalid JSON from the planner, empty lecture list, or Ollama failures — check `OLLAMA_API_BASE` / Ollama logs; reduce topic length; ensure `model_id` supports JSON-style chat for the plan step.
- **TTS disabled or `tts_model_id` required**: see [TTS.md](TTS.md) — for `kitten`, set a Hugging Face repo id; for tests use `tts_backend = "null"`.
- **Dagestan `stub` and empty ingest**: the default `dagestan_provider` does not run a real LLM for extraction, so session ingestion may add no graph nodes. Switch to `ollama` or a cloud provider for populated graph memory; see [DAGESTAN.md](DAGESTAN.md).

## Contributing

- Follow [AGENTS.md](../AGENTS.md) for stack conventions.
- Keep changes scoped; prefer small PRs that map to one subsystem in the concepts doc.
