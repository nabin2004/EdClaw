#!/usr/bin/env python3
"""
Render a lecture series to Manim MP4s and mux each lecture with chunked TTS audio.

Requires:
  - Ollama running; ``model_id`` in profile for planner/codegen.
  - ``shield_model`` in profile (defaults to the same tag as ``model_id``). Override with
    ``--shield-model`` if needed.
  - ``ffmpeg`` and ``ffprobe`` on PATH.
  - TTS: ``tts_enabled`` and a working backend in profile (e.g. kitten + model id).

Examples:
  PYTHONPATH=src .venv/bin/python scripts/render_series_with_tts.py \\
    content/ir/series/2026-04-23-intro-linear-algebra-8

  # Re-use existing videos/manifest.json; only TTS + mux
  PYTHONPATH=src .venv/bin/python scripts/render_series_with_tts.py ./my-series --tts-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import frontmatter
from ollama import AsyncClient

from educlaw.automanim.orchestrator import run_automanim
from educlaw.config.settings import load_settings
from educlaw.safety.shield import Shield
from educlaw.tts.contract import TTSRequest
from educlaw.tts.registry import build_backend


def _slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "lec"


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


def _require_bin(name: str) -> str:
    p = shutil.which(name)
    if not p:
        raise SystemExit(f"Missing `{name}` on PATH (install ffmpeg).")
    return p


def _ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        [
            _require_bin("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(r.stdout)
    return float(data["format"]["duration"])


def _ffmpeg_concat_media(paths: list[Path], out: Path, *, reencode_audio: bool) -> None:
    if len(paths) == 1:
        shutil.copy2(paths[0], out)
        return
    lst = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
    )
    try:
        for p in paths:
            ap = p.resolve().as_posix().replace("'", "'\\''")
            lst.write(f"file '{ap}'\n")
        lst.close()
        cmd = [
            _require_bin("ffmpeg"),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            lst.name,
        ]
        if reencode_audio:
            cmd += ["-c:v", "copy", "-c:a", "pcm_s16le", str(out)]
        else:
            cmd += ["-c", "copy", str(out)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    finally:
        Path(lst.name).unlink(missing_ok=True)


def _mux_video_audio(
    video: Path,
    audio: Path,
    out: Path,
    *,
    video_pad_sec: float,
) -> None:
    """Mux *video* with *audio*; if audio is longer, hold last video frame for *video_pad_sec*."""
    ff = _require_bin("ffmpeg")
    if video_pad_sec <= 0.01:
        subprocess.run(
            [
                ff,
                "-y",
                "-i",
                str(video),
                "-i",
                str(audio),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(out),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return
    # Extend video by cloning the last frame so audio is not clipped.
    vf = f"tpad=stop_mode=clone:stop_duration={video_pad_sec:.3f}"
    subprocess.run(
        [
            ff,
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-filter_complex",
            f"[0:v]{vf}[v]",
            "-map",
            "[v]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


async def _maybe_close_ollama(client: AsyncClient) -> None:
    aclose = getattr(client, "aclose", None)
    if callable(aclose):
        await aclose()  # type: ignore[misc]
        return
    close = getattr(client, "close", None)
    if callable(close):
        out = close()
        if asyncio.iscoroutine(out):
            await out  # type: ignore[misc]


async def _synthesize_long_wav(
    tts: Any,
    text: str,
    *,
    chunk_chars: int,
    voice: str | None,
    speed: float,
    sample_rate: int,
    work: Path,
) -> Path:
    chunks = _chunk_words(text, chunk_chars)
    if not chunks:
        raise ValueError("empty TTS text")
    wav_paths: list[Path] = []
    for i, ch in enumerate(chunks):
        req = TTSRequest(text=ch, voice=voice, speed=speed, sample_rate=sample_rate)
        audio = await tts.synthesize(req)
        wp = work / f"chunk_{i:04d}.wav"
        wp.write_bytes(audio.audio_bytes)
        wav_paths.append(wp)
    merged = work / "narration.wav"
    if len(wav_paths) == 1:
        shutil.copy2(wav_paths[0], merged)
    else:
        _ffmpeg_concat_media(wav_paths, merged, reencode_audio=True)
    return merged


async def _run_automanim_collect(
    md_path: Path,
    settings: Any,
    shield: Shield,
    client: AsyncClient,
    videos_root: Path,
) -> tuple[list[Path], list[dict[str, Any]]]:
    post = frontmatter.loads(md_path.read_text(encoding="utf-8"))
    meta = dict(post.metadata) if isinstance(post.metadata, dict) else {}
    clips: list[tuple[int, Path, dict[str, Any]]] = []
    async for ev in run_automanim(
        str(post.content),
        meta,
        settings,
        shield,
        ollama=client,
        output_root=videos_root,
    ):
        if ev.kind == "scene_done" and ev.artifact and ev.artifact.artifact_path:
            p = Path(ev.artifact.artifact_path)
            if p.is_file() and ev.scene_index is not None:
                art = ev.artifact
                row = {
                    "scene_index": ev.scene_index,
                    "scene_title": ev.scene_title,
                    "artifact_path": str(p),
                    "exit_code": art.exit_code,
                }
                clips.append((ev.scene_index, p, row))
    clips.sort(key=lambda x: x[0])
    paths = [p for _, p, _ in clips]
    rows = [r for _, _, r in clips]
    return paths, rows


def _write_series_manifest(
    manifest_path: Path,
    lecture_id: str,
    rows: list[dict[str, Any]],
) -> None:
    data: dict[str, Any] = {}
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data[lecture_id] = rows
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _clips_from_manifest(manifest: dict[str, Any], lecture_id: str) -> list[Path]:
    rows = manifest.get(lecture_id) or []
    if not isinstance(rows, list):
        return []
    pairs: list[tuple[int, Path]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ap = row.get("artifact_path")
        si = row.get("scene_index")
        if ap and isinstance(si, int):
            p = Path(str(ap))
            if p.is_file():
                pairs.append((si, p))
    pairs.sort(key=lambda x: x[0])
    return [p for _, p in pairs]


async def _async_main(args: argparse.Namespace) -> int:
    _require_bin("ffmpeg")
    _require_bin("ffprobe")

    series = args.series.expanduser().resolve()
    if not series.is_dir():
        print(f"Not a directory: {series}")
        return 1

    updates: dict[str, Any] = {}
    if args.shield_model:
        updates["shield_model"] = args.shield_model
    if args.automanim_backend:
        updates["automanim_backend"] = args.automanim_backend
    settings = load_settings().model_copy(update=updates)

    videos_root = series / "videos"
    if not args.tts_only:
        videos_root.mkdir(parents=True, exist_ok=True)
    final_root = args.final_dir.expanduser().resolve() if args.final_dir else series / "final"
    final_root.mkdir(parents=True, exist_ok=True)
    tmp_root = series / ".render_series_tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)

    manifest_path = videos_root / "manifest.json"
    if manifest_path.is_file():
        disk_manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        disk_manifest = {}

    tts = None
    if not args.skip_tts:
        if not settings.tts_enabled:
            print("TTS disabled in profile (tts_enabled=false). Use --skip-tts for video-only.")
            return 1
        tts = build_backend(settings)
        if tts is None:
            print("TTS backend could not be built.")
            return 1

    client = AsyncClient(host=settings.ollama_url.rstrip("/"))
    shield = Shield(client, model=settings.shield_model)

    summary: list[dict[str, Any]] = []

    try:
        for md_path in sorted(series.glob("lecture-*.md")):
            post = frontmatter.loads(md_path.read_text(encoding="utf-8"))
            meta = dict(post.metadata) if isinstance(post.metadata, dict) else {}
            lecture_id = str(meta.get("id") or md_path.stem)
            stem = md_path.stem

            work = tmp_root / stem
            work.mkdir(parents=True, exist_ok=True)

            if args.tts_only:
                clip_paths = _clips_from_manifest(disk_manifest, lecture_id)
            else:
                print(f"AutoManim: {md_path.name} ({lecture_id}) …")
                clip_paths, manifest_rows = await _run_automanim_collect(
                    md_path,
                    settings,
                    shield,
                    client,
                    videos_root,
                )
                _write_series_manifest(manifest_path, lecture_id, manifest_rows)
                disk_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            if not clip_paths:
                print(f"  Skip (no rendered clips): {lecture_id}")
                summary.append({"lecture": lecture_id, "status": "no_video"})
                continue

            concat_video = work / "lecture_manim_concat.mp4"
            _ffmpeg_concat_media(clip_paths, concat_video, reencode_audio=False)

            if args.skip_tts:
                out_mp4 = final_root / f"{stem}-manim-only.mp4"
                shutil.copy2(concat_video, out_mp4)
                print(f"  Wrote {out_mp4.name}")
                summary.append(
                    {"lecture": lecture_id, "video": str(out_mp4), "status": "video_only"},
                )
                continue

            plain = _tts_plain_text(str(post.content), args.tts_max_chars)
            print(f"  TTS ({len(plain)} chars, chunks ≤{args.chunk_chars}) …")
            assert tts is not None
            wav = await _synthesize_long_wav(
                tts,
                plain,
                chunk_chars=args.chunk_chars,
                voice=settings.tts_voice,
                speed=float(settings.tts_speed),
                sample_rate=int(settings.tts_sample_rate),
                work=work,
            )

            v_dur = _ffprobe_duration(concat_video)
            a_dur = _ffprobe_duration(wav)
            pad = max(0.0, a_dur - v_dur)

            out_mp4 = final_root / f"{stem}-with-audio.mp4"
            _mux_video_audio(concat_video, wav, out_mp4, video_pad_sec=pad)
            print(f"  Wrote {out_mp4.name} (video {v_dur:.1f}s, audio {a_dur:.1f}s)")
            summary.append(
                {
                    "lecture": lecture_id,
                    "video": str(out_mp4),
                    "manim_concat": str(concat_video),
                    "audio": str(wav),
                    "status": "ok",
                },
            )

    finally:
        await _maybe_close_ollama(client)
        if tts is not None:
            await tts.close()

    (final_root / "render-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nDone. Outputs in {final_root}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "series",
        type=Path,
        help="Series directory containing lecture-*.md",
    )
    p.add_argument(
        "--shield-model",
        default=None,
        help="Ollama model id for Shield (overrides profile shield_model).",
    )
    p.add_argument(
        "--automanim-backend",
        choices=("local", "docker"),
        default=None,
        help="Override automanim render backend from profile.",
    )
    p.add_argument(
        "--final-dir",
        type=Path,
        default=None,
        help="Directory for final MP4s (default: <series>/final).",
    )
    p.add_argument(
        "--chunk-chars",
        type=int,
        default=320,
        help="Max characters per TTS chunk (smaller avoids kitten/ONNX long-sequence errors).",
    )
    p.add_argument(
        "--tts-max-chars",
        type=int,
        default=24_000,
        dest="tts_max_chars",
        help="Max plain-text characters taken from each lecture for TTS.",
    )
    p.add_argument(
        "--tts-only",
        action="store_true",
        help="Skip AutoManim; use existing videos/manifest.json for clip paths.",
    )
    p.add_argument(
        "--skip-tts",
        action="store_true",
        help="Only concatenate Manim scenes to final/ (no narration).",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main()
