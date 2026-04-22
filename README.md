# EduClaw

Local-first educational agent gateway: **Google ADK** for the agent loop, **Ollama** for Gemma / EmbeddingGemma / ShieldGemma, **FastAPI** for HTTP + WebSocket, **SQLAlchemy** + **sqlite-vec** (optional) for IR + Dagestan memory.

## Quickstart

```bash
cp .env.example .env
./scripts/bootstrap.sh   # or: uv venv && uv pip install -e ".[dev]"
export OLLAMA_API_BASE=http://127.0.0.1:11434
ollama pull gemma3:latest && ollama pull embeddinggemma && ollama pull shieldgemma:2b
educlaw doctor
educlaw serve
```

- Gateway: `http://127.0.0.1:18789` (HTTP + `ws://127.0.0.1:18789/ws`)
- WebSocket handshake: first frame `{"type":"connect","token":"local_user:my-session"}` then `{"type":"message","text":"Hello"}`

## Layout

- `src/educlaw/` — main package (gateway, agent, IR, memory, sandbox, safety, CLI)
- `content/ir/` — sample IR nodes (also used as default `ir_root` when present)
- `packages/educlaw-training/` — optional SFT/DPO tooling (stubs)
- `packages/educlaw-content-starter/` — publishable IR starter pack
- `profiles/` — TOML profiles (`local.toml` default)
- `docker/` — runner + manim images + Gemma tool Modelfile

## Documentation

- [docs/EduClaw_Concepts_Explained.md](docs/EduClaw_Concepts_Explained.md) — subsystem mapping (IR, Dagestan, ADK, Ollama)
- [docs/DEVELOPERS.md](docs/DEVELOPERS.md) — environment setup, run, CLI, tests, troubleshooting
- [docs/ROADMAP.md](docs/ROADMAP.md) — future work and planned directions
- [AGENTS.md](AGENTS.md) — contributor / AI agent conventions

## ADK + Ollama

Use `LiteLlm(model="ollama_chat/<tag>")` and set `OLLAMA_API_BASE` (required by LiteLLM). Prefer `ollama_chat/` over `ollama/` for tool-calling stability per ADK docs.

## License

Apache-2.0
