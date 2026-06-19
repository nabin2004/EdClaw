"""Shared course pipeline: plan → lectures → TTS → AutoManim.

Used by both ``educlaw autocourse generate`` and ``scripts/run_full_course_pipeline.py``.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import tempfile
import wave
from dataclasses import dataclass, field
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
from educlaw.tts.contract import TTSRequest
from educlaw.tts.registry import build_backend


# ---------------------------------------------------------------------------
# Slug / TTS utilities (also re-exported for the script)
# ---------------------------------------------------------------------------

def slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "course"


def tts_plain_text(markdown: str, max_chars: int) -> str:
    t = re.sub(r"```[\s\S]*?```", " ", markdown)
    t = re.sub(r"#{1,6}\s*", "", t)
    t = re.sub(r"[*_`]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_chars]


def chunk_words(text: str, max_chars: int) -> list[str]:
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


def wav_sig(path: Path) -> tuple[int, int, int, str, str]:
    with wave.open(str(path), "rb") as w:
        p = w.getparams()
        return (p.nchannels, p.sampwidth, p.framerate, p.comptype, p.compname)


def concat_wav_files(paths: list[Path], dest: Path) -> None:
    if not paths:
        raise ValueError("no WAV paths")
    if len(paths) == 1:
        shutil.copy2(paths[0], dest)
        return
    sig0 = wav_sig(paths[0])
    frames: list[bytes] = []
    with wave.open(str(paths[0]), "rb") as w0:
        frames.append(w0.readframes(w0.getnframes()))
    for p in paths[1:]:
        if wav_sig(p) != sig0:
            raise RuntimeError(f"WAV format mismatch: {p} vs {paths[0]}")
        with wave.open(str(p), "rb") as w:
            frames.append(w.readframes(w.getnframes()))
    nch, sw, fr, ct, cn = sig0
    with wave.open(str(dest), "wb") as out_w:
        out_w.setnchannels(nch)
        out_w.setsampwidth(sw)
        out_w.setframerate(fr)
        out_w.setcomptype(ct, cn)
        for f in frames:
            out_w.writeframes(f)


async def synthesize_lecture_wav(
    tts: Any,
    text: str,
    *,
    chunk_chars: int,
    voice: str | None,
    speed: float,
    sample_rate: int,
) -> bytes:
    chunks = chunk_words(text, chunk_chars)
    if not chunks:
        raise ValueError("empty TTS text")
    with tempfile.TemporaryDirectory(prefix="educlaw_tts_") as td:
        tmp = Path(td)
        paths: list[Path] = []
        for i, ch in enumerate(chunks):
            req = TTSRequest(text=ch, voice=voice, speed=speed, sample_rate=sample_rate)
            audio = await tts.synthesize(req)
            p = tmp / f"chunk_{i:04d}.wav"
            p.write_bytes(audio.audio_bytes)
            paths.append(p)
        merged = tmp / "merged.wav"
        concat_wav_files(paths, merged)
        return merged.read_bytes()


# ---------------------------------------------------------------------------
# Pipeline config + runner
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
    tts_max_chars: int = 12_000
    tts_chunk_chars: int = 320
    continue_on_error: bool = False
    generate_site: bool = False
    site_output_dir: Path | None = None


async def run_pipeline(
    cfg: PipelineConfig,
    settings: Settings | None = None,
) -> tuple[int, Path]:
    """Run the full plan → lectures → TTS → AutoManim pipeline.

    Returns ``(exit_code, output_dir)``.
    """
    out_root = cfg.out
    if out_root is None:
        today = date.today().isoformat()
        sl = slug(cfg.topic[:60])
        out_root = Path("content") / "ir" / "series" / f"{today}-{sl}"
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
    user = (
        f"Plan a course with exactly {n} lectures (all {n}, not fewer). "
        f"Audience: general learners. Topic:\n{cfg.topic.strip()}"
    )

    tts = None
    if cfg.enable_tts and s.tts_enabled:
        tts = build_backend(s)
        if tts is None:
            print("TTS: disabled in settings; skipping audio.")
    elif cfg.enable_tts and not s.tts_enabled:
        print("TTS: set tts_enabled=true in profile. Skipping audio.")

    client = AsyncClient(host=s.ollama_url.rstrip("/"))
    audio_dir = out_root / "audio"
    if tts is not None:
        audio_dir.mkdir(parents=True, exist_ok=True)

    shield_impl: Shield | NoopShield = (
        Shield(client, model=s.shield_model) if cfg.enable_shield else NoopShield()
    )

    manim_clips: list[dict[str, object]] = []
    lecture_rows: list[dict[str, Any]] = []
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

    try:
        try:
            plan = await plan_course(client, s, user)
        except CoursePlanningFailed as e:
            print(f"Error: {e}")
            if e.raw_preview:
                print(f"(raw preview) {e.raw_preview[:200]}…")
            exit_code = 1
        else:
            lectures = plan.lectures[:n]
            (out_root / "course-plan.json").write_text(
                json.dumps(
                    {"title": plan.title, "audience": plan.audience, "lecture_count": len(lectures)},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest["lecture_count"] = len(lectures)
            print(f"Plan: {plan.title} ({len(lectures)} lectures)")

            prior_titles: list[str] = []
            n_lec = len(lectures)

            for i, outline in enumerate(lectures, start=1):
                print(f"  Lecture {i}/{n_lec}: {outline.title}")
                row: dict[str, Any] = {"lecture_index": i, "lecture_title": outline.title}

                try:
                    result = await generate_lecture(
                        client,
                        s.model_id,
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
                    if not cfg.continue_on_error:
                        exit_code = 1
                        break
                    continue

                prior_titles.append(outline.title)
                meta = dict(result.ir_suggestion) if result.ir_suggestion else {}
                post = frontmatter.Post(result.markdown, **meta)
                lec_slug = slug(outline.title or f"lec-{i}", 48)
                md_path = out_root / f"lecture-{i:02d}-{lec_slug}.md"
                md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
                print(f"  Wrote {md_path.name}")
                row["markdown"] = str(md_path.relative_to(out_root))

                if tts is not None:
                    text_content = tts_plain_text(result.markdown, cfg.tts_max_chars)
                    try:
                        wav_bytes = await synthesize_lecture_wav(
                            tts,
                            text_content,
                            chunk_chars=cfg.tts_chunk_chars,
                            voice=s.tts_voice,
                            speed=float(s.tts_speed),
                            sample_rate=int(s.tts_sample_rate),
                        )
                        wav = audio_dir / f"lecture-{i:02d}.wav"
                        wav.write_bytes(wav_bytes)
                        print(f"  TTS: {wav.name} ({len(wav_bytes)} bytes)")
                        row["audio"] = str(wav.relative_to(out_root))
                    except Exception as e:  # noqa: BLE001
                        print(f"  TTS error: {e!s}")
                        row["audio_error"] = str(e)

                scenes: list[dict[str, object]] = []
                if s.automanim_enabled:
                    try:
                        async for am_ev in run_automanim(
                            result.markdown,
                            dict(result.ir_suggestion),
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
                                rec = {
                                    "lecture_index": i,
                                    "lecture_title": outline.title,
                                    "path": am_ev.artifact.artifact_path,
                                    "scene": am_ev.artifact.scene_name,
                                }
                                scenes.append(rec)
                                manim_clips.append(rec)
                                print(f"  Manim: {am_ev.artifact.artifact_path}")
                            elif am_ev.kind == "error" and am_ev.message:
                                print(f"  Manim error: {am_ev.message}")
                    except Exception as e:  # noqa: BLE001
                        print(f"  AutoManim failed: {e!s}")
                        row["manim_error"] = str(e)
                        if not cfg.continue_on_error:
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
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        await _close_client()
        if tts is not None:
            await tts.close()

    if cfg.generate_site and exit_code == 0:
        try:
            from educlaw.sitegen.generator import generate_site

            site_path = generate_site(out_root, output_dir=cfg.site_output_dir)
            print(f"Site generated at: {site_path}")
        except Exception as e:  # noqa: BLE001
            print(f"Site generation failed: {e!s}")
            if not cfg.continue_on_error:
                exit_code = 1

    print(f"\nArtifacts under: {out_root}")
    return exit_code, out_root
