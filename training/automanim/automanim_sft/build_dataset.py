"""Build JSONL SFT corpus from episode directories."""

from __future__ import annotations

import json
import os
from pathlib import Path

from automanim_sft.template import render_episode


def _episode_dirs(dataset_dir: Path) -> list[Path]:
    out: list[Path] = []
    for item in sorted(os.listdir(dataset_dir)):
        item_path = dataset_dir / item
        if not item_path.is_dir() or not item.startswith("episode_"):
            continue
        out.append(item_path)
    return out


def build_automanim_jsonl(
    *,
    dataset_dir: Path | str,
    output_file: Path | str,
    episode_id_filter: set[str] | None = None,
    require_generated_code: bool = True,
    include_failures: bool = True,
    verbose_every: int = 10,
) -> dict[str, object]:
    """
    Iterate ``dataset/*/metadata.json``, render Gemma-style text rows.

    Args:
        dataset_dir: Root containing ``episode_*`` dirs.
        output_file: JSONL destination (one ``{"text": "..."}`` per line).
        episode_id_filter: If set, only these ``episode_*`` basename IDs.
        require_generated_code: Skip episodes with empty ``generated_code``.
        include_failures: When False and ``require_generated_code`` is False, skip rows
            where ``status == "failure"`` and there is no successful code turn.
            (When requiring code, failures without code are already skipped.)
        verbose_every: Print progress every N written rows.

    Returns:
        Summary dict: written, skipped counts, skipped reasons samples, lengths.
    """
    root = Path(dataset_dir)
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    skipped_reasons: dict[str, int] = {}
    skipped_samples: dict[str, list[str]] = {}
    lengths: list[int] = []
    written = 0

    def _skip(reason: str, sample: str) -> None:
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        if reason not in skipped_samples:
            skipped_samples[reason] = []
        if len(skipped_samples[reason]) < 5:
            skipped_samples[reason].append(sample)

    with out_path.open("w", encoding="utf-8") as f_out:
        for item_path in _episode_dirs(root):
            epid = item_path.name
            if episode_id_filter is not None and epid not in episode_id_filter:
                continue

            metadata_path = item_path / "metadata.json"
            if not metadata_path.is_file():
                _skip("no_metadata_json", epid)
                continue

            try:
                entry = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                _skip("metadata_load_error", f"{metadata_path}: {exc}")
                continue

            tid = entry.get("episode_id", epid)
            gc = entry.get("generated_code") or ""
            if isinstance(gc, str) and gc.strip():
                pass  # ok
            else:
                gc = ""

            if require_generated_code and not gc.strip():
                _skip("no_generated_code", tid)
                continue

            if (
                not require_generated_code
                and not include_failures
                and entry.get("status") == "failure"
                and not gc.strip()
            ):
                _skip("failure_no_code", tid)
                continue

            try:
                rendered = render_episode(entry)
            except Exception as exc:  # noqa: BLE001 — surface bad rows clearly
                _skip("render_error", f"{tid}: {exc}")
                continue

            f_out.write(json.dumps({"text": rendered}, ensure_ascii=False) + "\n")
            lengths.append(len(rendered))
            written += 1
            if verbose_every and written % verbose_every == 0:
                print(f"Processed {written} episodes...", flush=True)

    summary: dict[str, object] = {
        "written": written,
        "skipped_reasons": skipped_reasons,
        "skipped_samples": skipped_samples,
        "lengths": lengths,
        "output_file": str(out_path.resolve()),
        "dataset_dir": str(root.resolve()),
    }

    if lengths:
        summary["chars_min"] = min(lengths)
        summary["chars_max"] = max(lengths)
        summary["chars_avg"] = sum(lengths) // len(lengths)

    return summary


def print_build_summary(summary: dict[str, object]) -> None:
    """Stdout summary for CLI."""
    print(
        "Done:",
        summary["written"],
        "rows ->",
        summary["output_file"],
        flush=True,
    )
    if summary.get("skipped_reasons"):
        print("Skipped by reason:", summary["skipped_reasons"], flush=True)
        ss = summary.get("skipped_samples") or {}
        for reason, items in ss.items():
            if items:
                print(f"  {reason} sample ids/paths:", items, flush=True)
    lens = summary.get("lengths")
    if lens:
        print(
            "Rendered text length (chars): min="
            f"{summary.get('chars_min')} max={summary.get('chars_max')} "
            f"avg={summary.get('chars_avg')}",
            flush=True,
        )
