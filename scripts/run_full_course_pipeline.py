#!/usr/bin/env python3
"""
End-to-end: autocourse (plan + autolecture) → optional AutoManim → optional TTS.

Reads ``profiles/local.toml`` (or ``EDUCLAW_PROFILE_PATH``). Requires Ollama.
AutoManim and TTS use your profile flags unless overridden by CLI.

Examples:
  .venv/bin/python scripts/run_full_course_pipeline.py \\
    "Introduction to linear algebra for beginners" --lectures 4

  EDUCLAW_AUTOMANIM_ENABLED=true .venv/bin/python scripts/run_full_course_pipeline.py \\
    "Python basics" --lectures 2 --out content/ir/series/my-run

  .venv/bin/python scripts/run_full_course_pipeline.py "Topic" --no-automanim --no-tts
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

from educlaw.autocourse.orchestrator import run_autocourse
from educlaw.config.settings import load_settings
from educlaw.safety.shield import Shield, Verdict
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

    settings_updates: dict[str, Any] = {"automanim_enabled": bool(args.automanim)}
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

    manifest: dict[str, object] = {
        "topic": args.topic,
        "lecture_count": n,
        "output_dir": str(out_root),
        "automanim": settings.automanim_enabled,
        "tts": tts is not None,
    }
    manim_clips: list[dict[str, object]] = []
    exit_code = 0

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
        if args.shield_dry_run:
            v = await Shield(client, model=settings.shield_model).classify(user)
            if v == Verdict.BLOCK:
                print("Shield: BLOCK — aborting before generation.")
                exit_code = 2
            else:
                print(f"Shield: {v} — continuing.")

        if exit_code == 0:
            async for ev in run_autocourse(user, settings, client):
                if ev.kind == "plan":
                    plan_payload = {
                        "title": ev.course_title,
                        "audience": ev.audience,
                        "lecture_count": ev.lecture_count,
                    }
                    (out_root / "course-plan.json").write_text(
                        json.dumps(plan_payload, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    print(f"Plan: {ev.course_title} ({ev.lecture_count} lectures)")

                elif ev.kind == "lecture_start":
                    print(
                        f"  Lecture {ev.lecture_index}/{ev.lecture_count}: {ev.lecture_title}",
                    )

                elif ev.kind == "lecture_done" and ev.result is not None:
                    r = ev.result
                    meta = dict(r.ir_suggestion) if r.ir_suggestion else {}
                    post = frontmatter.Post(r.markdown, **meta)
                    lec_slug = _slug(ev.lecture_title or f"lec-{ev.lecture_index}", 48)
                    md_path = out_root / f"lecture-{ev.lecture_index:02d}-{lec_slug}.md"
                    md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
                    print(f"  Wrote {md_path.name}")

                    if tts is not None and ev.lecture_index is not None:
                        text = _tts_plain_text(r.markdown, args.tts_max_chars)
                        try:
                            wav_bytes = await _synthesize_lecture_wav(
                                tts,
                                text,
                                chunk_chars=args.tts_chunk_chars,
                                voice=settings.tts_voice,
                                speed=float(settings.tts_speed),
                                sample_rate=int(settings.tts_sample_rate),
                            )
                            wav = audio_dir / f"lecture-{ev.lecture_index:02d}.wav"
                            wav.write_bytes(wav_bytes)
                            print(f"  TTS: {wav.name} ({len(wav_bytes)} bytes)")
                        except Exception as e:  # noqa: BLE001
                            print(f"  TTS error: {e!s}")

                elif ev.kind == "automanim" and ev.automanim is not None:
                    am = ev.automanim
                    if am.kind == "scene_done" and am.artifact and am.artifact.artifact_path:
                        manim_clips.append(
                            {
                                "lecture_index": ev.lecture_index,
                                "lecture_title": ev.lecture_title,
                                "path": am.artifact.artifact_path,
                                "scene": am.artifact.scene_name,
                            },
                        )
                        print(f"  Manim: {am.artifact.artifact_path}")
                    elif am.kind == "error" and am.message:
                        print(f"  Manim error: {am.message}")

                elif ev.kind == "error":
                    print(f"Error: {ev.message}")
                    if (ev.message or "").startswith("AutoManim failed"):
                        continue
                    if not args.continue_on_error:
                        exit_code = 1
                        break

                elif ev.kind == "done":
                    print("Done:", ev.message or "")

    finally:
        manifest["manim_artifacts"] = manim_clips
        manifest["exit_code"] = exit_code
        (out_root / "pipeline-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        await _maybe_close_ollama()
        if tts is not None:
            await tts.close()

    print(f"\nArtifacts under: {out_root}")
    return exit_code


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run autocourse + autolecture, optional AutoManim and TTS (see module docstring)."
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
        help="Enable AutoManim (sets automanim_enabled; default: on).",
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
        help="Do not exit on first autocourse/lecture error.",
    )
    p.add_argument(
        "--shield-dry-run",
        action="store_true",
        help="If Shield blocks the topic, exit before Ollama course planning.",
    )
    return p


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
