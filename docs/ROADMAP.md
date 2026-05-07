# Roadmap

This document describes **planned** work. Nothing here is a commitment or release promise; it reflects the direction of the EduClaw scaffold and pedagogy-focused subsystems.

## Near term (MVP hardening)

- ~~**Course site generation**: Copier-based Jekyll site scaffolding from autocourse output (`educlaw site generate`), course registry (`courses.yml`), and catalog landing page. See [SITE_GENERATION.md](SITE_GENERATION.md).~~ *(done)*
- **WebChat UX**: Minimal static client that speaks the `/ws` protocol (plain-text turns + JSON `assistant.status` / `assistant.delta` frames); see [DEVELOPERS.md](DEVELOPERS.md).
- **Tool-capable Gemma**: Document and CI-gate the `docker/modelfiles/gemma3-tool.Modelfile` build; optional `educlaw doctor` check that a `*-tool` tag exists when tools are enabled.
- **Sandbox selection**: Profile or env flag to choose `NullSandbox` vs `DockerSandbox` after `educlaw/runner:latest` is built; fail fast with a clear message if Docker is unavailable.
- **IR tools**: Add `ir_prereq_walk` / richer `slice_for_learner` (graph walks, prerequisite ordering) on top of the existing `networkx` lint path.
- **Dagestan**: Learner memory already uses the PyPI temporal graph (decay, curation, retrieval live upstream; see [DAGESTAN.md](DAGESTAN.md)). Open directions: optional migration to a stronger backing store (e.g. `kuzu`) when scale demands it, while keeping the same `educlaw.memory.dagestan` async surface.

## Medium term (product shape)

- **Autocourse + TTS**: Optional server- or client-side path to read aloud each `lecture_done` (e.g. call `type: tts` with excerpted text, or a single `autocourse`+`tts` flag) without blocking the Ollama generation loop.
- **Channels**: Real `python-telegram-bot` / `discord.py` / `matrix-nio` adapters behind `educlaw.channels` entry points; shared session mapping from `thread_id` to ADK `session_id`.
- **Persistence**: Replace or supplement `InMemorySessionService` with a database-backed session store for restarts and multi-process scaling of *non-agent* workers (gateway still single-worker for one logical agent state by default).
- **Manim pipeline**: **AutoManim** covers lecture → Manim CE → MP4 (CLI + optional autocourse hook); see [AUTOMANIM.md](AUTOMANIM.md). Remaining: wire the ADK tutor `queue_manim_render` tool + optional HTTP artifact routes per [MANIM_PIPELINE.md](MANIM_PIPELINE.md).
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
