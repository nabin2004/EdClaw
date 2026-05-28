#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2>=3.1",
# ]
# ///
"""
Emit Gemma-4-style JSONL ({\"text\": ...}) from AutoManim episode metadata.

Run from repo root or from ``training/automanim``::

  uv run training/automanim/scripts/build_sft_jsonl.py \\
    --dataset-dir src/educlaw/automanim/dataset \\
    --output src/educlaw/automanim/sft_dataset.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_pkg_path() -> None:
    here = Path(__file__).resolve().parent
    pkg_root = here.parent  # .../training/automanim
    sys.path.insert(0, str(pkg_root))


def main() -> None:
    _ensure_pkg_path()
    from automanim_sft.build_dataset import (
        build_automanim_jsonl,
        print_build_summary,
    )

    ap = argparse.ArgumentParser(
        description="Build sft_dataset.jsonl from episode metadata dirs",
    )
    ap.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Directory containing episode_* folders",
    )
    ap.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination JSONL path",
    )
    ap.add_argument(
        "--episode-id",
        action="append",
        default=None,
        help="Repeatable: restrict to episode id(s) like episode_0002",
    )
    ap.add_argument(
        "--require-generated-code",
        action="store_true",
        default=True,
        dest="require_generated_code",
        help="Skip episodes with empty generated_code (default: on)",
    )
    ap.add_argument(
        "--no-require-generated-code",
        action="store_false",
        dest="require_generated_code",
        help="Include episodes without generated_code (often failure-only traces)",
    )
    ap.add_argument(
        "--include-failures",
        action="store_true",
        default=True,
        help="When --no-require-generated-code, include failure rows (default)",
    )
    ap.add_argument(
        "--exclude-failures-without-code",
        action="store_false",
        dest="include_failures",
        help="When not requiring code, still skip failures with no assistant code",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress dots",
    )
    args = ap.parse_args()

    filt = set(args.episode_id) if args.episode_id else None

    summary = build_automanim_jsonl(
        dataset_dir=args.dataset_dir,
        output_file=args.output,
        episode_id_filter=filt,
        require_generated_code=bool(args.require_generated_code),
        include_failures=bool(args.include_failures),
        verbose_every=0 if args.quiet else 10,
    )
    print_build_summary(summary)


if __name__ == "__main__":
    main()
