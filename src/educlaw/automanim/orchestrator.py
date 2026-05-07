"""AutoManim: plan scenes, codegen Manim CE, critic loop, render to MP4."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ollama import AsyncClient

from educlaw.automanim.adk_runner import run_llm_agent_once
from educlaw.automanim.codegen import build_codegen_agent, build_codegen_user_message
from educlaw.automanim.critic import llm_critic_review, static_critic
from educlaw.automanim.planner import build_planner_agent, parse_viz_plan
from educlaw.automanim.render import build_render_backend
from educlaw.automanim.schema import AutoManimEvent, RenderArtifact
from educlaw.config.settings import Settings
from educlaw.safety.shield import NoopShield, Shield, Verdict


def _slug(s: str, max_len: int = 48) -> str:
    x = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (x[:max_len] or "scene").rstrip("-")


async def run_automanim(
    lecture_markdown: str,
    ir_suggestion: dict[str, Any],
    settings: Settings,
    shield: Shield | NoopShield,
    ollama: AsyncClient | None = None,
    *,
    output_root: Path | None = None,
) -> AsyncIterator[AutoManimEvent]:
    """Stream AutoManim pipeline events for one lecture."""
    lecture_id = str(ir_suggestion.get("id") or "lecture")
    lecture_title = str(ir_suggestion.get("title") or lecture_id)

    verdict = await shield.classify(lecture_markdown[:50_000])
    if verdict == Verdict.BLOCK:
        yield AutoManimEvent(
            kind="error",
            lecture_id=lecture_id,
            message="Lecture blocked by safety policy.",
        )
        return

    planner = build_planner_agent(settings)
    user_plan = (
        "IR metadata (JSON):\n"
        f"{json.dumps(ir_suggestion, indent=2)[:8000]}\n\n"
        "Lecture (Markdown):\n"
        f"{lecture_markdown[:40_000]}"
    )
    try:
        raw_plan = await run_llm_agent_once(planner, user_text=user_plan)
        plan = parse_viz_plan(raw_plan, max_scenes=settings.automanim_max_scenes_per_lecture)
    except Exception as e:  # noqa: BLE001
        yield AutoManimEvent(
            kind="error",
            lecture_id=lecture_id,
            message=f"Planner failed: {e!s}",
        )
        return

    yield AutoManimEvent(
        kind="plan",
        lecture_id=lecture_id,
        message=f"{len(plan.scenes)} scene(s)",
        extra={"scenes": [s.model_dump() for s in plan.scenes]},
    )

    if not plan.scenes:
        yield AutoManimEvent(kind="done", lecture_id=lecture_id, message="No scenes planned.")
        return

    root = output_root or (settings.automanim_output_dir or settings.data_dir / "automanim")
    lec_dir = root / _slug(lecture_id)
    lec_dir.mkdir(parents=True, exist_ok=True)

    codegen = build_codegen_agent(settings)
    backend = build_render_backend(settings)

    for idx, scene in enumerate(plan.scenes, start=1):
        yield AutoManimEvent(
            kind="scene_start",
            lecture_id=lecture_id,
            scene_index=idx,
            scene_title=scene.title,
        )
        revision: str | None = None
        source = ""
        for attempt in range(1, settings.automanim_max_attempts + 1):
            yield AutoManimEvent(
                kind="codegen",
                lecture_id=lecture_id,
                scene_index=idx,
                scene_title=scene.title,
                extra={"attempt": attempt},
            )
            try:
                user_cg = build_codegen_user_message(
                    scene, lecture_title=lecture_title, revision_feedback=revision
                )
                source = await run_llm_agent_once(codegen, user_text=user_cg)
            except Exception as e:  # noqa: BLE001
                yield AutoManimEvent(
                    kind="error",
                    lecture_id=lecture_id,
                    scene_index=idx,
                    message=f"Codegen failed: {e!s}",
                )
                source = ""
                break

            yield AutoManimEvent(
                kind="critic",
                lecture_id=lecture_id,
                scene_index=idx,
                source_preview=source[:400],
                extra={"attempt": attempt},
            )
            st = static_critic(source, max_source_bytes=settings.automanim_max_source_bytes)
            if not st.ok:
                revision = st.feedback
                continue

            if settings.automanim_llm_critic and ollama is not None:
                llm_r = await llm_critic_review(ollama, settings.model_id, source)
                if not llm_r.ok:
                    revision = llm_r.feedback
                    continue

            dest = lec_dir / f"{idx:02d}-{_slug(scene.title)}.mp4"
            yield AutoManimEvent(
                kind="render",
                lecture_id=lecture_id,
                scene_index=idx,
                scene_title=scene.title,
                extra={"path": str(dest)},
            )
            try:
                art = await backend.render_scene(source, dest)
            except Exception as e:  # noqa: BLE001
                yield AutoManimEvent(
                    kind="error",
                    lecture_id=lecture_id,
                    scene_index=idx,
                    message=f"Render failed: {e!s}",
                )
                art = RenderArtifact(
                    artifact_path="",
                    scene_name="",
                    exit_code=1,
                    stderr_tail=str(e),
                )

            yield AutoManimEvent(
                kind="scene_done",
                lecture_id=lecture_id,
                scene_index=idx,
                scene_title=scene.title,
                artifact=art,
            )
            break
        else:
            yield AutoManimEvent(
                kind="error",
                lecture_id=lecture_id,
                scene_index=idx,
                message=f"Critic rejected after {settings.automanim_max_attempts} attempt(s). "
                f"Last feedback: {revision or 'unknown'}",
            )

    yield AutoManimEvent(kind="done", lecture_id=lecture_id, message="AutoManim finished.")
