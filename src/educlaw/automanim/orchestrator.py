"""AutoManim: plan scenes, codegen Manim CE, critic loop, render to MP4."""

from __future__ import annotations

import json
import logging
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
from educlaw.viz import manim_available

_AUTOMANIM_LOCAL_MANIM_HINT = (
    "Manim Community Edition is not available (no `manim` on PATH and "
    "`python -m manim` failed). Install with: pip install 'educlaw[automanim]' "
    '(or pip install manim). Or set automanim_backend = "docker" and pull '
    "`manimcommunity/manim:stable` (default; see docs/AUTOMANIM.md) or build "
    "`educlaw/manim:latest` from docker/manim.Dockerfile."
)

LOG = logging.getLogger(__name__)


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

    yield AutoManimEvent(
        kind="phase",
        lecture_id=lecture_id,
        message="Starting AutoManim pipeline.",
    )

    yield AutoManimEvent(
        kind="phase",
        lecture_id=lecture_id,
        message="Running safety classification (Shield)…",
    )
    LOG.info("automanim lecture=%s phase=shield_classify_start", lecture_id)

    verdict = await shield.classify(lecture_markdown[:50_000])
    if verdict == Verdict.BLOCK:
        LOG.warning("automanim lecture=%s shield=BLOCK", lecture_id)
        yield AutoManimEvent(
            kind="error",
            lecture_id=lecture_id,
            message="Lecture blocked by safety policy.",
        )
        return

    LOG.info("automanim lecture=%s shield=OK", lecture_id)
    yield AutoManimEvent(
        kind="phase",
        lecture_id=lecture_id,
        message="Safety check passed.",
    )

    if settings.automanim_backend == "local" and not manim_available():
        LOG.error("automanim lecture=%s manim_missing backend=local", lecture_id)
        yield AutoManimEvent(
            kind="error",
            lecture_id=lecture_id,
            message=_AUTOMANIM_LOCAL_MANIM_HINT,
        )
        return

    planner = build_planner_agent(settings)
    user_plan = (
        "IR metadata (JSON):\n"
        f"{json.dumps(ir_suggestion, indent=2)[:8000]}\n\n"
        "Lecture (Markdown):\n"
        f"{lecture_markdown[:40_000]}"
    )

    yield AutoManimEvent(
        kind="phase",
        lecture_id=lecture_id,
        message="Planning scenes with LLM…",
    )
    LOG.info("automanim lecture=%s phase=planner_llm_start", lecture_id)

    try:
        raw_plan = await run_llm_agent_once(planner, user_text=user_plan)
        plan = parse_viz_plan(raw_plan, max_scenes=settings.automanim_max_scenes_per_lecture)
    except Exception as e:  # noqa: BLE001
        LOG.exception("automanim lecture=%s planner_failed err=%s", lecture_id, e)
        yield AutoManimEvent(
            kind="error",
            lecture_id=lecture_id,
            message=f"Planner failed: {e!s}",
        )
        return

    LOG.info(
        "automanim lecture=%s phase=planner_llm_done scene_count=%d",
        lecture_id,
        len(plan.scenes),
    )
    yield AutoManimEvent(
        kind="phase",
        lecture_id=lecture_id,
        message=f"Plan ready: {len(plan.scenes)} scene(s).",
    )

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

    max_att = settings.automanim_max_attempts

    for idx, scene in enumerate(plan.scenes, start=1):
        yield AutoManimEvent(
            kind="scene_start",
            lecture_id=lecture_id,
            scene_index=idx,
            scene_title=scene.title,
            message=f"Scene {idx} of {len(plan.scenes)}",
        )
        LOG.info(
            "automanim lecture=%s scene=%d/%d title=%s",
            lecture_id,
            idx,
            len(plan.scenes),
            scene.title,
        )

        revision: str | None = None
        source = ""
        for attempt in range(1, max_att + 1):
            yield AutoManimEvent(
                kind="codegen",
                lecture_id=lecture_id,
                scene_index=idx,
                scene_title=scene.title,
                message=f"Generating Manim code (attempt {attempt}/{max_att})",
                extra={"attempt": attempt},
            )
            try:
                user_cg = build_codegen_user_message(
                    scene, lecture_title=lecture_title, revision_feedback=revision
                )
                source = await run_llm_agent_once(codegen, user_text=user_cg)
            except Exception as e:  # noqa: BLE001
                LOG.exception(
                    "automanim lecture=%s scene=%d codegen_failed attempt=%d err=%s",
                    lecture_id,
                    idx,
                    attempt,
                    e,
                )
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
                scene_title=scene.title,
                source_preview=source[:400],
                message=f"Running critic (attempt {attempt}/{max_att})",
                extra={"attempt": attempt},
            )
            st = static_critic(source, max_source_bytes=settings.automanim_max_source_bytes)
            if not st.ok:
                revision = st.feedback
                LOG.info(
                    "automanim lecture=%s scene=%d static_critic_reject attempt=%s",
                    lecture_id,
                    idx,
                    attempt,
                )
                continue

            if settings.automanim_llm_critic and ollama is not None:
                llm_r = await llm_critic_review(ollama, settings.model_id, source)
                if not llm_r.ok:
                    revision = llm_r.feedback
                    LOG.info(
                        "automanim lecture=%s scene=%d llm_critic_reject attempt=%s",
                        lecture_id,
                        idx,
                        attempt,
                    )
                    continue

            scene_dir = lec_dir / f"{idx:02d}-{_slug(scene.title)}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            dest = scene_dir / "scene.mp4"
            yield AutoManimEvent(
                kind="render",
                lecture_id=lecture_id,
                scene_index=idx,
                scene_title=scene.title,
                message=f"Rendering video → {scene_dir.name}/{dest.name}",
                extra={"path": str(dest), "scene_dir": str(scene_dir)},
            )
            try:
                art = await backend.render_scene(source, dest)
            except Exception as e:  # noqa: BLE001
                LOG.exception(
                    "automanim lecture=%s scene=%d render_exc err=%s",
                    lecture_id,
                    idx,
                    e,
                )
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
                    scene_dir=str(dest.parent),
                    source_path=str(dest.parent / "scene.py"),
                    log_path=str(dest.parent / "render.log"),
                )
            else:
                if art.exit_code != 0 or not (art.artifact_path or "").strip():
                    tail = (art.stderr_tail or "").strip()
                    if len(tail) > 1200:
                        tail = tail[:1200] + "…"
                    LOG.warning(
                        "automanim lecture=%s scene=%d render_subproc_failed exit=%s stderr=%s",
                        lecture_id,
                        idx,
                        art.exit_code,
                        (tail[:400] + "…") if len(tail) > 400 else tail or "(empty)",
                    )
                    detail = tail or "no MP4 written (Manim exit non-zero or no output file)"
                    yield AutoManimEvent(
                        kind="error",
                        lecture_id=lecture_id,
                        scene_index=idx,
                        message=f"Render failed (exit {art.exit_code}): {detail}",
                    )

            yield AutoManimEvent(
                kind="scene_done",
                lecture_id=lecture_id,
                scene_index=idx,
                scene_title=scene.title,
                artifact=art,
            )
            LOG.info(
                "automanim lecture=%s scene=%d scene_done exit=%s path=%s",
                lecture_id,
                idx,
                art.exit_code,
                art.artifact_path or "(none)",
            )
            break
        else:
            LOG.warning(
                "automanim lecture=%s scene=%d critic_exhausted attempts=%d",
                lecture_id,
                idx,
                max_att,
            )
            yield AutoManimEvent(
                kind="error",
                lecture_id=lecture_id,
                scene_index=idx,
                message=f"Critic rejected after {max_att} attempt(s). "
                f"Last feedback: {revision or 'unknown'}",
            )

    yield AutoManimEvent(kind="done", lecture_id=lecture_id, message="AutoManim finished.")
    LOG.info("automanim lecture=%s phase=pipeline_done", lecture_id)
