# Agent / contributor notes

For human-oriented setup (venv, Ollama, `educlaw serve`, troubleshooting), see [docs/DEVELOPERS.md](docs/DEVELOPERS.md). For planned work, see [docs/ROADMAP.md](docs/ROADMAP.md).

## Stack

- **Python 3.11+** (CI uses 3.12)
- **google-adk**: `LlmAgent`, `Runner`, `InMemorySessionService`, `BaseMemoryService`, callbacks
- **litellm** (via ADK `LiteLlm`) + **ollama** Python client for embeddings (IR index CLI) / Shield
- **fastapi** + **uvicorn** — single ASGI app, **one worker** for gateway
- **sqlalchemy[asyncio]** + **aiosqlite** — ORM for IR index (`IrNodeRow`); learner graph memory via **PyPI `dagestan`** (JSON), wrapped by `educlaw.memory.dagestan`
- **No pluggy** — optional plugins use `importlib.metadata` entry points (`educlaw.channels`, `educlaw.tts`)

## Conventions

- Async-first on gateway and agent paths; avoid blocking I/O in request handlers.
- `strict_local` (default): only loopback model endpoints in `profiles/local.toml`.
- Shield: classify input in `before_model_callback`, output in `after_model_callback`; audit hashes only. The WebSocket **autocourse** and **tts** paths also run `Shield.classify` on the user string before Ollama / TTS.
- Sandbox: default `NullSandbox` for dev; use `DockerSandbox` when `educlaw/runner:latest` exists.
- IR: Markdown + YAML frontmatter under `content/ir` or `~/.educlaw/ir`; run `educlaw ir lint`.
- **Autocourse** (`autocourse/`, `autolecture/`) and **TTS** (`tts/`) are Ollama- or backend-driven outside the ADK `Runner`, but share settings and the gateway.

## Commands

- `educlaw serve` — gateway
- `educlaw doctor` / `educlaw doctor --offline` — health / CI
- `educlaw ir lint` / `educlaw ir index`
- `educlaw tts list` / `educlaw tts say` — TTS (when enabled in profile); see [docs/TTS.md](docs/TTS.md)
- `ruff check src tests`, `mypy src/educlaw`, `pytest`
