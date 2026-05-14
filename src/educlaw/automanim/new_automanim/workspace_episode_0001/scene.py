from manim import *

class AutoScene(Scene):
    def construct(self):
        circle = Circle()
        square = Square()
        
        self.play(Create(circle))
        self.wait(1)
        self.play(ReplacementTransform(circle, square))
        self.wait(2)
