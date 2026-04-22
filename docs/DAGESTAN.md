# Dagestan: PyPI package vs EduClaw

## Canonical package

Learner memory is implemented by the **`dagestan`** distribution on **PyPI** ([pypi.org/project/dagestan](https://pypi.org/project/dagestan/)). Source and docs also live on GitHub ([github.com/nabin2004/dagestan](https://github.com/nabin2004/dagestan)).

That library stores memory as a **typed temporal knowledge graph** (entities, concepts, events, preferences, goals), with JSON persistence, optional LLM extraction (`stub`, OpenAI, Anthropic, or a custom client), curation (decay, contradictions), and graph retrieval without embedding similarity for the graph path.

The package is **MIT licensed**. EduClaw is **Apache-2.0**; keep that distinction in mind when copying or extending upstream code.

## What EduClaw does

[`educlaw.memory.dagestan`](../src/educlaw/memory/dagestan.py) is a **thin async adapter**: it constructs upstream `dagestan.Dagestan` from [`Settings`](../src/educlaw/config/settings.py) (`dagestan_db_path`, `dagestan_provider`, and Ollama-backed `llm_client` when `dagestan_provider` is `ollama`), and runs blocking upstream calls in a worker thread via **anyio**.

It preserves EduClaw’s existing async surface for tools and ADK:

- `ingest_log(session_id, role, text)` — conversation ingestion with `source=session_id`
- `recall(query, k)` — graph retrieval, mapped to `(id, source)` tuples for `DagestanMemoryService`
- `assert_fact` / `snapshot` — learner beliefs as **`NodeType.PREFERENCE`** nodes keyed by `source` (learner id); returns **`BeliefFact`** dataclasses (`id`, `predicate`, `object`, `confidence`)

SQLAlchemy models **`Fact`** and **`EmbeddedLog`** in [`memory/models.py`](../src/educlaw/memory/models.py) are **no longer written** by this adapter but remain in the schema so existing SQLite files keep working under `create_all`.

## See also

- [EduClaw_Concepts_Explained.md](EduClaw_Concepts_Explained.md) — subsystem table and §12
- [`src/educlaw/memory/adk_memory_service.py`](../src/educlaw/memory/adk_memory_service.py) — ADK `BaseMemoryService` bridge
