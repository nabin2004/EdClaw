# Roadmap

This document describes **planned** work. Nothing here is a commitment or release promise; it reflects the direction of the EduClaw scaffold and pedagogy-focused subsystems.

## Near term (MVP hardening)

- **WebChat UX**: Minimal static or single-page client that speaks the `/ws` protocol (connect + message frames), so new contributors can exercise the stack without hand-rolling JSON over `wscat`.
- **Tool-capable Gemma**: Document and CI-gate the `docker/modelfiles/gemma3-tool.Modelfile` build; optional `educlaw doctor` check that a `*-tool` tag exists when tools are enabled.
- **Sandbox selection**: Profile or env flag to choose `NullSandbox` vs `DockerSandbox` after `educlaw/runner:latest` is built; fail fast with a clear message if Docker is unavailable.
- **IR tools**: Add `ir_prereq_walk` / richer `slice_for_learner` (graph walks, prerequisite ordering) on top of the existing `networkx` lint path.
- **Dagestan**: Background decay for fact confidence; optional migration to a stronger graph store (`kuzu`) when scale demands it, behind the same service interface.

## Medium term (product shape)

- **Autocourse + TTS**: Optional server- or client-side path to read aloud each `lecture_done` (e.g. call `type: tts` with excerpted text, or a single `autocourse`+`tts` flag) without blocking the Ollama generation loop.
- **Channels**: Real `python-telegram-bot` / `discord.py` / `matrix-nio` adapters behind `educlaw.channels` entry points; shared session mapping from `thread_id` to ADK `session_id`.
- **Persistence**: Replace or supplement `InMemorySessionService` with a database-backed session store for restarts and multi-process scaling of *non-agent* workers (gateway still single-worker for one logical agent state by default).
- **Manim pipeline**: End-to-end path from IR `manim` hints to `educlaw/manim:latest` job queue and artifact storage.
- **Evaluation**: ADK eval JSON under `tests/evals/`, run in CI with mocked or pinned models where feasible.

## Longer term (ambitious)

- **Training package**: Flesh out `packages/educlaw-training/` (SFT/DPO, GGUF export, Ollama import) for FunctionGemma-style tool behavior on domain-specific tool traces.
- **Cloud profile**: Optional Gemini / Vertex / vLLM on Cloud Run in `profiles/cloud.toml` with strict separation from the default `strict_local` path.
- **Federation / content**: Versioned IR course packs, signing, and learner-specific overlays without forking the whole course repo.

## Explicit non-goals (for now)

- Transpiling the upstream TypeScript OpenClaw codebase.
- Multi-gateway worker processes sharing one in-memory ADK state (scale via separate sandbox/model workers, not duplicate gateways).

## How to suggest changes

Open issues or design docs that reference concrete user stories (e.g. “learner on shared lab machine”, “offline-only school lab”). Link new features back to the **subsystem table** in [EduClaw_Concepts_Explained.md](EduClaw_Concepts_Explained.md) so the architecture stays coherent.
