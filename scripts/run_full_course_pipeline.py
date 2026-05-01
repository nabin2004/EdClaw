#!/usr/bin/env python3
"""
End-to-end course generator: plan → per lecture: Markdown → WAV (optional) → Manim (optional).

Within each lecture the order is strict: write ``lecture-NN-*.md``, then ``audio/lecture-NN.wav``
(if TTS is on), then AutoManim scenes under ``videos/`` before the next lecture starts.

Reads ``profiles/local.toml`` (or ``EDUCLAW_PROFILE_PATH``). Requires Ollama.

Examples:
  .venv/bin/python scripts/run_full_course_pipeline.py \\
    "Introduction to linear algebra" --lectures 8

  .venv/bin/python scripts/run_full_course_pipeline.py \\
    "Python basics" --lectures 2 --out content/ir/series/my-run --no-automanim

  .venv/bin/python scripts/run_full_course_pipeline.py "Topic" --no-tts --no-automanim --no-shield
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import tempfile
import wave
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter
from ollama import AsyncClient

from educlaw.autocourse.orchestrator import CoursePlanningFailed, plan_course
from educlaw.autolecture.generator import generate_lecture
from educlaw.automanim.orchestrator import run_automanim
from educlaw.config.settings import load_settings
from educlaw.safety.shield import NoopShield, Shield
from educlaw.tts.contract import TTSRequest
from educlaw.tts.registry import build_backend


def _slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "course"


def _tts_plain_text(markdown: str, max_chars: int) -> str:
    t = re.sub(r"```[\s\S]*?```", " ", markdown)
    t = re.sub(r"#{1,6}\s*", "", t)
    t = re.sub(r"[*_`]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_chars]


def _chunk_words(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    out: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if cur and cur_len + add > max_chars:
            out.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += add
    if cur:
        out.append(" ".join(cur))
    return out


def _wav_sig(path: Path) -> tuple[int, int, int, str, str]:
    with wave.open(str(path), "rb") as w:
        p = w.getparams()
        return (p.nchannels, p.sampwidth, p.framerate, p.comptype, p.compname)


def _concat_wav_files(paths: list[Path], dest: Path) -> None:
    if not paths:
        raise ValueError("no WAV paths")
    if len(paths) == 1:
        shutil.copy2(paths[0], dest)
        return
    sig0 = _wav_sig(paths[0])
    frames: list[bytes] = []
    with wave.open(str(paths[0]), "rb") as w0:
        frames.append(w0.readframes(w0.getnframes()))
    for p in paths[1:]:
        if _wav_sig(p) != sig0:
            raise RuntimeError(f"WAV format mismatch: {p} vs {paths[0]}")
        with wave.open(str(p), "rb") as w:
            frames.append(w.readframes(w.getnframes()))
    nch, sw, fr, ct, cn = sig0
    with wave.open(str(dest), "wb") as out:
        out.setnchannels(nch)
        out.setsampwidth(sw)
        out.setframerate(fr)
        out.setcomptype(ct, cn)
        for f in frames:
            out.writeframes(f)


async def _synthesize_lecture_wav(
    tts: Any,
    text: str,
    *,
    chunk_chars: int,
    voice: str | None,
    speed: float,
    sample_rate: int,
) -> bytes:
    chunks = _chunk_words(text, chunk_chars)
    if not chunks:
        raise ValueError("empty TTS text")
    with tempfile.TemporaryDirectory(prefix="educlaw_tts_") as td:
        tmp = Path(td)
        paths: list[Path] = []
        for i, ch in enumerate(chunks):
            req = TTSRequest(
                text=ch,
                voice=voice,
                speed=speed,
                sample_rate=sample_rate,
            )
            audio = await tts.synthesize(req)
            p = tmp / f"chunk_{i:04d}.wav"
            p.write_bytes(audio.audio_bytes)
            paths.append(p)
        merged = tmp / "merged.wav"
        _concat_wav_files(paths, merged)
        return merged.read_bytes()


async def _run(args: argparse.Namespace) -> int:
    out_root = args.out
    if out_root is None:
        today = date.today().isoformat()
        slug = _slug(args.topic[:60])
        out_root = (
            Path(__file__).resolve().parents[1] / "content" / "ir" / "series" / f"{today}-{slug}"
        )
    out_root = out_root.expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    settings_updates: dict[str, Any] = {
        "automanim_enabled": bool(args.automanim),
        "shield_enabled": bool(args.shield),
    }
    if args.automanim:
        vdir = args.automanim_output_dir
        if vdir is None:
            vdir = out_root / "videos"
        vdir = vdir.expanduser().resolve()
        vdir.mkdir(parents=True, exist_ok=True)
        settings_updates["automanim_output_dir"] = vdir
    if args.automanim_backend is not None:
        settings_updates["automanim_backend"] = args.automanim_backend
    settings = load_settings().model_copy(update=settings_updates)

    n = max(2, min(8, args.lectures))
    user = (
        f"Plan a course with exactly {n} lectures (all {n}, not fewer). "
        f"Audience: general learners. Topic:\n{args.topic.strip()}"
    )

    tts = None
    if args.tts and settings.tts_enabled:
        tts = build_backend(settings)
        if tts is None:
            print("TTS: disabled in settings; skipping audio.")
    elif args.tts and not settings.tts_enabled:
        print("TTS: set tts_enabled=true in profile (or use --no-tts). Skipping audio.")

    client = AsyncClient(host=settings.ollama_url.rstrip("/"))
    audio_dir = out_root / "audio"
    if tts is not None:
        audio_dir.mkdir(parents=True, exist_ok=True)

    shield_impl: Shield | NoopShield = (
        Shield(client, model=settings.shield_model) if args.shield else NoopShield()
    )

    manim_clips: list[dict[str, object]] = []
    lecture_rows: list[dict[str, Any]] = []
    exit_code = 0

    manifest: dict[str, object] = {
        "topic": args.topic,
        "lecture_count": n,
        "output_dir": str(out_root),
        "automanim": settings.automanim_enabled,
        "tts": tts is not None,
        "shield_ollama": bool(args.shield),
        "manim_artifacts": manim_clips,
        "lectures": lecture_rows,
    }

    async def _maybe_close_ollama() -> None:
        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            await aclose()  # type: ignore[misc]
            return
        close = getattr(client, "close", None)
        if callable(close):
            out = close()
            if asyncio.iscoroutine(out):
                await out  # type: ignore[misc]

    try:
        try:
            plan = await plan_course(client, settings, user)
        except CoursePlanningFailed as e:
            print(f"Error: {e}")
            if e.raw_preview:
                print(f"(raw preview) {e.raw_preview[:200]}…")
            exit_code = 1
        else:
            lectures = plan.lectures[:n]
            plan_payload = {
                "title": plan.title,
                "audience": plan.audience,
                "lecture_count": len(lectures),
            }
            (out_root / "course-plan.json").write_text(
                json.dumps(plan_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest["lecture_count"] = len(lectures)
            print(f"Plan: {plan.title} ({len(lectures)} lectures)")

            prior_titles: list[str] = []
            n_lec = len(lectures)

            for i, outline in enumerate(lectures, start=1):
                print(f"  Lecture {i}/{n_lec}: {outline.title}")
                row: dict[str, Any] = {
                    "lecture_index": i,
                    "lecture_title": outline.title,
                }

                try:
                    result = await generate_lecture(
                        client,
                        settings.model_id,
                        outline,
                        course_title=plan.title,
                        lecture_index=i,
                        lecture_count=n_lec,
                        prior_lecture_titles=list(prior_titles),
                    )
                except Exception as e:  # noqa: BLE001
                    print(f"  Lecture generation failed: {e!s}")
                    row["error"] = str(e)
                    lecture_rows.append(row)
                    if not args.continue_on_error:
                        exit_code = 1
                        break
                    continue

                prior_titles.append(outline.title)
                meta = dict(result.ir_suggestion) if result.ir_suggestion else {}
                post = frontmatter.Post(result.markdown, **meta)
                lec_slug = _slug(outline.title or f"lec-{i}", 48)
                md_path = out_root / f"lecture-{i:02d}-{lec_slug}.md"
                md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
                print(f"  Wrote {md_path.name}")
                row["markdown"] = str(md_path.relative_to(out_root))

                if tts is not None:
                    text = _tts_plain_text(result.markdown, args.tts_max_chars)
                    try:
                        wav_bytes = await _synthesize_lecture_wav(
                            tts,
                            text,
                            chunk_chars=args.tts_chunk_chars,
                            voice=settings.tts_voice,
                            speed=float(settings.tts_speed),
                            sample_rate=int(settings.tts_sample_rate),
                        )
                        wav = audio_dir / f"lecture-{i:02d}.wav"
                        wav.write_bytes(wav_bytes)
                        print(f"  TTS: {wav.name} ({len(wav_bytes)} bytes)")
                        row["audio"] = str(wav.relative_to(out_root))
                    except Exception as e:  # noqa: BLE001
                        print(f"  TTS error: {e!s}")
                        row["audio_error"] = str(e)

                scenes: list[dict[str, object]] = []
                if settings.automanim_enabled:
                    try:
                        async for am_ev in run_automanim(
                            result.markdown,
                            dict(result.ir_suggestion),
                            settings,
                            shield_impl,
                            ollama=client,
                            output_root=settings.automanim_output_dir,
                        ):
                            if (
                                am_ev.kind == "scene_done"
                                and am_ev.artifact
                                and am_ev.artifact.artifact_path
                            ):
                                ap = am_ev.artifact.artifact_path
                                rec = {
                                    "lecture_index": i,
                                    "lecture_title": outline.title,
                                    "path": ap,
                                    "scene": am_ev.artifact.scene_name,
                                }
                                scenes.append(rec)
                                manim_clips.append(rec)
                                print(f"  Manim: {ap}")
                            elif am_ev.kind == "error" and am_ev.message:
                                print(f"  Manim error: {am_ev.message}")
                    except Exception as e:  # noqa: BLE001
                        msg = f"AutoManim failed: {e!s}"
                        print(f"  {msg}")
                        row["manim_error"] = str(e)
                        if not args.continue_on_error:
                            exit_code = 1
                            lecture_rows.append(row)
                            break
                if scenes:
                    row["manim_scenes"] = scenes

                lecture_rows.append(row)
            else:
                if exit_code == 0:
                    print("Done: pipeline finished.")

    finally:
        manifest["manim_artifacts"] = manim_clips
        manifest["lectures"] = lecture_rows
        manifest["exit_code"] = exit_code
        (out_root / "pipeline-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        await _maybe_close_ollama()
        if tts is not None:
            await tts.close()

    if args.generate_site and exit_code == 0:
        try:
            from educlaw.sitegen.generator import generate_site

            site_path = generate_site(out_root, output_dir=args.site_output_dir)
            print(f"Site generated at: {site_path}")
        except Exception as e:  # noqa: BLE001
            print(f"Site generation failed: {e!s}")
            if not args.continue_on_error:
                exit_code = 1

    print(f"\nArtifacts under: {out_root}")
    return exit_code


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run plan + per-lecture Markdown, optional chunked TTS, optional AutoManim "
            "(see module docstring)."
        ),
    )
    p.add_argument(
        "topic",
        help="What to teach (passed to the course planner).",
    )
    p.add_argument(
        "--lectures",
        type=int,
        default=4,
        metavar="N",
        help="Exact number of lectures to plan (2–8, default 4).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: content/ir/series/YYYY-MM-DD-slug).",
    )
    p.add_argument(
        "--automanim",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable AutoManim after each lecture (default: on).",
    )
    p.add_argument(
        "--automanim-output-dir",
        type=Path,
        default=None,
        dest="automanim_output_dir",
        help="Override automanim output dir (default: <out>/videos).",
    )
    p.add_argument(
        "--automanim-backend",
        choices=("local", "docker"),
        default=None,
        dest="automanim_backend",
        help="Override automanim render backend.",
    )
    p.add_argument(
        "--tts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Synthesize WAV per lecture if tts_enabled in profile (default: on).",
    )
    p.add_argument(
        "--shield",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run Ollama Shield before AutoManim scenes (default: on). Use --no-shield to skip.",
    )
    p.add_argument(
        "--tts-max-chars",
        type=int,
        default=12_000,
        dest="tts_max_chars",
        help="Max plain-text characters taken from each lecture before chunking (default 12000).",
    )
    p.add_argument(
        "--tts-chunk-chars",
        type=int,
        default=320,
        dest="tts_chunk_chars",
        help="Max characters per TTS call (chunked then merged to one WAV; default 320).",
    )
    p.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Do not exit on first lecture / TTS / AutoManim failure.",
    )
    p.add_argument(
        "--generate-site",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="generate_site",
        help="Generate a Jekyll course site after finishing (default: off).",
    )
    p.add_argument(
        "--site-output-dir",
        type=Path,
        default=None,
        dest="site_output_dir",
        help="Parent directory for the generated site (default: sites/).",
    )
    return p


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
