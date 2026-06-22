#!/usr/bin/env python3
"""
IR-first course pipeline: prompt → markdown (one by one) → unified IR JSON → audio + video.

For each lecture the strict order is:
  1. Write lecture-NN-<slug>.md
  2. Generate lecture-NN-ir.json  (TTS text + animation spec per chunk)
  3. Synthesize audio/lecture-NN.wav + audio/lecture-NN.srt / .vtt  (if --tts)
  4. Render Manim scenes per chunk animation spec under videos/  (if --manim)

The IR JSON is the single source of truth: it contains both the subtitle text for
the TTS model and the animation instructions (what/how to animate) for each audio chunk.

Examples:
  .venv/bin/python scripts/generate_ir_pipeline.py "Real Analysis" --lectures 4
  .venv/bin/python scripts/generate_ir_pipeline.py "Gradient Descent" --no-tts --no-manim
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter
from ollama import AsyncClient

from educlaw.autocourse.orchestrator import CoursePlanningFailed, plan_course
from educlaw.autolecture.generator import generate_lecture
from educlaw.config.settings import load_settings
from educlaw.tts.lecture_ir import LectureIR
from educlaw.tts.md_to_ir import markdown_to_lecture_ir, synthesize_from_ir


def _slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "lecture"


async def _render_manim_from_ir(
    ir: LectureIR,
    output_root: Path,
    settings: Any,
    ollama: AsyncClient,
) -> list[dict[str, object]]:
    """Render one Manim scene per chunk that has an animation spec, bypassing the planner."""
    import re as _re
    from educlaw.automanim.adk.adk_runner import run_llm_agent_once
    from educlaw.automanim.adk.codegen import build_codegen_agent, build_codegen_user_message
    from educlaw.automanim.adk.critic import static_critic
    from educlaw.automanim.adk.render import build_render_backend
    from educlaw.automanim.adk.schema import SceneSpec

    anim_chunks = ir.animation_chunks()
    if not anim_chunks:
        return []

    def _slug(s: str, max_len: int = 48) -> str:
        x = _re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return (x[:max_len] or "scene").rstrip("-")

    lec_dir = output_root / _slug(ir.lecture_id)
    lec_dir.mkdir(parents=True, exist_ok=True)

    codegen = build_codegen_agent(settings)
    backend = build_render_backend(settings)
    max_att = settings.automanim_max_attempts
    results: list[dict[str, object]] = []

    for idx, chunk in enumerate(anim_chunks, start=1):
        if chunk.animation is None:
            continue
        scene = SceneSpec(
            title=chunk.animation.title,
            description=chunk.animation.description,
            visual_intent=chunk.animation.visual_intent,
        )
        print(f"      Scene {idx}/{len(anim_chunks)}: {scene.title}")

        revision: str | None = None
        source = ""
        for attempt in range(1, max_att + 1):
            try:
                user_cg = build_codegen_user_message(
                    scene, lecture_title=ir.title, revision_feedback=revision
                )
                source = await run_llm_agent_once(codegen, user_text=user_cg)
            except Exception as e:
                print(f"        Codegen failed (attempt {attempt}): {e}")
                break

            st = static_critic(source, max_source_bytes=settings.automanim_max_source_bytes)
            if not st.ok:
                revision = st.feedback
                continue

            scene_dir = lec_dir / f"{idx:02d}-{_slug(scene.title)}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            dest = scene_dir / "scene.mp4"
            try:
                art = await backend.render_scene(source, dest)
            except Exception as e:
                print(f"        Render exception: {e}")
                break

            if art.exit_code == 0 and art.artifact_path:
                results.append(
                    {
                        "chunk_id": chunk.id,
                        "scene_hint": chunk.scene_hint,
                        "scene": art.scene_name,
                        "path": art.artifact_path,
                        "start_ms": chunk.start_ms,
                        "end_ms": chunk.end_ms,
                    }
                )
            else:
                print(f"        Render failed (exit {art.exit_code}): {art.stderr_tail[:200]}")
            break
        else:
            print(f"        Critic rejected after {max_att} attempt(s).")

    return results


async def _run(args: argparse.Namespace) -> int:
    s = load_settings()

    out_root: Path
    if args.out:
        out_root = Path(args.out).expanduser().resolve()
    else:
        today = date.today().isoformat()
        sl = _slug(args.topic[:60])
        out_root = Path("content") / "ir" / "series" / f"{today}-{sl}"
        out_root = out_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    enable_tts: bool = args.tts and s.tts_enabled
    enable_manim: bool = args.manim

    if args.tts and not s.tts_enabled:
        print("TTS: set tts_enabled=true in profile to enable audio synthesis.")

    audio_dir = out_root / "audio"
    video_dir = out_root / "videos"
    if enable_tts:
        audio_dir.mkdir(parents=True, exist_ok=True)
    if enable_manim:
        video_dir.mkdir(parents=True, exist_ok=True)

    client = AsyncClient(host=s.ollama_url.rstrip("/"))

    tts = None
    if enable_tts:
        from educlaw.tts.registry import build_backend
        tts = build_backend(s)
        if tts is None:
            print("TTS backend unavailable; skipping audio.")
            enable_tts = False

    n = max(2, min(8, args.lectures))
    user = (
        f"Plan a course with exactly {n} lectures (all {n}, not fewer). "
        f"Audience: general learners. Topic:\n{args.topic.strip()}"
    )

    manifest: dict[str, Any] = {
        "topic": args.topic,
        "lecture_count": n,
        "output_dir": str(out_root),
        "tts": enable_tts,
        "manim": enable_manim,
        "lectures": [],
    }
    errors: list[dict[str, Any]] = []
    exit_code = 0

    try:
        try:
            plan = await plan_course(client, s, user)
        except CoursePlanningFailed as e:
            print(f"Planning failed: {e}")
            return 1

        lectures = plan.lectures[:n]
        (out_root / "course-plan.json").write_text(
            json.dumps(
                {"title": plan.title, "audience": plan.audience, "lecture_count": len(lectures)},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"Plan: {plan.title}  ({len(lectures)} lectures)")

        prior_titles: list[str] = []
        n_lec = len(lectures)

        for i, outline in enumerate(lectures, start=1):
            print(f"\n  [{i}/{n_lec}] {outline.title}")
            row: dict[str, Any] = {"index": i, "title": outline.title}

            # --- 1. Generate markdown ---
            try:
                result = await generate_lecture(
                    client,
                    s.model_id,
                    outline,
                    course_title=plan.title,
                    lecture_index=i,
                    lecture_count=n_lec,
                    prior_lecture_titles=list(prior_titles),
                    think=s.ollama_chat_think,
                )
            except Exception as e:
                msg = str(e)
                print(f"    Markdown generation failed: {msg}")
                row["error"] = msg
                errors.append({"index": i, "stage": "markdown", "error": msg})
                manifest["lectures"].append(row)
                if not args.continue_on_error:
                    exit_code = 1
                    break
                continue

            prior_titles.append(outline.title)
            meta = dict(result.ir_suggestion) if result.ir_suggestion else {}
            post = frontmatter.Post(result.markdown, **meta)
            lec_slug = _slug(outline.title or f"lec-{i}")
            node_id = str(meta.get("id") or lec_slug)
            md_path = out_root / f"lecture-{i:02d}-{lec_slug}.md"
            md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
            print(f"    Wrote {md_path.name}")
            row["markdown"] = md_path.name

            # --- 2. Generate unified IR (TTS text + animation specs) ---
            ir_path = out_root / f"lecture-{i:02d}-ir.json"
            try:
                ir = await markdown_to_lecture_ir(
                    client,
                    s.model_id,
                    result.markdown,
                    lecture_id=node_id,
                    title=outline.title,
                    think=s.ollama_chat_think,
                )
                ir_path.write_text(ir.model_dump_json(indent=2), encoding="utf-8")
                n_chunks = len(ir.chunks)
                n_anim = len(ir.animation_chunks())
                print(f"    IR: {n_chunks} chunks, {n_anim} with animation → {ir_path.name}")
                row["ir"] = ir_path.name
            except Exception as e:
                msg = str(e)
                print(f"    IR generation failed: {msg}")
                row["ir_error"] = msg
                errors.append({"index": i, "stage": "ir", "error": msg})
                manifest["lectures"].append(row)
                if not args.continue_on_error:
                    exit_code = 1
                    break
                continue

            # --- 3. TTS synthesis from IR ---
            if enable_tts and tts is not None:
                wav_path = audio_dir / f"lecture-{i:02d}.wav"
                srt_path = audio_dir / f"lecture-{i:02d}.srt"
                vtt_path = audio_dir / f"lecture-{i:02d}.vtt"
                try:
                    wav_bytes, ir_timed = await synthesize_from_ir(
                        tts,
                        ir,
                        voice=s.tts_voice,
                        speed=float(s.tts_speed),
                        sample_rate=int(s.tts_sample_rate),
                    )
                    wav_path.write_bytes(wav_bytes)
                    srt_path.write_text(ir_timed.to_srt(), encoding="utf-8")
                    vtt_path.write_text(ir_timed.to_vtt(), encoding="utf-8")
                    # update IR file with timestamps
                    ir_path.write_text(ir_timed.model_dump_json(indent=2), encoding="utf-8")
                    row["audio"] = str(wav_path.relative_to(out_root))
                    row["srt"] = str(srt_path.relative_to(out_root))
                    print(f"    Audio: {wav_path.name} ({len(wav_bytes):,} bytes)")
                except Exception as e:
                    msg = str(e)
                    print(f"    TTS error: {msg}")
                    row["tts_error"] = msg
                    errors.append({"index": i, "stage": "tts", "error": msg})

            # --- 4. Manim scenes from IR animation specs ---
            if enable_manim:
                try:
                    manim_settings = s.model_copy(
                        update={
                            "automanim_enabled": True,
                            "automanim_output_dir": video_dir,
                            "shield_enabled": False,
                        }
                    )
                    scenes = await _render_manim_from_ir(ir, video_dir, manim_settings, client)
                    if scenes:
                        row["manim_scenes"] = scenes
                        print(f"    Manim: {len(scenes)} scene(s) rendered")
                except Exception as e:
                    msg = str(e)
                    print(f"    Manim error: {msg}")
                    row["manim_error"] = msg
                    errors.append({"index": i, "stage": "manim", "error": msg})

            manifest["lectures"].append(row)

        else:
            print("\nDone.")

    finally:
        manifest_path = out_root / "pipeline-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if errors:
            (out_root / "pipeline-errors.json").write_text(
                json.dumps(errors, indent=2) + "\n", encoding="utf-8"
            )

        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            await aclose()
        if tts is not None:
            await tts.close()

    print(f"\nArtifacts: {out_root}")
    return exit_code


def main() -> None:
    p = argparse.ArgumentParser(
        description="Prompt → markdown lectures → unified IR JSON → audio + video."
    )
    p.add_argument("topic", help="What to teach (e.g. 'Real Analysis', 'Gradient Descent')")
    p.add_argument("--lectures", type=int, default=4, metavar="N",
                   help="Number of lectures to generate (2–8, default 4)")
    p.add_argument("--out", type=Path, default=None,
                   help="Output directory (default: content/ir/series/YYYY-MM-DD-slug)")
    p.add_argument("--tts", action=argparse.BooleanOptionalAction, default=True,
                   help="Synthesize audio from IR (requires tts_enabled in profile)")
    p.add_argument("--manim", action=argparse.BooleanOptionalAction, default=False,
                   help="Render Manim scenes from IR animation specs")
    p.add_argument("--continue-on-error", action="store_true",
                   help="Keep going if a lecture/IR/TTS step fails")
    args = p.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
