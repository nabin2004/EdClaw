#!/usr/bin/env python3
"""Aggregate ManiBench metrics JSONL runs into an ablation markdown table."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path


def _mean(xs: list[float]) -> float:
    return statistics.mean(xs) if xs else 0.0


def _stderr(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    return statistics.stdev(xs) / math.sqrt(len(xs))


def summarize(path: Path) -> dict[str, float]:
    execs, vcers, aligns, covs = [], [], [], []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            m = obj.get("metrics") or obj
            execs.append(float(m.get("executability", 0)))
            vcers.append(float(m.get("vcer", 0)))
            aligns.append(float(m.get("alignment", 0)))
            covs.append(float(m.get("coverage", 0)))
    return {
        "executability_mean": _mean(execs),
        "executability_stderr": _stderr(execs),
        "vcer_mean": _mean(vcers),
        "alignment_mean": _mean(aligns),
        "coverage_mean": _mean(covs),
        "n": len(execs),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", metavar="NAME=PATH", required=True)
    ap.add_argument("--out-md", type=Path, default=Path("manibench_ablation.md"))
    args = ap.parse_args()

    header = (
        "| Stage | Exec | Exec stderr | VCER | Align | Coverage | n |\n"
        "|---|---:|---:|---:|---:|---:|---:|"
    )
    lines = ["# ManiBench ablation", "", header.split("\n")[0], header.split("\n")[1]]
    for item in args.runs:
        if "=" not in item:
            print("Use NAME=path/to/scores.jsonl", file=sys.stderr)
            sys.exit(1)
        name, p = item.split("=", 1)
        s = summarize(Path(p))
        row = (
            f"| {name} | {s['executability_mean']:.3f} | {s['executability_stderr']:.3f} | "
            f"{s['vcer_mean']:.3f} | {s['alignment_mean']:.3f} | "
            f"{s['coverage_mean']:.3f} | {s['n']} |"
        )
        lines.append(row)

    text = "\n".join(lines) + "\n"
    args.out_md.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
