from manim import *

class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Pythagorean Theorem", font_size=48)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        # Create right triangle
        a = 3
        b = 4
        c = 5
        
        triangle = Polygon(
            [0, 0, 0], [a, 0, 0], [0, b, 0],
            color=WHITE
        )
        
        # Labels for sides
        label_a = MathTex("a").next_to(triangle.get_bottom(), DOWN)
        label_b = MathTex("b").next_to(triangle.get_left(), LEFT)
        label_c = MathTex("c").move_to(triangle.get_center() + RIGHT * 0.5 + UP * 0.5)

        self.play(Create(triangle))
        self.play(Write(label_a), Write(label_b))
        self.wait(1)

        # Equation
        equation = MathTex("a^2 + b^2 = c^2").next_to(triangle, DOWN, buff=1)
        self.play(Write(equation))
        self.wait(1)

        # Highlight sides and show c
        self.play(Write(label_c))
        self.play(Indicate(triangle))
        self.wait(2)
