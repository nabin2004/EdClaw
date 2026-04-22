"""Version-conflict and GL-hallucination patterns (ManiBench / paper Table 3 categories)."""

import re
from dataclasses import dataclass

# 40+ style patterns; each match increments VCER signal
GL_BAN_PATTERNS: list[tuple[str, str]] = [
    (r"manim_imports_ext", "import_system: manim_imports_ext"),
    (r"from\s+manimlib", "import_system: manimlib"),
    (r"import\s+manimlib", "import_system: manimlib"),
    (r"\bCONFIG\s*=\s*\{", "class_config: CONFIG dict"),
    (r"\bShowCreation\s*\(", "animation: ShowCreation (use Create)"),
    (r"\bFadeInFrom\s*\(", "animation: FadeInFrom (use FadeIn(shift=...))"),
    (r"\bInteractiveScene\b", "scene: InteractiveScene"),
    (r"\bGraphScene\b", "scene: GraphScene (use Scene/Axes)"),
    (r"\bPiCreature\b", "pi_creature: not in CE"),
    (r"\bMobjectFromRegion\b", "gl_mobject: possible GL-only"),
    (r"apply_depth_test", "3d: apply_depth_test"),
    (r"set_shading\s*\(", "3d: set_shading"),
    (r"frame\.reorient\s*\(", "camera: frame.reorient (use camera.frame)"),
    (r"self\.frame\.reorient", "camera: self.frame.reorient"),
    (r"\bFadeOutAndShift\s*\(", "animation: check CE name"),
    (r"OpenGL", "gl: OpenGL-specific"),
    (r"from\s+manim\.mobject\.types\.point_cloud_mobject\s+import\s+Mobject1D", "import: legacy"),
    (r"\bMCircle\b", "hallucination: MCircle (use Circle)"),
    (r"\bShowPassingFlashWithThinningStrokeWidth\b", "gl: long GL name"),
]

# Precompiled
_COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p, re.IGNORECASE), reason) for p, reason in GL_BAN_PATTERNS
]


@dataclass
class VCERResult:
    """True if any GL/deprecated pattern matched (treat as version conflict)."""

    vcer: float  # 0.0 or 1.0 for this sample (rate is over batch)
    hits: list[str]

    @property
    def has_conflict(self) -> bool:
        return bool(self.hits)


def scan_vcer(source: str) -> VCERResult:
    """Return 1.0 if any known GL/invalid-for-CE pattern is present."""
    hits: list[str] = []
    for pat, reason in _COMPILED:
        if pat.search(source):
            hits.append(reason)
    v = 1.0 if hits else 0.0
    return VCERResult(vcer=v, hits=hits)
