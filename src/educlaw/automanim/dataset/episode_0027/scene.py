"""
Dead ReLU Neurons Visualization
Shows how negative inputs kill gradients and prevent weight updates.
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Dead ReLU Neurons", font_size=42, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)
        
        # Create axes for ReLU function
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-1, 4, 1],
            x_length=6,
            y_length=3.5,
            axis_config={"include_tip": True},
        )
        axes.next_to(title, DOWN, buff=0.5)
        
        x_label = MathTex("x").next_to(axes.x_axis.get_end(), RIGHT)
        y_label = MathTex("f(x)").next_to(axes.y_axis.get_end(), UP)
        
        self.play(Create(axes), Write(x_label), Write(y_label), run_time=1)
        
        # ReLU function
        relu_graph = axes.plot(
            lambda x: max(0, x),
            x_range=[-4, 4],
            color=BLUE,
            stroke_width=4,
        )
        self.play(Create(relu_graph), run_time=1)
        self.wait(0.3)
        
        # Dead zone
        dead_zone = Rectangle(
            width=axes.c2p(0, 0)[0] - axes.c2p(-4, 0)[0],
            height=axes.c2p(0, 4)[1] - axes.c2p(0, -1)[1],
            fill_color=RED,
            fill_opacity=0.3,
            stroke_color=RED,
            stroke_width=2,
        )
        dead_zone.move_to([
            (axes.c2p(-4, 0)[0] + axes.c2p(0, 0)[0]) / 2,
            (axes.c2p(0, -1)[1] + axes.c2p(0, 4)[1]) / 2,
            0
        ])
        
        dead_text = Text("DEAD ZONE", color=RED, font_size=18)
        dead_text.move_to(dead_zone.get_center())
        
        self.play(FadeIn(dead_zone), Write(dead_text), run_time=0.8)
        self.wait(0.3)
        
        # Sample point
        sample_point = Dot(axes.c2p(-2, 0), color=RED, radius=0.1)
        output_text = MathTex("f(-2) = 0", color=WHITE).scale(0.7)
        output_text.next_to(axes, LEFT, buff=0.3)
        
        self.play(FadeIn(sample_point), Write(output_text), run_time=0.6)
        self.wait(0.3)
        
        # Gradient explanation
        grad_text = MathTex("\\frac{df}{dx} = 0 \\text{ for } x < 0", color=RED).scale(0.7)
        grad_text.to_corner(UL, buff=0.3)
        
        zero_arrow = Arrow(
            sample_point.get_center() + UP * 0.2,
            sample_point.get_center() + DOWN * 0.2,
            color=RED,
            buff=0,
            stroke_width=5,
        )
        
        self.play(
            FadeOut(dead_text),
            Write(grad_text),
            GrowArrow(zero_arrow),
            run_time=0.8
        )
        self.wait(0.3)
        
        # Weight update explanation
        self.play(
            FadeOut(zero_arrow),
            FadeOut(grad_text),
            FadeOut(output_text),
            FadeOut(sample_point),
            run_time=0.3
        )
        
        # Weight update equations
        weight_eq = MathTex(
            "w_{\\text{new}} = w_{\\text{old}} - \\eta \\cdot \\frac{\\partial L}{\\partial w}",
            color=WHITE
        ).scale(0.65)
        weight_eq.next_to(axes, RIGHT, buff=0.3)
        
        chain_eq = MathTex(
            "\\frac{\\partial L}{\\partial w} = \\frac{\\partial L}{\\partial f} \\cdot \\mathbf{0} = 0",
            color=RED
        ).scale(0.6)
        chain_eq.next_to(weight_eq, DOWN, aligned_edge=LEFT, buff=0.3)
        
        result_eq = MathTex("\\Rightarrow w_{\\text{new}} = w_{\\text{old}}", color=YELLOW).scale(0.65)
        result_eq.next_to(chain_eq, DOWN, aligned_edge=LEFT, buff=0.3)
        
        self.play(Write(weight_eq), run_time=0.8)
        self.play(Write(chain_eq), run_time=0.8)
        self.play(Write(result_eq), run_time=0.6)
        self.wait(0.3)
        
        # Final dead neuron
        skull = Text("X", font_size=48, color=RED)
        skull.move_to(dead_zone.get_center())
        
        self.play(
            FadeOut(dead_zone, run_time=0.3),
            FadeIn(skull),
            run_time=0.6
        )
        
        dead_label = Text("DEAD NEURON", font_size=22, color=RED, weight=BOLD)
        dead_label.next_to(skull, DOWN)
        
        frozen_text = Text("Weights frozen!", font_size=16, color=GRAY)
        frozen_text.next_to(dead_label, DOWN)
        
        self.play(Write(dead_label), run_time=0.5)
        self.play(Write(frozen_text), run_time=0.4)
        self.wait(0.5)
        
        # Summary
        self.play(
            FadeOut(title),
            FadeOut(axes),
            FadeOut(x_label),
            FadeOut(y_label),
            FadeOut(relu_graph),
            FadeOut(weight_eq),
            FadeOut(chain_eq),
            FadeOut(result_eq),
            FadeOut(skull),
            FadeOut(dead_label),
            FadeOut(frozen_text),
            run_time=0.8
        )
        
        summary = Text(
            "x < 0  →  gradient = 0  →  no weight update",
            font_size=26,
            color=YELLOW
        )
        self.play(Write(summary), run_time=1)
        self.wait(0.8)
        self.play(FadeOut(summary), run_time=0.5)
