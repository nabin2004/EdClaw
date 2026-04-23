from educlaw.automanim.critic import static_critic


def test_static_critic_rejects_show_creation() -> None:
    src = """
from manim import *
class X(Scene):
    def construct(self):
        self.play(ShowCreation(Dot()))
"""
    r = static_critic(src, max_source_bytes=100_000)
    assert not r.ok
    assert "ShowCreation" in r.feedback or "Forbidden" in r.feedback


def test_static_critic_accepts_minimal_scene() -> None:
    src = """
from manim import *
class X(Scene):
    def construct(self):
        self.add(Dot())
"""
    r = static_critic(src, max_source_bytes=100_000)
    assert r.ok
