# EduClaw Concepts — Python Tech Stack

**Status:** companion to the full architecture primer (TS/OpenClaw reference vs this repo’s Python implementation).

**Audience:** Python engineers implementing EduClaw with **Google ADK**, **Gemma** (via Ollama), **EmbeddingGemma**, **ShieldGemma**, and idiomatic libraries.

## Framing

- **Not a TypeScript fork.** Fresh Python code; borrows OpenClaw *ideas* (gateway daemon, channel adapters, sandbox, IR-aware context).
- **ADK-native.** `LlmAgent`, `Runner`, `SessionService`, `BaseMemoryService`, and callbacks replace a hand-rolled agent loop.
- **Async-first** on the gateway and tool path.

## Subsystem index → this repo

| # | Subsystem | Role | Primary paths |
|---|-----------|------|----------------|
| 1 | Gateway | FastAPI + WS + webhooks | `src/educlaw/gateway/` |
| 2 | Channels | Normalized envelopes | `src/educlaw/channels/` |
| 3 | Plugins | Entry-point discovery (no pluggy) | `src/educlaw/channels/registry.py` |
| 4 | Agent loop | ADK `Runner` + `LlmAgent` | `src/educlaw/agent/root.py`, `wiring.py` |
| 5 | Context engine | IR + beliefs in `before_model_callback` | `src/educlaw/agent/callbacks/ir_assemble.py` |
| 6 | Sandbox | `NullSandbox` / `DockerSandbox` | `src/educlaw/sandbox/` |
| 7 | Ollama + Gemma | `LiteLlm("ollama_chat/...")` | `src/educlaw/agent/model.py`, `profiles/local.toml` |
| 8 | EmbeddingGemma | `EmbeddingClient` + `VecStore` | `src/educlaw/memory/embeddings.py`, `vec_store.py` |
| 9 | FunctionGemma | Tools + optional training pkg | `src/educlaw/agent/tools/`, `packages/educlaw-training/` |
| 10 | ShieldGemma | `before_model` / `after_model` | `src/educlaw/safety/shield.py`, `agent/callbacks/shield_*.py` |
| 11 | IR | Pydantic + frontmatter + SQL index | `src/educlaw/ir/`, `content/ir/` |
| 12 | Dagestan | Facts + embedded logs + ADK memory | `src/educlaw/memory/dagestan.py`, `adk_memory_service.py` |

## 1. Gateway

Single ASGI app (`educlaw.gateway.app:app`): `GET /healthz`, `WS /ws`, webhooks under `POST /webhooks/{channel_id}`.

Run: `uvicorn educlaw.gateway.app:app --host 127.0.0.1 --port 18789 --workers 1`

## 2. Channels

`InboundEnvelope` / `OutboundMessage` in `channels/contract.py`. WebChat + CLI helpers; Telegram stub in `channels/telegram.py`.

## 3. Extensibility

Use `importlib.metadata` entry points group `educlaw.channels` (see `channels/registry.py`).

## 4–5. Agent + context

- Root agent: `agent/root.py` + `agent/wiring.py`
- Model: `LiteLlm(model=f"ollama_chat/{model_id}")` in `agent/model.py`
- Context injection: `callbacks/ir_assemble.py` appends IR slice + belief snapshot via `llm_request.append_instructions(...)`

## 6. Sandbox

`Sandbox` protocol in `sandbox/contract.py`. `NullSandbox` for safe local dev commands; `DockerSandbox` for hardened containers when Docker is available.

## 7. Ollama + Gemma

Set `OLLAMA_API_BASE` (see `profiles/local.toml` `[env]`). Use **ollama_chat** provider in LiteLLM. For reliable tool calls, build a tool-capable model from `docker/modelfiles/gemma3-tool.Modelfile`.

## 8. EmbeddingGemma

`EmbeddingClient.embed()` writes into `VecStore` (sqlite-vec when the extension loads; cosine fallback otherwise).

## 9. FunctionGemma

Structured tool calls: ADK `FunctionTool` wrappers in `agent/tools/`. LoRA / DPO pipeline stubs live under `packages/educlaw-training/`.

## 10. ShieldGemma

`Shield.classify()` calls Ollama `generate` with temperature 0. Wired as ADK callbacks; audit log stores **hashes only** (`safety/audit.py`).

## 11. IR

Author Markdown + YAML under `content/ir` (repo default) or `~/.educlaw/ir`. CLI: `educlaw ir lint`, `educlaw ir index`.

## 12. Dagestan

- SQL tables: `memory/models.py` (`Fact`, `EmbeddedLog`, `IrNodeRow`)
- Engine: `memory/dagestan.py`
- ADK integration: `DagestanMemoryService` implements `BaseMemoryService`; `after_agent_callback` calls `callback_context.add_session_to_memory()`.

## Appendix — dependencies

See root `pyproject.toml` for pinned stacks (`google-adk`, `litellm`, `fastapi`, `sqlalchemy[asyncio]`, `aiosqlite`, …). Optional extras: `sqlite-vec`, `channels`, `cloud`, `structured`, `training`.
