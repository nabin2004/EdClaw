"""Shared course pipeline: plan → lectures → subtitles+TTS → Manim.

Pipeline runs in three sequential phases so that a failure in one phase for one
lecture never blocks the remaining lectures or later phases:

  Phase 1 – Plan the course and generate ALL lecture Markdown files.
  Phase 2 – LLM segments each lecture into subtitle blocks (industry-standard
             15-20 CPS, max 2 lines / 42 chars per line, 3-7 s per block),
             synthesises per-block TTS audio, and writes SRT + VTT.
  Phase 3 – Run AutoManim on each lecture using subtitle blocks as timing anchors.

Within every phase, errors are caught per-lecture, logged, and skipped so the
pipeline always makes as much progress as possible.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter
from ollama import AsyncClient

from educlaw.autocourse.orchestrator import CoursePlanningFailed, plan_course
from educlaw.autolecture.generator import generate_lecture
from educlaw.automanim.orchestrator import run_automanim
from educlaw.config.settings import Settings, load_settings
from educlaw.safety.shield import NoopShield, Shield
from educlaw.tts.md_to_srt import SubtitleBlock, blocks_to_srt, blocks_to_vtt, estimate_timing, segment_markdown, synthesize_blocks
from educlaw.tts.registry import build_backend


# ---------------------------------------------------------------------------
# Slug / WAV utilities (also re-exported for the CLI script)
# ---------------------------------------------------------------------------

def slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "course"


# ---------------------------------------------------------------------------
# Pipeline config
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    topic: str
    lectures: int = 4
    out: Path | None = None
    enable_tts: bool = True
    enable_automanim: bool = True
    enable_shield: bool = True
    automanim_output_dir: Path | None = None
    automanim_backend: str | None = None
    continue_on_error: bool = True
    generate_site: bool = False
    site_output_dir: Path | None = None


# ---------------------------------------------------------------------------
# Phased pipeline runner
# ---------------------------------------------------------------------------

# Internal record shared across phases
_LecRecord = dict[str, Any]


async def run_pipeline(
    cfg: PipelineConfig,
    settings: Settings | None = None,
) -> tuple[int, Path]:
    """Run the full phased pipeline.

    Returns ``(exit_code, output_dir)``.
    exit_code is 0 on full success, 1 if any stage of any lecture failed.
    """
    out_root = cfg.out
    if out_root is None:
        today = date.today().isoformat()
        sl = slug(cfg.topic[:60])
        out_root = Path("content") / "courses" / f"{today}-{sl}"
    out_root = out_root.expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    settings_updates: dict[str, Any] = {
        "automanim_enabled": cfg.enable_automanim,
        "shield_enabled": cfg.enable_shield,
    }
    if cfg.enable_automanim:
        vdir = cfg.automanim_output_dir or (out_root / "videos")
        vdir = vdir.expanduser().resolve()
        vdir.mkdir(parents=True, exist_ok=True)
        settings_updates["automanim_output_dir"] = vdir
    if cfg.automanim_backend is not None:
        settings_updates["automanim_backend"] = cfg.automanim_backend

    s = (settings or load_settings()).model_copy(update=settings_updates)
    n = max(2, min(8, cfg.lectures))

    tts = None
    if cfg.enable_tts and s.tts_enabled:
        tts = build_backend(s)
        if tts is None:
            print("TTS: backend unavailable; skipping audio.")
    elif cfg.enable_tts and not s.tts_enabled:
        print("TTS: set tts_enabled=true in profile. Skipping audio.")

    client = AsyncClient(host=s.ollama_url.rstrip("/"))
    audio_dir = out_root / "audio"

    shield_impl: Shield | NoopShield = (
        Shield(client, model=s.shield_model) if cfg.enable_shield else NoopShield()
    )

    manim_clips: list[dict[str, object]] = []
    lecture_rows: list[_LecRecord] = []
    pipeline_errors: list[dict[str, Any]] = []
    exit_code = 0

    manifest: dict[str, object] = {
        "topic": cfg.topic,
        "lecture_count": n,
        "output_dir": str(out_root),
        "automanim": s.automanim_enabled,
        "tts": tts is not None,
        "shield_ollama": cfg.enable_shield,
        "manim_artifacts": manim_clips,
        "lectures": lecture_rows,
    }

    async def _close_client() -> None:
        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            await aclose()
            return
        close = getattr(client, "close", None)
        if callable(close):
            out = close()
            if asyncio.iscoroutine(out):
                await out

    def _err(lecture_index: int, stage: str, msg: str) -> None:
        nonlocal exit_code
        exit_code = 1
        pipeline_errors.append({"lecture_index": lecture_index, "stage": stage, "error": msg})
        print(f"  [lec {lecture_index:02d}][{stage}] ERROR: {msg}")

    # Phase 1 output: (lecture_index, outline, raw_markdown, md_path)
    generated: list[tuple] = []
    # Phase 2 output: (lecture_index, outline, raw_markdown, subtitle_blocks)
    subtitled: list[tuple] = []

    try:
        # ── Phase 1: Plan + all lecture Markdown files ─────────────────────────
        print(f"\n=== Phase 1: Planning and generating {n} lecture Markdown files ===")
        plan_user = (
            f"Plan a course with exactly {n} lectures (all {n}, not fewer). "
            f"Audience: general learners. Topic:\n{cfg.topic.strip()}"
        )
        try:
            plan = await plan_course(client, s, plan_user)
        except CoursePlanningFailed as e:
            print(f"Course planning failed: {e}")
            if e.raw_preview:
                print(f"(raw preview) {e.raw_preview[:200]}…")
            exit_code = 1
            return exit_code, out_root

        lectures = plan.lectures[:n]
        (out_root / "course-plan.json").write_text(
            json.dumps(
                {"title": plan.title, "audience": plan.audience, "lecture_count": len(lectures)},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        manifest["lecture_count"] = len(lectures)
        print(f"Plan: {plan.title!r}  ({len(lectures)} lectures)")

        prior_titles: list[str] = []
        n_lec = len(lectures)
        for i, outline in enumerate(lectures, start=1):
            row: _LecRecord = {"lecture_index": i, "lecture_title": outline.title}
            lecture_rows.append(row)
            print(f"  [{i}/{n_lec}] {outline.title}")
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
                _err(i, "lecture", str(e))
                row["error"] = str(e)
                continue

            prior_titles.append(outline.title)
            meta = dict(result.ir_suggestion) if result.ir_suggestion else {}
            post = frontmatter.Post(result.markdown, **meta)
            lec_slug = slug(outline.title or f"lec-{i}", 48)
            md_path = out_root / f"lecture-{i:02d}-{lec_slug}.md"
            md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
            row["markdown"] = str(md_path.relative_to(out_root))
            print(f"    Wrote {md_path.name}")
            generated.append((i, outline, result.markdown, md_path))

        print(
            f"Phase 1 complete: {len(generated)}/{n_lec} lecture(s) written"
            + (f"  ({n_lec - len(generated)} failed)" if len(generated) < n_lec else "")
        )

        # ── Phase 2: Subtitle segmentation + TTS ──────────────────────────────
        print(
            f"\n=== Phase 2: Subtitle segmentation"
            f"{' + TTS' if tts is not None else ' (TTS disabled)'}"
            f" for {len(generated)} lecture(s) ==="
        )
        if tts is not None:
            audio_dir.mkdir(parents=True, exist_ok=True)

        sub_ok = 0
        for i, outline, raw_md, md_path in generated:
            row = lecture_rows[i - 1]
            try:
                segments = await segment_markdown(
                    client,
                    s.model_id,
                    raw_md,
                    think=s.ollama_chat_think,
                )
                if not segments:
                    raise ValueError("LLM returned empty subtitle segment list.")

                if tts is not None:
                    blocks, wav_bytes = await synthesize_blocks(
                        tts,
                        segments,
                        voice=s.tts_voice,
                        speed=float(s.tts_speed),
                        sample_rate=int(s.tts_sample_rate),
                    )
                    wav_path = audio_dir / f"lecture-{i:02d}.wav"
                    srt_path = audio_dir / f"lecture-{i:02d}.srt"
                    vtt_path = audio_dir / f"lecture-{i:02d}.vtt"
                    wav_path.write_bytes(wav_bytes)
                    srt_path.write_text(blocks_to_srt(blocks), encoding="utf-8")
                    vtt_path.write_text(blocks_to_vtt(blocks), encoding="utf-8")
                    row["audio"] = str(wav_path.relative_to(out_root))
                    row["audio_srt"] = str(srt_path.relative_to(out_root))
                    row["audio_vtt"] = str(vtt_path.relative_to(out_root))
                    print(
                        f"  [{i:02d}] {wav_path.name}"
                        f"  ({len(wav_bytes)} bytes, {len(blocks)} subtitle blocks)"
                    )
                else:
                    blocks = estimate_timing(segments)
                    print(f"  [{i:02d}] {len(blocks)} subtitle block(s) (timing estimated)")

                subtitled.append((i, outline, raw_md, blocks))
                sub_ok += 1
            except Exception as e:
                _err(i, "subtitles", str(e))
                row["subtitle_error"] = str(e)

        print(
            f"Phase 2 complete: {sub_ok}/{len(generated)} lecture(s) subtitled"
            + (f"  ({len(generated) - sub_ok} failed)" if sub_ok < len(generated) else "")
        )

        # ── Phase 3: AutoManim from subtitle blocks ────────────────────────────
        if s.automanim_enabled:
            print(f"\n=== Phase 3: Manim video generation for {len(subtitled)} lecture(s) ===")
            manim_ok = 0
            for i, outline, raw_md, subtitle_blocks in subtitled:
                row = lecture_rows[i - 1]
                scenes: list[dict[str, object]] = []
                try:
                    async for am_ev in run_automanim(
                        raw_md,
                        subtitle_blocks,
                        outline.title,
                        s,
                        shield_impl,
                        ollama=client,
                        output_root=s.automanim_output_dir,
                    ):
                        if (
                            am_ev.kind == "scene_done"
                            and am_ev.artifact
                            and am_ev.artifact.artifact_path
                        ):
                            rec: dict[str, object] = {
                                "lecture_index": i,
                                "lecture_title": outline.title,
                                "path": am_ev.artifact.artifact_path,
                                "scene": am_ev.artifact.scene_name,
                            }
                            scenes.append(rec)
                            manim_clips.append(rec)
                            print(f"  [{i:02d}] scene {am_ev.artifact.scene_name}: {am_ev.artifact.artifact_path}")
                        elif am_ev.kind == "error" and am_ev.message:
                            print(f"  [{i:02d}] Manim scene error: {am_ev.message}")
                    if scenes:
                        manim_ok += 1
                except Exception as e:
                    _err(i, "automanim", str(e))
                    row["manim_error"] = str(e)

                if scenes:
                    row["manim_scenes"] = scenes

            print(
                f"Phase 3 complete: {manim_ok}/{len(subtitled)} lecture(s) produced Manim clips"
                + (f"  ({len(subtitled) - manim_ok} failed or no scenes)" if manim_ok < len(subtitled) else "")
            )
        else:
            print("\n=== Phase 3: AutoManim skipped (disabled) ===")

        if exit_code == 0:
            print("\nDone: all phases completed without errors.")

    finally:
        manifest["manim_artifacts"] = manim_clips
        manifest["lectures"] = lecture_rows
        manifest["exit_code"] = exit_code
        (out_root / "pipeline-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        if pipeline_errors:
            from datetime import datetime

            error_doc = {
                "run_timestamp": datetime.now().isoformat(timespec="seconds"),
                "topic": cfg.topic,
                "total_errors": len(pipeline_errors),
                "errors": pipeline_errors,
            }
            (out_root / "pipeline-errors.json").write_text(
                json.dumps(error_doc, indent=2) + "\n", encoding="utf-8"
            )
            log_lines = [
                f"[{error_doc['run_timestamp']}] topic={cfg.topic!r}\n"
            ] + [
                f"  lec {e['lecture_index']:02d} | stage={e['stage']} | {e['error']}\n"
                for e in pipeline_errors
            ]
            with (out_root / "pipeline-errors.log").open("a", encoding="utf-8") as lf:
                lf.writelines(log_lines)
        await _close_client()
        if tts is not None:
            await tts.close()

    if cfg.generate_site:
        try:
            from educlaw.sitegen.generator import generate_site

            site_path = generate_site(out_root, output_dir=cfg.site_output_dir)
            print(f"Site generated at: {site_path}")
        except Exception as e:
            print(f"Site generation failed: {e!s}")
            exit_code = 1

    print(f"\nArtifacts under: {out_root}")
    return exit_code, out_root
