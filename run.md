# Runbook: EduClaw gateway + Ollama streaming chat

This walkthrough verifies the **`ollama` execution engine** (`OllamaChatExecutionEngine`): the gateway forwards each user message to **`POST http://127.0.0.1:11434/api/chat`** with streaming NDJSON and pushes tokens to the browser as WebSocket **`assistant.delta`** messages.

For Python venv installation and tooling, see [docs/DEVELOPERS.md](docs/DEVELOPERS.md).

## 1. Prerequisites

- **Python 3.11+** and an activated venv with EduClaw installed (`pip install -e ".[dev]"` or equivalent).
- **Ollama** running locally (default URL: `http://127.0.0.1:11434`).
- The **chat model** your profile uses is pulled, for example:

  ```bash
  ollama pull gemma4:e2b
  ```

  The default repo profile sets `model_id = "gemma4:e2b"` in [profiles/local.toml](profiles/local.toml). Adjust the pull command if you change `model_id`.

## 2. Configuration

Default local profile already enables Ollama streaming:

- `gateway_execution_engine = "ollama"` under `[educlaw]`
- `ollama_url` and `model_id` under `[educlaw]`
- Optional: `ollama_chat_think` — `false` (default) sends `"think": false` in the chat JSON; `null` omits the field.

To use another profile file:

```bash
export EDUCLAW_PROFILE_PATH="/path/to/your.toml"
```

## 3. Health check (Ollama + profile)

From the repo root (venv active):

```bash
educlaw doctor
```

You should see `strict_local: OK` and `Ollama: OK`. Warnings about missing models mean you should `ollama pull` the named tags.

CI-style (no HTTP to Ollama):

```bash
educlaw doctor --offline
```

## 4. Start the gateway

```bash
educlaw serve
```

Defaults come from the profile (typically `http://127.0.0.1:18789`).

## 5. Verify HTTP

In another terminal:

```bash
curl -sS http://127.0.0.1:18789/healthz
```

Expected: JSON like `{"status":"ok"}`.

## 6. Verify Ollama alone (optional)

Confirms the model answers outside EduClaw:

```bash
curl -sS http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma4:e2b","messages":[{"role":"user","content":"Say hi in one word."}],"stream":false,"think":false}'
```

Replace `gemma4:e2b` if your profile uses another `model_id`.

## 7. Verify WebSocket + streaming UI

1. Open **http://127.0.0.1:18789/** in a browser (static chat page).
2. Wait until the status shows **Connected**.
3. Send a short message. The assistant reply should **appear token-by-token** (streaming), not only after the full response.

The page sends **plain WebSocket text** frames; the server replies with JSON lines such as:

```json
{"type":"assistant.delta","token":"<fragment>"}
```

### Raw WebSocket (optional)

Tools like **[websocat](https://github.com/vi/websocat)** can connect after the server is up:

```bash
websocat ws://127.0.0.1:18789/ws
```

Type a line of text and press Enter; watch for JSON `assistant.delta` messages.

## 8. Troubleshooting

| Symptom | What to check |
|--------|----------------|
| Immediate stub text like “Stub response (no LLM wired yet)” | `gateway_execution_engine` is not `"ollama"` in the active profile, or profile path is wrong. |
| Gateway errors / empty reply | Is Ollama running? Run `educlaw doctor`. Is `model_id` pulled? |
| Browser stuck on Disconnected | Is `educlaw serve` running? Firewall / wrong host/port? |
| Shield / embeddings / IR | Those use separate code paths; this runbook covers only **gateway tutor chat** via `gateway_execution_engine = "ollama"`. |

## 9. Other engines

- **`stub`**: No model; canned reply (good for offline tests).
- **`pi`**: Requires `pip install "educlaw[pi]"` (`pi-agent-core`); richer agent loop + tools.
