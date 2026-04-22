#!/usr/bin/env python3
"""Refresh manibench_eval_hashes.json from pilot_prompts.json."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.leakage import refresh_eval_hashes_json  # noqa: E402

if __name__ == "__main__":
    p = refresh_eval_hashes_json()
    print(f"Wrote {p}")
