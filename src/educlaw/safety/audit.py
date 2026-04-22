"""Audit log for safety decisions (hash-only for sensitive inputs)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from educlaw.safety.shield import Verdict


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def append_audit(
    path: Path,
    *,
    verdict: Verdict,
    phase: Literal["input", "output"],
    text: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "ts": datetime.now(UTC).isoformat(),
            "verdict": verdict.value,
            "phase": phase,
            "sha256": _hash_text(text),
        }
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
