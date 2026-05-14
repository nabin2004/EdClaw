from manim import *
import numpy as np

class AutoScene(Scene):
    def construct(self):
        # 1. Create Right Triangle
        a = 3
        b = 4
        c = 5
        
        triangle = Polygon(
            [0, 0, 0],
            [b, 0, 0],
            [0, a, 0],
            color=WHITE
        )
        
        # Labels for sides
        label_a = MathTex("a").next_to(triangle.get_vertices()[2], LEFT)
        label_b = MathTex("b").next_to(triangle.get_vertices()[1], DOWN)
        label_c = MathTex("c").move_to(triangle.get_center() + RIGHT * 0.5 + UP * 0.5)
        
        # 2. Create Squares
        # square_a is on the left side (vertical)
        square_a = Square(side_length=a, fill_opacity=0.5, color=BLUE)
        square_a.next_to(triangle, LEFT, buff=0).align_to(triangle, DOWN)
        
        # square_b is on the bottom side (horizontal)
        square_b = Square(side_length=b, fill_opacity=0.5, color=GREEN)
        square_b.next_to(triangle, DOWN, buff=0).align_to(triangle, LEFT)
        
        # square_c is on the hypotenuse
        # Vertices of triangle: P1=(0,a), P2=(0,0), P3=(b,0)
        # Hypotenuse: P1 to P3.
        # Midpoint: (b/2, a/2)
        # Angle of hypotenuse: atan2(-a, b)
        angle_h = np.arctan2(-a, b)
        square_c = Square(side_length=c, fill_opacity=0.5, color=RED)
        square_c.rotate(angle_h)
        # Center: midpoint of hypotenuse + (c/2) * normal_unit_vector
        # Normal vector to (b, -a) is (a, b)
        # Unit normal: (a/c, b/c)
        # Center: (b/2 + a/2, a/2 + b/2)
        square_c.move_to([b/2 + a/2, a/2 + b/2, 0])

        # 3. Animation Sequence
        self.play(Create(triangle))
        self.play(Write(label_a), Write(label_b))
        self.play(Write(label_c))
        self.wait(1)
        
        self.play(FadeIn(square_a), FadeIn(square_b))
        self.wait(1)
        self.play(FadeIn(square_c))
        self.wait(1)
        
        # 4. Show Formula
        formula = MathTex("a^2 + b^2 = c^2").to_edge(UP)
        self.play(Write(formula))
        self.wait(2)

        # Final cleanup/emphasis
        self.play(Indicate(square_a), Indicate(square_b), Indicate(square_c))
        self.wait(1)
