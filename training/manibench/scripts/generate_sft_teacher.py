#!/usr/bin/env python3
"""Distill SFT rows from a teacher LLM via LiteLLM (Gemini, OpenAI, Anthropic, Ollama, …)."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manibench.constants import MANIM_CE_SYSTEM  # noqa: E402
from manibench.eval.harness import composite_reward, evaluate_sample  # noqa: E402
from manibench.leakage import assert_no_eval_leakage  # noqa: E402
from manibench.prompt_seeds import weighted_prompts  # noqa: E402

DRY_RUN_COMPLETION = """```python
from manim import *

class DryRunScene(Scene):
    def construct(self):
        self.play(Create(Text("dry-run", font_size=44)))
```"""


def _model_slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "_")


def _cache_key(model: str, system: str, user: str) -> str:
    payload = f"{model}\n{system}\n{user}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_cache(cache_dir: Path, key: str) -> str | None:
    path = cache_dir / f"{key}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        c = data.get("completion")
        return c if isinstance(c, str) else None
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(cache_dir: Path, key: str, completion: str) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{key}.json"
    path.write_text(json.dumps({"completion": completion}, ensure_ascii=False), encoding="utf-8")


def _extract_user_messages_from_jsonl(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.is_file():
        return done
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for m in row.get("messages", []):
                if m.get("role") == "user":
                    done.add(m["content"])
                    break
    return done


def _load_prompt_pairs_from_jsonl(path: Path, cap: int) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if len(pairs) >= cap:
                break
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cat = str(row.get("task_type") or "direct_visualization")
            if isinstance(row.get("user"), str):
                pairs.append((cat, row["user"]))
                continue
            if isinstance(row.get("prompt"), str):
                pairs.append((cat, row["prompt"]))
                continue
            user = ""
            for m in row.get("messages", []):
                if m.get("role") == "user":
                    u = m.get("content")
                    user = u if isinstance(u, str) else ""
                    break
            if user:
                pairs.append((cat, user))
    return pairs


def _should_retry(exc: BaseException) -> bool:
    name = type(exc).__name__
    if any(
        s in name
        for s in (
            "RateLimit",
            "APIConnection",
            "Connect",
            "Timeout",
            "ServiceUnavailable",
            "InternalServer",
        )
    ):
        return True
    return isinstance(exc, (TimeoutError, asyncio.TimeoutError, OSError))


def _assistant_from_response(resp: Any) -> str:
    choice0 = resp.choices[0]
    msg = getattr(choice0, "message", None) or {}
    if isinstance(msg, dict):
        content = msg.get("content")
    else:
        content = getattr(msg, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


async def _acompletion_with_retries(
    *,
    model: str,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
    timeout: float,
    max_retries: int,
) -> str:
    import litellm  # noqa: WPS433

    last: BaseException | None = None
    for attempt in range(max_retries):
        try:
            resp = await litellm.acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            return _assistant_from_response(resp)
        except BaseException as exc:  # noqa: BLE001
            last = exc
            if attempt < max_retries - 1 and _should_retry(exc):
                await asyncio.sleep(2**attempt)
                continue
            raise
    assert last is not None
    raise last


async def _process_one(
    *,
    category: str,
    user: str,
    model: str,
    dry_run: bool,
    cache_dir: Path,
    temperature: float,
    max_tokens: int,
    timeout: float,
    max_retries: int,
    run_render: bool,
    require_exec: bool,
    min_composite: float,
    sem: asyncio.Semaphore,
    out_lock: asyncio.Lock,
    rej_lock: asyncio.Lock,
    out_path: Path,
    rejected_path: Path | None,
    resume_users: set[str],
) -> tuple[bool, bool]:
    """Returns (teacher_api_called, skipped_resume)."""
    if user in resume_users:
        return False, True

    key = _cache_key(model, MANIM_CE_SYSTEM, user)
    completion: str | None = _load_cache(cache_dir, key)
    api_called = False

    if completion is None:
        async with sem:
            if dry_run:
                completion = DRY_RUN_COMPLETION
            else:
                completion = await _acompletion_with_retries(
                    model=model,
                    system=MANIM_CE_SYSTEM,
                    user=user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    max_retries=max_retries,
                )
                api_called = True
        if completion and not dry_run:
            _write_cache(cache_dir, key, completion)

    if not completion or not completion.strip():
        row = {
            "messages": [
                {"role": "system", "content": MANIM_CE_SYSTEM},
                {"role": "user", "content": user},
            ],
            "task_type": category,
            "source": f"teacher_rejected:{_model_slug(model)}",
            "reject_reason": "empty_completion",
        }
        async with rej_lock:
            if rejected_path is not None:
                with rejected_path.open("a", encoding="utf-8") as fo:
                    fo.write(json.dumps(row, ensure_ascii=False) + "\n")
        return api_called, False

    metrics = evaluate_sample(completion, run_render=run_render)
    reward = composite_reward(metrics)

    ok_exec = not require_exec or float(metrics["executability"]) >= 1.0
    ok_reward = reward >= min_composite

    slug = _model_slug(model)
    base_row = {
        "messages": [
            {"role": "system", "content": MANIM_CE_SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": completion.strip()},
        ],
        "task_type": category,
        "source": f"teacher:{slug}",
        "metrics": metrics,
    }

    if not ok_exec or not ok_reward:
        reason = []
        if not ok_exec:
            reason.append("require_exec_failed")
        if not ok_reward:
            reason.append("below_min_composite")
        rej = {
            **base_row,
            "source": f"teacher_rejected:{slug}",
            "reject_reason": ",".join(reason),
        }
        async with rej_lock:
            if rejected_path is not None:
                with rejected_path.open("a", encoding="utf-8") as fo:
                    fo.write(json.dumps(rej, ensure_ascii=False) + "\n")
        return api_called, False

    async with out_lock:
        with out_path.open("a", encoding="utf-8") as fo:
            fo.write(json.dumps(base_row, ensure_ascii=False) + "\n")
    return api_called, False


async def _run_async(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    if args.prompts_jsonl is not None:
        pairs = _load_prompt_pairs_from_jsonl(args.prompts_jsonl, args.count)
    else:
        pairs = weighted_prompts(args.count, rng)

    users = [u for _, u in pairs]
    if not args.skip_leak_check:
        assert_no_eval_leakage(users)

    resume_users: set[str] = set()
    if args.resume and args.out.is_file():
        resume_users = _extract_user_messages_from_jsonl(args.out)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not args.resume or not args.out.is_file():
        args.out.write_text("", encoding="utf-8")
    if args.rejected_out:
        args.rejected_out.parent.mkdir(parents=True, exist_ok=True)
        if not args.resume or not args.rejected_out.is_file():
            args.rejected_out.write_text("", encoding="utf-8")

    sem = asyncio.Semaphore(max(1, args.concurrency))
    out_lock = asyncio.Lock()
    rej_lock = asyncio.Lock()
    run_render = bool(args.render_eval)

    tasks = [
        _process_one(
            category=cat,
            user=user,
            model=args.model,
            dry_run=args.dry_run,
            cache_dir=args.cache_dir,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=float(args.timeout),
            max_retries=args.max_retries,
            run_render=run_render,
            require_exec=args.require_exec,
            min_composite=args.min_composite,
            sem=sem,
            out_lock=out_lock,
            rej_lock=rej_lock,
            out_path=args.out,
            rejected_path=args.rejected_out,
            resume_users=resume_users,
        )
        for cat, user in pairs
    ]
    await asyncio.gather(*tasks)
    accepted_lines = sum(1 for line in args.out.read_text(encoding="utf-8").splitlines() if line.strip())
    return accepted_lines


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate SFT JSONL from a teacher model (LiteLLM).")
    ap.add_argument("--model", type=str, default="gemini/gemini-2.0-flash")
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--prompts-jsonl", type=Path, default=None, help="Optional JSONL of prompts (messages/user/prompt).")
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "manibench-sft-teacher.jsonl")
    ap.add_argument("--rejected-out", type=Path, default=None)
    ap.add_argument("--cache-dir", type=Path, default=ROOT / "out" / "_teacher_cache")
    ap.add_argument("--resume", action="store_true", help="Skip user prompts already present in --out.")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--max-retries", type=int, default=3)
    ap.add_argument("--render-eval", action="store_true", help="Run manim render for executability (slow).")
    ap.add_argument("--require-exec", action="store_true", help="Keep only rows with executability==1.")
    ap.add_argument("--min-composite", type=float, default=0.0, help="Minimum composite_reward to keep.")
    ap.add_argument("--dry-run", action="store_true", help="Stub completions; no API calls.")
    ap.add_argument("--skip-leak-check", action="store_true")
    args = ap.parse_args()

    accepted = asyncio.run(_run_async(args))
    print(f"Wrote {accepted} accepted rows to {args.out}")
    if args.rejected_out:
        rej_n = sum(1 for _ in args.rejected_out.read_text(encoding="utf-8").splitlines() if _.strip())
        print(f"Rejected / logged rows: {rej_n} -> {args.rejected_out}")


if __name__ == "__main__":
    main()
