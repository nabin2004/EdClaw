#!/usr/bin/env python3
"""
End-to-end course generator: plan → Markdown → subtitle-chunked SRT/VTT+WAV → Manim.

Subtitle generation follows industry standards:
  - 15-20 characters per second reading speed
  - Max 2 lines, 42 characters per line per block
  - 3-7 seconds display duration per block

Reads ``profiles/local.toml`` (or ``EDUCLAW_PROFILE_PATH``). Requires Ollama.

Examples:
  .venv/bin/python scripts/run_full_course_pipeline.py \\
    "Introduction to linear algebra" --lectures 8

  .venv/bin/python scripts/run_full_course_pipeline.py \\
    "Python basics" --lectures 2 --out content/courses/my-run --no-automanim

  .venv/bin/python scripts/run_full_course_pipeline.py "Topic" --no-tts --no-automanim --no-shield
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from educlaw.autocourse.pipeline import PipelineConfig, run_pipeline


async def _run(args: argparse.Namespace) -> int:
    cfg = PipelineConfig(
        topic=args.topic,
        lectures=args.lectures,
        out=args.out,
        enable_tts=bool(args.tts),
        enable_automanim=bool(args.automanim),
        enable_shield=bool(args.shield),
        automanim_output_dir=args.automanim_output_dir,
        automanim_backend=args.automanim_backend,
        continue_on_error=args.continue_on_error,
        generate_site=args.generate_site,
        site_output_dir=args.site_output_dir,
    )
    exit_code, _ = await run_pipeline(cfg)
    return exit_code


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run plan + per-lecture Markdown, optional chunked TTS, optional AutoManim "
            "(see module docstring)."
        ),
    )
    p.add_argument("topic", help="What to teach (passed to the course planner).")
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
        help="Output directory (default: content/courses/YYYY-MM-DD-slug).",
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
