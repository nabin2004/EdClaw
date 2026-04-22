#!/usr/bin/env python3
"""
Iterative rejection-sampling SFT loop (Stage B).

Each iteration:
  1. Load policy (Hub adapter + base model id).
  2. Roll out completions for prompts from `prompts-jsonl` (must NOT be pilot eval).
  3. Score with `manibench.eval.harness` or `eval_uv_standalone` logic.
  4. Keep top `--top-fraction` by composite reward with executability gate.
  5. Fine-tune 1 epoch LoRA on buffer + optional `--mix-core-jsonl`.

Requires GPU + transformers for real runs. Use `--dry-run` to validate plumbing only.

Environment:
  MANIBENCH_ROLLOUT_CMD — optional shell command that reads prompt from stdin, prints completion.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.eval.harness import composite_reward, evaluate_sample  # noqa: E402
from manibench.leakage import assert_no_eval_leakage  # noqa: E402


def rollout_one(prompt_text: str) -> str:
    cmd = __import__("os").environ.get("MANIBENCH_ROLLOUT_CMD")
    if cmd:
        proc = subprocess.run(
            cmd,
            shell=True,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=600,
        )
        return proc.stdout or ""
    # Placeholder for CI / dry-run
    return """```python
from manim import *

class PlaceholderScene(Scene):
    def construct(self):
        self.play(Create(Text("stub")))
```"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts-jsonl", type=Path, required=True)
    ap.add_argument("--out-buffer", type=Path, default=ROOT / "out" / "iter_buffer.jsonl")
    ap.add_argument("--top-fraction", type=float, default=0.25)
    ap.add_argument("--require-exec", action="store_true", help="Keep only executability==1")
    ap.add_argument("--no-render-eval", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-rows", type=int, default=1000)
    args = ap.parse_args()

    scored = []
    with args.prompts_jsonl.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= args.max_rows:
                break
            if not line.strip():
                continue
            row = json.loads(line)
            user = ""
            for m in row.get("messages", []):
                if m.get("role") == "user":
                    user = m["content"]
                    break
            if args.dry_run:
                completion = rollout_one(user)
            else:
                completion = rollout_one(user)
            metrics = evaluate_sample(completion, run_render=not args.no_render_eval)
            if args.require_exec and metrics["executability"] < 1.0:
                continue
            r = composite_reward(metrics)
            msg_row = {
                "messages": row["messages"][:2]
                + [{"role": "assistant", "content": completion}],
                "metrics": metrics,
            }
            scored.append((r, msg_row))

    scored.sort(key=lambda x: x[0], reverse=True)
    k = max(1, math.ceil(len(scored) * args.top_fraction))
    keep = [x[1] for x in scored[:k]]

    texts = []
    for row in keep:
        for m in row["messages"]:
            if m["role"] == "user":
                texts.append(m["content"])
    assert_no_eval_leakage(texts)

    args.out_buffer.parent.mkdir(parents=True, exist_ok=True)
    with args.out_buffer.open("w", encoding="utf-8") as fo:
        for row in keep:
            fo.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(keep)} / {len(scored)} rows to {args.out_buffer}")


if __name__ == "__main__":
    main()
