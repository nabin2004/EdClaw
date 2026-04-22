"""Prevent train/eval leakage: pilot problem prompts must not appear in training rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def load_pilot_hashes() -> dict[str, str]:
    """Map MB-xxx -> sha256(full_prompt)."""
    path = DATA_DIR / "pilot_prompts.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: _sha256(item["full_prompt"]) for item in raw}


def load_eval_hashes_file() -> dict[str, str]:
    """Load precomputed `manibench_eval_hashes.json` if present."""
    path = DATA_DIR / "manibench_eval_hashes.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("hashes", data)


def assert_no_eval_leakage(
    train_texts: list[str],
    *,
    pilot_hashes: dict[str, str] | None = None,
) -> None:
    """Raise ValueError if any training string matches a pilot prompt hash."""
    ph = pilot_hashes or load_eval_hashes_file() or load_pilot_hashes()
    bad: list[str] = []
    for t in train_texts:
        h = _sha256(t)
        if h in ph.values():
            bad.append(h[:16])
    if bad:
        raise ValueError(f"Training data leaks pilot prompts (sha256 prefix match): {bad}")


def refresh_eval_hashes_json() -> Path:
    """Rewrite manibench_eval_hashes.json from pilot_prompts.json."""
    path = DATA_DIR / "manibench_eval_hashes.json"
    hashes = load_pilot_hashes()
    payload = {
        "description": "SHA256 of full_prompt per pilot problem",
        "hashes": hashes,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
