import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from datasets import Dataset

LOCAL_JSON = Path(__file__).parent / "ManiBench" / "ManiBench_Pilot_Dataset.json"
HF_REPO = "nabin2004/ManiBench"
HF_FILENAME = "ManiBench_Pilot_Dataset.json"


@lru_cache(maxsize=1)
def _load_problems() -> Dict[str, dict]:
    if LOCAL_JSON.is_file():
        path = LOCAL_JSON
    else:
        from huggingface_hub import hf_hub_download

        path = Path(
            hf_hub_download(HF_REPO, HF_FILENAME, repo_type="dataset"),
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {p["id"]: p for p in data["problems"]}


def build_dataset() -> Dataset:
    problems = _load_problems()
    rows = [
        {
            "prompt": [{"role": "user", "content": p["full_prompt"]}],
            "problem_id": pid,
        }
        for pid, p in problems.items()
    ]
    return Dataset.from_list(rows)


# ---------- VCER patterns -------------------------------------------------------

_BASE_VCER_PATTERNS: List[str] = [
    r"from\s+manim_imports_ext\s+import",
    r"from\s+manim_gl\s+import",
    r"\bCONFIG\s*=\s*\{",
    r"\bInteractiveScene\b",
    r"\bReconfigurableScene\b",
    r"\bGraphScene\b",
    r"\bShowCreation\b",
    r"\bFadeInFrom\s*\(",
    r"\bPiCreature\b",
    r"\bTeacherStudentsScene\b",
    r"\bapply_depth_test\s*\(",
    r"\bset_shading\s*\(",
    r"\.reorient\s*\(",
    r"\bGlowDot\b",
    r"\bDieFace\b",
    r"\bOldTex\b",
    r"\bOldTexText\b",
    r"\bforce_skipping\s*\(",
    r"\bfix_in_frame\s*\(",
    r"\bset_floor_plane\s*\(",
]


def get_vcer_patterns(problem_id: str) -> List[str]:
    """Base ManimGL→CE conflict patterns extended with problem-specific ones."""
    problems = _load_problems()
    patterns = list(_BASE_VCER_PATTERNS)
    incompats = problems.get(problem_id, {}).get("version_conflict_notes", {}).get(
        "known_incompatibilities", [],
    )
    for entry in incompats:
        token = re.split(r"[\s().→/]", entry.split("→")[0].strip())[0].strip()
        if len(token) > 2:
            patterns.append(rf"\b{re.escape(token)}\b")
    return list(dict.fromkeys(patterns))  # deduplicated, order preserved


# ---------- Alignment events ----------------------------------------------------

_COMPOUND_CAMEL = re.compile(r'\b([A-Z][a-z]{2,}(?:[A-Z][a-z]{2,})+)\b')
_CALL_NAME      = re.compile(r'\b([A-Z][a-z]{2,})\s*(?=\()')


def _event_detection_patterns(event: dict) -> List[str]:
    text  = event.get("description", "") + " " + event.get("reference_code_lines", "")
    names = set(_COMPOUND_CAMEL.findall(text) + _CALL_NAME.findall(text))
    return [rf"\b{re.escape(n)}\b" for n in names]


def get_alignment_events(problem_id: str) -> List[Tuple[float, List[str]]]:
    """Returns [(weight, [detection_patterns]), ...] per required visual event."""
    problems = _load_problems()
    events = problems.get(problem_id, {}).get("required_visual_events", [])
    return [(e["weight"], _event_detection_patterns(e)) for e in events]


# ---------- Coverage terms ------------------------------------------------------

_CODE_TERMS = re.compile(r'\b([A-Z][a-zA-Z0-9]{3,}|[a-z]{3,}_[a-z_]+)\b')


def get_coverage_terms(problem_id: str) -> List[str]:
    """Code-like tokens extracted from per-problem coverage_requirements."""
    problems = _load_problems()
    terms: List[str] = []
    for req in problems.get(problem_id, {}).get("coverage_requirements", []):
        paren = re.findall(r'\(([A-Za-z][A-Za-z0-9_]{2,})\)', req)
        terms.extend(paren if paren else _CODE_TERMS.findall(req))
    return list(dict.fromkeys(terms))
