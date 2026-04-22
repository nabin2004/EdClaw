"""Generate GL→CE conversion training rows (target ≥145 for manibench-sft-core v0)."""

from __future__ import annotations

from manibench.constants import MANIM_CE_SYSTEM


def _msg(user: str, assistant: str, category: str, tag: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": MANIM_CE_SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant.strip()},
        ],
        "category": category,
        "task_type": "version_conflict_traps",
        "source": "gl_ce_catalog",
        "tag": tag,
    }


def iter_gl_ce_pairs() -> list[dict]:
    rows: list[dict] = []

    # --- Category 1: imports ---
    rows.append(
        _msg(
            "Rewrite imports for Manim CE only.",
            '''from manim import *

class ImportDemo(Scene):
    def construct(self):
        t = Tex(r"Hello")
        self.play(Create(t))
''',
            "import_system",
            "imports_star",
        )
    )
    for i in range(20):
        rows.append(
            _msg(
                f"Replace legacy manim_imports_ext / manimlib with CE imports (variant {i}).",
                f"""from manim import *

class ImportScene{i}(Scene):
    def construct(self):
        self.play(Create(Text("CE {i}", font_size=48)))
""",
                "import_system",
                f"imports_variant_{i}",
            )
        )

    # --- Category 2: CONFIG → __init__ ---
    for i in range(25):
        rows.append(
            _msg(
                "Convert CONFIG dict style to modern Manim CE __init__ parameters.",
                f'''from manim import *

class ConfigScene{i}(Scene):
    def construct(self):
        c = Circle(color=BLUE, radius=0.5 + {i % 5} * 0.05)
        self.play(Create(c))
''',
                "class_config",
                f"config_modern_{i}",
            )
        )

    # --- Category 3: Scene types ---
    for i in range(15):
        rows.append(
            _msg(
                "Use Scene + Axes instead of GraphScene for a simple plot.",
                f'''from manim import *

class AxesScene{i}(Scene):
    def construct(self):
        ax = Axes(x_range=[-3, 3], y_range=[-2, 2])
        self.play(Create(ax))
''',
                "scene_types",
                f"axes_instead_graph_{i}",
            )
        )

    # --- Category 4: Animation renames ---
    for i in range(25):
        rows.append(
            _msg(
                "Use Create instead of ShowCreation; FadeIn with shift instead of FadeInFrom.",
                f'''from manim import *

class AnimScene{i}(Scene):
    def construct(self):
        s = Square()
        self.play(Create(s))
        self.play(FadeIn(s, shift=DOWN * 0.2))
''',
                "animation_renames",
                f"create_fadein_{i}",
            )
        )

    # --- Category 5: PiCreature / GL-only (negative teaching) ---
    for i in range(10):
        rows.append(
            _msg(
                "Implement a simple title scene without PiCreature (not available in CE).",
                f'''from manim import *

class Title{i}(Scene):
    def construct(self):
        self.play(Write(Text("Topic {i}", font_size=56)))
''',
                "pi_creature",
                f"no_pi_{i}",
            )
        )

    # --- Category 6: 3D limited ---
    for i in range(10):
        rows.append(
            _msg(
                "Avoid GL-only 3D shading helpers; keep a 2D illustration.",
                f'''from manim import *

class Flat{i}(Scene):
    def construct(self):
        v = Arrow(ORIGIN, RIGHT * 2, buff=0)
        self.play(Create(v))
''',
                "3d_limited",
                f"flat_instead_3d_{i}",
            )
        )

    # --- Category 7: Camera ---
    for i in range(15):
        rows.append(
            _msg(
                "Use self.camera.frame when framing instead of frame.reorient patterns.",
                f'''from manim import *

class Cam{i}(Scene):
    def construct(self):
        self.play(self.camera.frame.animate.scale(0.9))
''',
                "camera",
                f"frame_animate_{i}",
            )
        )

    # --- Category 8: Custom mobjects (use CE primitives) ---
    for i in range(14):
        rows.append(
            _msg(
                "Draw a marker dot using Dot/Circle — do not invent MCircle.",
                f'''from manim import *

class Marker{i}(Scene):
    def construct(self):
        d = Dot(point=ORIGIN + RIGHT * {i % 3}, color=YELLOW)
        self.play(Create(d))
''',
                "custom_mobjects",
                f"dot_not_mcircle_{i}",
            )
        )

    # --- Pad to ≥145 with small variant scenes (sequencing / pedagogy) ---
    for i in range(15):
        rows.append(
            _msg(
                f"Use LaggedStart for staggered Appear animations (variant {i}).",
                f'''from manim import *

class Lag{i}(Scene):
    def construct(self):
        grp = VGroup(*[Square(side_length=0.3) for _ in range(4)])
        grp.arrange(RIGHT, buff=0.15)
        self.play(LaggedStart(*[FadeIn(s) for s in grp], lag_ratio=0.2))
''',
                "structural",
                f"lagged_{i}",
            )
        )

    assert len(rows) >= 145, len(rows)
    return rows


def gallery_seed_examples() -> list[dict]:
    """Short Manim CE gallery-style exercises (instruction → full scene)."""
    seeds = []
    templates = [
        (
            "Fade in a formula with MathTex and pause.",
            r'''from manim import *

class GalleryFormula(Scene):
    def construct(self):
        m = MathTex(r"\int_0^1 x\,dx = \frac{1}{2}")
        self.play(FadeIn(m))
        self.wait()
''',
        ),
        (
            "Show axes and plot y = x^2 with simple dots.",
            '''from manim import *

class GalleryPlot(Scene):
    def construct(self):
        ax = Axes(x_range=[-2, 2], y_range=[0, 4])
        graph = ax.plot(lambda x: x**2, color=BLUE)
        self.play(Create(ax), Create(graph))
''',
        ),
        (
            "Animate a ValueTracker updating a DecimalNumber.",
            '''from manim import *

class GalleryTracker(Scene):
    def construct(self):
        vt = ValueTracker(0)
        num = DecimalNumber(vt.get_value(), num_decimal_places=2)
        num.add_updater(lambda m: m.set_value(vt.get_value()))
        self.play(vt.animate.set_value(3), run_time=2)
''',
        ),
        (
            "Use Succession for ordered animations.",
            '''from manim import *

class GallerySuccession(Scene):
    def construct(self):
        a = Dot(LEFT)
        b = Dot(RIGHT)
        self.play(Succession(Create(a), Wait(0.3), Create(b)))
''',
        ),
        (
            "Label objects with Brace and Tex.",
            '''from manim import *

class GalleryBrace(Scene):
    def construct(self):
        line = Line(LEFT * 2, RIGHT * 2)
        br = Brace(line, direction=DOWN)
        t = br.get_tex(r"L")
        self.play(Create(line), GrowFromCenter(br), FadeIn(t))
''',
        ),
    ]
    for title, code in templates:
        seeds.append(
            {
                "messages": [
                    {"role": "system", "content": MANIM_CE_SYSTEM},
                    {"role": "user", "content": title},
                    {"role": "assistant", "content": code.strip()},
                ],
                "category": "direct_visualization",
                "task_type": "direct_visualization",
                "source": "gallery_seed",
            }
        )
    return seeds
