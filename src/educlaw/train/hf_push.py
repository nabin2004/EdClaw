"""Push EdClaw content to HuggingFace Hub as a fine-tuning dataset.

Two entry points:
  push_to_hub        – scans IR .md files (and optional Manim scene.py files)
  push_jsonl_to_hub  – reads a pre-built ShareGPT JSONL file directly
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import frontmatter

if TYPE_CHECKING:
    from datasets import Dataset, DatasetDict

FormatType = Literal["sharegpt", "alpaca"]

_SYSTEM_PROMPT = (
    "You are EdClaw, an expert educational AI tutor. "
    "You provide clear, well-structured, comprehensive explanations of academic topics. "
    "Your teaching style is thorough yet accessible, using progressive complexity and concrete examples."
)

_MANIM_SYSTEM_PROMPT = (
    "You are an expert Manim animation developer for educational content. "
    "Given a scene description and lecture context, write clean, correct Manim Python code "
    "that visually explains the concept."
)


def _slug_to_title(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug).title()


def _scene_slug_to_title(slug: str) -> str:
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
    slug = re.sub(r"^teach-me-(?:about-)?", "", slug)
    slug = re.sub(r"-\d+$", "", slug)
    slug = re.sub(r"^\d+-", "", slug)
    return re.sub(r"[-_]+", " ", slug).title()


def _load_lecture(path: Path) -> dict | None:
    try:
        post = frontmatter.loads(path.read_text(encoding="utf-8"))
        meta = dict(post.metadata) if isinstance(post.metadata, dict) else {}
        body = post.content.strip()
        if not body:
            return None
        return {"meta": meta, "body": body, "path": str(path)}
    except Exception:
        return None


def _to_sharegpt(lecture: dict) -> dict:
    meta = lecture["meta"]
    title = str(meta.get("title") or _slug_to_title(Path(lecture["path"]).stem))
    objective = str(meta.get("objective") or "").strip()
    difficulty = meta.get("difficulty")
    prereqs = [str(p) for p in (meta.get("prerequisites") or [])]

    human_parts = [f"Teach me about: **{title}**"]
    if objective:
        human_parts.append(f"\nObjective: {objective}")
    if prereqs:
        human_parts.append(f"\nPrerequisites: {', '.join(prereqs)}")
    if difficulty:
        human_parts.append(f"\nDifficulty: {difficulty}/5")

    return {
        "conversations": [
            {"from": "system", "value": _SYSTEM_PROMPT},
            {"from": "human", "value": "".join(human_parts)},
            {"from": "gpt", "value": lecture["body"]},
        ]
    }


def _to_alpaca(lecture: dict) -> dict:
    meta = lecture["meta"]
    title = str(meta.get("title") or _slug_to_title(Path(lecture["path"]).stem))
    objective = str(meta.get("objective") or "").strip()
    difficulty = meta.get("difficulty")
    prereqs = [str(p) for p in (meta.get("prerequisites") or [])]

    input_parts = [f"Topic: {title}"]
    if objective:
        input_parts.append(f"Objective: {objective}")
    if prereqs:
        input_parts.append(f"Prerequisites: {', '.join(prereqs)}")
    if difficulty:
        input_parts.append(f"Difficulty: {difficulty}/5")

    return {
        "instruction": (
            "You are an expert educational AI tutor. "
            "Provide a comprehensive, well-structured lecture on the given topic."
        ),
        "input": "\n".join(input_parts),
        "output": lecture["body"],
    }


# ---------------------------------------------------------------------------
# IR scene (Manim code) collection
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    try:
        import json
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _series_title(series_dir: Path) -> str:
    plan = _read_json(series_dir / "course-plan.json")
    if plan.get("title"):
        return str(plan["title"])
    slug = series_dir.name
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
    slug = re.sub(r"^teach-me-(?:about-)?", "", slug)
    return re.sub(r"[-_]+", " ", slug).title()


def _lecture_excerpt(series_dir: Path, max_chars: int = 600) -> str:
    for md in sorted(series_dir.glob("lecture-*.md")):
        try:
            post = frontmatter.loads(md.read_text(encoding="utf-8"))
            body = post.content.strip()
            if body:
                return body[:max_chars]
        except Exception:
            pass
    return ""


def collect_ir_scenes(ir_root: Path) -> list[dict]:
    """Return one dict per scene.py in content/ir/series/**/videos/**."""
    series_root = ir_root / "series"
    if not series_root.is_dir():
        series_root = ir_root

    scenes: list[dict] = []
    for series_dir in sorted(series_root.iterdir()):
        if not series_dir.is_dir():
            continue
        stitle = _series_title(series_dir)
        excerpt = _lecture_excerpt(series_dir)
        videos_dir = series_dir / "videos"
        if not videos_dir.is_dir():
            continue

        for lecture_dir in sorted(videos_dir.iterdir()):
            if not lecture_dir.is_dir():
                continue
            lecture_title = _scene_slug_to_title(lecture_dir.name)

            for scene_dir in sorted(lecture_dir.iterdir()):
                if not scene_dir.is_dir():
                    continue
                scene_py = scene_dir / "scene.py"
                if not scene_py.is_file():
                    continue
                try:
                    code = scene_py.read_text(encoding="utf-8").strip()
                except OSError:
                    continue
                if not code:
                    continue

                scene_title = _scene_slug_to_title(scene_dir.name)
                scenes.append(
                    {
                        "series_title": stitle,
                        "lecture_title": lecture_title,
                        "scene_title": scene_title,
                        "code": code,
                        "excerpt": excerpt,
                    }
                )
    return scenes


def _to_sharegpt_code(scene: dict) -> dict:
    human = (
        f"Write a Manim animation scene titled '{scene['scene_title']}' "
        f"for the lecture '{scene['lecture_title']}' from the course '{scene['series_title']}'."
    )
    if scene["excerpt"]:
        human += f"\n\nLecture context:\n{scene['excerpt']}"

    return {
        "conversations": [
            {"from": "system", "value": _MANIM_SYSTEM_PROMPT},
            {"from": "human", "value": human},
            {"from": "gpt", "value": scene["code"]},
        ]
    }


def _to_alpaca_code(scene: dict) -> dict:
    input_text = (
        f"Scene title: {scene['scene_title']}\n"
        f"Lecture: {scene['lecture_title']}\n"
        f"Course: {scene['series_title']}"
    )
    if scene["excerpt"]:
        input_text += f"\n\nContext:\n{scene['excerpt']}"

    return {
        "instruction": (
            "Write a complete Manim Python animation scene for an educational video. "
            "Return only the Python code."
        ),
        "input": input_text,
        "output": scene["code"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def collect_lectures(ir_root: Path) -> list[dict]:
    """Recursively load all .md files under ir_root."""
    lectures = []
    for md_path in sorted(ir_root.rglob("*.md")):
        lecture = _load_lecture(md_path)
        if lecture:
            lectures.append(lecture)
    return lectures


def build_hf_dataset(
    lectures: list[dict],
    fmt: FormatType = "sharegpt",
    scenes: list[dict] | None = None,
) -> "Dataset":
    try:
        from datasets import Dataset
    except ImportError as e:
        raise ImportError(
            "Install the 'training' extras: pip install 'educlaw[training]'"
        ) from e

    rows = [_to_sharegpt(lec) if fmt == "sharegpt" else _to_alpaca(lec) for lec in lectures]

    if scenes:
        code_rows = [
            _to_sharegpt_code(s) if fmt == "sharegpt" else _to_alpaca_code(s)
            for s in scenes
        ]
        rows.extend(code_rows)

    return Dataset.from_list(rows)


def push_to_hub(
    ir_root: Path,
    repo_id: str,
    *,
    token: str | None = None,
    private: bool = True,
    fmt: FormatType = "sharegpt",
    test_size: float = 0.0,
    include_code: bool = True,
) -> str:
    """Collect lectures (and optionally Manim scenes), build a HuggingFace Dataset, push to Hub.

    Args:
        include_code: When True (default), also adds code-generation rows from
            scene.py files found under content/ir/series/**/videos/**/.

    Returns the dataset URL.
    """
    lectures = collect_lectures(ir_root)
    if not lectures:
        raise ValueError(f"No .md files found under {ir_root}")

    scenes: list[dict] | None = None
    if include_code:
        scenes = collect_ir_scenes(ir_root)

    ds = build_hf_dataset(lectures, fmt=fmt, scenes=scenes)

    if test_size > 0.0:
        split_ds: DatasetDict = ds.train_test_split(test_size=test_size, seed=42)
        split_ds.push_to_hub(repo_id, token=token, private=private)
    else:
        ds.push_to_hub(repo_id, split="train", token=token, private=private)

    return f"https://huggingface.co/datasets/{repo_id}"


def push_jsonl_to_hub(
    jsonl_path: Path,
    repo_id: str,
    *,
    token: str | None = None,
    private: bool = True,
    test_size: float = 0.0,
) -> str:
    """Push a pre-built ShareGPT JSONL file directly to HuggingFace Hub.

    Args:
        jsonl_path: Path to the JSONL file (one record per line).
        repo_id: Target HuggingFace dataset repo, e.g. ``myuser/educlaw-lectures``.
        token: HuggingFace token (falls back to $HF_TOKEN in the caller).
        private: Whether to create a private dataset.
        test_size: Fraction held out as test split (0 = train only).

    Returns the dataset URL.
    """
    try:
        from datasets import Dataset
    except ImportError as e:
        raise ImportError(
            "Install the 'training' extras: pip install 'educlaw[training]'"
        ) from e

    rows: list[dict] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    if not rows:
        raise ValueError(f"No records found in {jsonl_path}")

    ds = Dataset.from_list(rows)

    if test_size > 0.0:
        from datasets import DatasetDict as _DatasetDict
        split_ds: _DatasetDict = ds.train_test_split(test_size=test_size, seed=42)
        split_ds.push_to_hub(repo_id, token=token, private=private)
    else:
        ds.push_to_hub(repo_id, split="train", token=token, private=private)

    return f"https://huggingface.co/datasets/{repo_id}"


# ---------------------------------------------------------------------------
# Manim SFT dataset push
# ---------------------------------------------------------------------------

def _validate_messages_record(record: dict) -> bool:
    """Return True if record has valid Gemma4 messages format."""
    msgs = record.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        return False
    roles = [m.get("role") for m in msgs]
    if "user" not in roles or "assistant" not in roles:
        return False
    return all(isinstance(m.get("content"), str) and m.get("content") for m in msgs)


def load_manim_sft(jsonl_path: Path) -> tuple[list[dict], dict]:
    """Load and validate a Manim SFT JSONL.

    Returns ``(rows, stats)`` where stats includes counts for reporting.
    Skips malformed records silently.
    """
    rows: list[dict] = []
    skipped = 0
    topics: set[str] = set()
    code_lengths: list[int] = []

    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if not _validate_messages_record(rec):
            skipped += 1
            continue
        rows.append(rec)
        if rec.get("topic"):
            topics.add(rec["topic"])
        # Measure assistant (code) length
        for msg in rec.get("messages", []):
            if msg.get("role") == "assistant":
                code_lengths.append(len(msg["content"]))

    avg_code = int(sum(code_lengths) / len(code_lengths)) if code_lengths else 0
    stats = {
        "total": len(rows),
        "skipped": skipped,
        "unique_topics": len(topics),
        "avg_code_chars": avg_code,
    }
    return rows, stats


def push_manim_sft_to_hub(
    jsonl_path: Path,
    repo_id: str,
    *,
    token: str | None = None,
    private: bool = True,
    test_size: float = 0.0,
) -> tuple[str, dict]:
    """Push the Manim SFT JSONL (messages format) to HuggingFace Hub.

    Validates that every record has the Gemma4 ``messages`` format
    (role/content pairs with at least a user and assistant turn).

    Args:
        jsonl_path: Path to ``dataset/manim_sft.jsonl``.
        repo_id: Target HuggingFace dataset repo.
        token: HuggingFace token (falls back to $HF_TOKEN in the caller).
        private: Whether to create a private dataset.
        test_size: Fraction held out as test split (0 = train only).

    Returns ``(dataset_url, stats_dict)``.
    """
    try:
        from datasets import Dataset
    except ImportError as e:
        raise ImportError(
            "Install the 'training' extras: pip install 'educlaw[training]'"
        ) from e

    rows, stats = load_manim_sft(jsonl_path)
    if not rows:
        raise ValueError(
            f"No valid messages-format records found in {jsonl_path}. "
            f"Skipped {stats['skipped']} malformed lines."
        )

    ds = Dataset.from_list(rows)

    if test_size > 0.0:
        from datasets import DatasetDict as _DatasetDict
        split_ds: _DatasetDict = ds.train_test_split(test_size=test_size, seed=42)
        split_ds.push_to_hub(repo_id, token=token, private=private)
    else:
        ds.push_to_hub(repo_id, split="train", token=token, private=private)

    url = f"https://huggingface.co/datasets/{repo_id}"
    return url, stats
