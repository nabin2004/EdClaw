```text

    ______    __      ________              
   / ____/___/ /_  __/ ____/ /___ __      __
  / __/ / __  / / / / /   / / __ `/ | /| / /
 / /___/ /_/ / /_/ / /___/ / /_/ /| |/ |/ / 
/_____/\__,_/\__,_/\____/_/\__,_/ |__/|__/  
```

# EduClaw

**Local-first educational agent gateway:** **Google ADK** for the agent loop, **Ollama** for Gemma / EmbeddingGemma (Shield classification reuses your main chat model by default), **FastAPI** for HTTP + WebSocket, **SQLAlchemy** + **sqlite-vec** (optional) for IR indexing, and **PyPI `dagestan`** for temporal-graph learner memory.

Wordmark source: [assets/ascii-logo.txt](assets/ascii-logo.txt) (font *slant*; regenerate with `pyfiglet -f slant EduClaw`).

## Quickstart

```bash
cp .env.example .env
./scripts/bootstrap.sh   # or: uv venv && uv pip install -e ".[dev]"
export OLLAMA_API_BASE=http://127.0.0.1:11434
ollama pull gemma3:latest && ollama pull embeddinggemma
educlaw doctor
educlaw serve
```

- Gateway: `http://127.0.0.1:18789` (HTTP + `ws://127.0.0.1:18789/ws`)
- **WebSocket `/ws`**: send **plain text** per turn; the server streams JSON `assistant.status` and `assistant.delta` frames (Ollama chat by default). **Autocourse** and **TTS** are **not** multiplexed on `/ws`—use [docs/AUTOCOURSE.md](docs/AUTOCOURSE.md) (`run_autocourse` / pipeline scripts) and `educlaw tts` / [docs/TTS.md](docs/TTS.md).

## Layout

- `src/educlaw/` — main package (gateway, agent, IR, memory, sandbox, safety, TTS, autocourse / autolecture / automanim, CLI)
- `content/ir/` — sample IR nodes (also used as default `ir_root` when present)
- `packages/educlaw-training/` — optional SFT/DPO tooling (stubs)
- `packages/educlaw-content-starter/` — publishable IR starter pack
- `profiles/` — TOML profiles (`local.toml` default)
- `docker/` — runner + manim images + Gemma tool Modelfile

## Documentation

- [docs/EduClaw_Concepts_Explained.md](docs/EduClaw_Concepts_Explained.md) — subsystem mapping (IR, Dagestan, ADK, Ollama, TTS, autocourse, AutoManim)
- [docs/DAGESTAN.md](docs/DAGESTAN.md) — PyPI `dagestan` package and how EduClaw wraps it
- [docs/AUTOCOURSE.md](docs/AUTOCOURSE.md) — Autocourse / Autolecture (`run_autocourse`, pipeline scripts)
- [docs/AUTOMANIM.md](docs/AUTOMANIM.md) — AutoManim: ADK planner/codegen + Manim render (CLI + optional autocourse hook)
- [docs/TTS.md](docs/TTS.md) — pluggable TTS registry, Kitten (offline), CLI
- [docs/DEVELOPERS.md](docs/DEVELOPERS.md) — environment setup, run, CLI, tests, troubleshooting, profiles and memory settings
- [docs/ROADMAP.md](docs/ROADMAP.md) — future work and planned directions
- [docs/MANIM_PIPELINE.md](docs/MANIM_PIPELINE.md) — how to implement the end-to-end Manim render path (stubs, IR hints, Docker, checklist)
- [AGENTS.md](AGENTS.md) — contributor / AI agent conventions

## ADK + Ollama

Use `LiteLlm(model="ollama_chat/<tag>")` and set `OLLAMA_API_BASE` (required by LiteLLM). Prefer `ollama_chat/` over `ollama/` for tool-calling stability per ADK docs.

## License

Apache-2.0
