#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2>=3.1",
# ]
# ///
"""Build Gemma-4-style JSONL from IR series scene.py files.

Run from repo root::

  uv run training/automanim/scripts/build_ir_sft_jsonl.py \\
    --ir-root content/ir \\
    --output src/educlaw/automanim/ir_sft_dataset.jsonl

Optionally also write per-scene subtitles.srt files::

  uv run training/automanim/scripts/build_ir_sft_jsonl.py \\
    --ir-root content/ir \\
    --output src/educlaw/automanim/ir_sft_dataset.jsonl \\
    --write-srt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _ensure_pkg_path() -> None:
    here = Path(__file__).resolve().parent
    pkg_root = here.parent  # .../training/automanim
    sys.path.insert(0, str(pkg_root))


def main() -> None:
    _ensure_pkg_path()

    from automanim_sft.build_dataset import print_build_summary
    from automanim_sft.ir_scene_dataset import build_srt, collect_ir_scenes
    from automanim_sft.template import render_episode

    ap = argparse.ArgumentParser(
        description="Build Gemma4 JSONL from content/ir/series scene.py files"
    )
    ap.add_argument(
        "--ir-root",
        type=Path,
        default=Path("content/ir"),
        help="IR content root (default: content/ir)",
    )
    ap.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination JSONL path",
    )
    ap.add_argument(
        "--write-srt",
        action="store_true",
        default=False,
        help="Write subtitles.srt alongside each scene.py (estimated timings)",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    args = ap.parse_args()

    ir_root = args.ir_root.expanduser().resolve()
    if not ir_root.is_dir():
        print(f"IR root not found: {ir_root}", file=sys.stderr)
        sys.exit(1)

    episodes = collect_ir_scenes(ir_root)
    if not episodes:
        print(f"No scene.py files found under {ir_root}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Found {len(episodes)} IR scenes under {ir_root}")

    out_path = args.output.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    lengths: list[int] = []
    series_root = ir_root / "series"

    with out_path.open("w", encoding="utf-8") as f_out:
        for ep in episodes:
            try:
                rendered = render_episode(ep)
            except Exception as exc:
                if not args.quiet:
                    print(f"  skip {ep['episode_id']}: render error: {exc}")
                skipped += 1
                continue

            f_out.write(json.dumps({"text": rendered}, ensure_ascii=False) + "\n")
            lengths.append(len(rendered))
            written += 1

            if args.write_srt and ep.get("narration_segments"):
                srt_text = build_srt(ep["narration_segments"])
                # Reconstruct the scene.py path to place srt next to it
                scene_path = (
                    series_root
                    / ep["series"].replace(" ", "-").lower()  # approximate; best-effort
                    / "videos"
                    / ep["lecture"]
                    / ep["scene"]
                    / "subtitles.srt"
                )
                # More reliable: find by episode_id parts
                parts = ep["episode_id"].split("__")
                if len(parts) == 3:
                    candidate = series_root / parts[0] / "videos" / parts[1] / parts[2] / "subtitles.srt"
                    if candidate.parent.is_dir():
                        scene_path = candidate

                try:
                    scene_path.write_text(srt_text, encoding="utf-8")
                    if not args.quiet:
                        print(f"  wrote {scene_path.relative_to(ir_root.parent)}")
                except OSError as exc:
                    if not args.quiet:
                        print(f"  could not write SRT for {ep['episode_id']}: {exc}")

            if not args.quiet and written % 5 == 0:
                print(f"  {written} episodes processed...")

    summary = {
        "written": written,
        "skipped": skipped,
        "output_file": str(out_path),
        "dataset_dir": str(ir_root),
        "lengths": lengths,
    }
    if lengths:
        summary["chars_min"] = min(lengths)
        summary["chars_max"] = max(lengths)
        summary["chars_avg"] = sum(lengths) // len(lengths)

    print_build_summary(summary)


if __name__ == "__main__":
    main()
