"""Static (and optional LLM) review of generated Manim source."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ollama import AsyncClient

from educlaw.viz import extract_python, has_manim_scene, scene_class_name, syntax_ok


@dataclass
class CriticResult:
    ok: bool
    feedback: str


_MANIM_GL_PATTERNS = (
    r"\bShowCreation\b",
    r"\bCONFIG\s*=",
    r"manim_imports_ext",
    r"\bGraphScene\b",
)


def static_critic(source: str, *, max_source_bytes: int) -> CriticResult:
    raw = source or ""
    if len(raw.encode("utf-8")) > max_source_bytes:
        return CriticResult(ok=False, feedback="Source exceeds max_source_bytes limit.")
    code = extract_python(raw)
    if not syntax_ok(code):
        return CriticResult(ok=False, feedback="Python syntax error; fix parsing issues.")
    if not has_manim_scene(code):
        return CriticResult(ok=False, feedback="No class inheriting from Scene found.")
    if scene_class_name(code) is None:
        return CriticResult(ok=False, feedback="Could not detect class Name(Scene) pattern.")
    for pat in _MANIM_GL_PATTERNS:
        if re.search(pat, code):
            return CriticResult(
                ok=False,
                feedback=f"Forbidden pattern for Manim CE detected ({pat}); use CE APIs only.",
            )
    return CriticResult(ok=True, feedback="")


async def llm_critic_review(client: AsyncClient, model: str, code: str) -> CriticResult:
    """Optional second pass: short model verdict ALLOW / REJECT."""
    snippet = extract_python(code)[:12_000]
    sys = (
        "You review Manim Community Edition Python for a sandboxed render. "
        "Reject if the code imports os/subprocess/socket, opens files outside the script, "
        "or uses obvious non-Manim side effects. "
        "Reply with exactly one line: ALLOW or REJECT: <brief reason>."
    )
    out = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": snippet},
        ],
        options={"temperature": 0, "num_predict": 128},
    )
    msg = ((out.get("message") or {}).get("content") or "").strip()
    upper = msg.upper()
    if upper.startswith("REJECT"):
        return CriticResult(ok=False, feedback=msg or "LLM critic rejected.")
    return CriticResult(ok=True, feedback="")
