"""
Batch Normalization Animation
Shows shifting and scaling of activation distributions
"""
from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Setup axes
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[0, 0.6, 0.1],
            x_length=10,
            y_length=4,
            axis_config={"color": WHITE},
            tips=False,
        ).shift(UP * 0.5)

        axes_labels = axes.get_axis_labels(
            x_label=MathTex("x", color=WHITE),
            y_label=MathTex("p(x)", color=WHITE),
        )

        self.play(Create(axes), Write(axes_labels))
        self.wait(0.5)

        # Original Gaussian (shifted)
        def gaussian(x, mu, sigma):
            return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

        # Original distribution (shifted and scaled)
        original_curve = axes.plot(
            lambda x: gaussian(x, 1.5, 0.8),
            x_range=[-4, 4],
            color=BLUE,
            stroke_width=3,
        )

        original_label = MathTex(r"\text{Original: } \mu=1.5, \sigma=0.8", color=BLUE).scale(0.7)
        original_label.next_to(axes.c2p(-2, 0.5), UP + LEFT)

        # Mean line
        mean_line_before = DashedLine(
            axes.c2p(1.5, 0),
            axes.c2p(1.5, 0.5),
            color=YELLOW,
            stroke_width=2,
        )
        mean_label_before = MathTex(r"\mu", color=YELLOW).scale(0.7)
        mean_label_before.next_to(mean_line_before.get_end(), UP + RIGHT, buff=0.1)

        self.play(
            Create(original_curve),
            Write(original_label),
            Create(mean_line_before),
            Write(mean_label_before),
        )
        self.wait(0.8)

        # Step 1: Subtract mean (shift to center)
        step1_text = Text("Step 1: Subtract Mean", font_size=28, color=YELLOW)
        step1_text.to_edge(DOWN, buff=0.5)
        self.play(Write(step1_text))
        self.wait(0.5)

        # Shift mean to 0
        centered_curve = axes.plot(
            lambda x: gaussian(x, 0, 0.8),
            x_range=[-4, 4],
            color=GREEN,
            stroke_width=3,
        )

        centered_label = MathTex(r"\text{Centered: } \mu=0", color=GREEN).scale(0.7)
        centered_label.next_to(axes.c2p(0, 0.5), UP, buff=0.2)

        mean_line_center = DashedLine(
            axes.c2p(0, 0),
            axes.c2p(0, 0.5),
            color=YELLOW,
            stroke_width=2,
        )

        self.play(
            Transform(original_curve, centered_curve),
            Transform(original_label, centered_label),
            Transform(mean_line_before, mean_line_center),
            FadeOut(mean_label_before),
        )
        self.wait(0.8)

        # Step 2: Divide by standard deviation (scale)
        step2_text = Text("Step 2: Divide by Std Dev", font_size=28, color=ORANGE)
        step2_text.to_edge(DOWN, buff=0.5)
        self.play(Transform(step1_text, step2_text))
        self.wait(0.5)

        # Scale to unit variance
        normalized_curve = axes.plot(
            lambda x: gaussian(x, 0, 1),
            x_range=[-4, 4],
            color=RED,
            stroke_width=3,
        )

        normalized_label = MathTex(r"\text{Normalized: } \mu=0, \sigma=1", color=RED).scale(0.7)
        normalized_label.next_to(axes.c2p(0, 0.4), UP, buff=0.2)

        # Variance annotation
        var_line_left = DashedLine(
            axes.c2p(-1, 0),
            axes.c2p(-1, 0.24),
            color=ORANGE,
            stroke_width=2,
        )
        var_line_right = DashedLine(
            axes.c2p(1, 0),
            axes.c2p(1, 0.24),
            color=ORANGE,
            stroke_width=2,
        )

        self.play(
            Transform(original_curve, normalized_curve),
            Transform(original_label, normalized_label),
            Create(var_line_left),
            Create(var_line_right),
        )
        self.wait(0.8)

        # Step 3: Learnable parameters (scale and shift)
        step3_text = Text("Step 3: Learnable Scale (γ) and Shift (β)", font_size=26, color=PURPLE)
        step3_text.to_edge(DOWN, buff=0.5)
        self.play(Transform(step1_text, step3_text))
        self.wait(0.5)

        # Apply gamma and beta
        gamma, beta = 1.5, 0.5

        final_curve = axes.plot(
            lambda x: gaussian(x, beta, 1 / gamma),
            x_range=[-4, 4],
            color=PURPLE,
            stroke_width=3,
        )

        final_label = MathTex(r"\text{Final: } \gamma=1.5, \beta=0.5", color=PURPLE).scale(0.7)
        final_label.next_to(axes.c2p(beta, 0.25), UP, buff=0.2)

        final_mean_line = DashedLine(
            axes.c2p(beta, 0),
            axes.c2p(beta, 0.25),
            color=PURPLE_A,
            stroke_width=2,
        )

        # Formula
        formula = MathTex(
            r"y = \gamma \cdot \frac{x - \mu}{\sigma} + \beta",
            color=WHITE,
        ).scale(0.9)
        formula.next_to(step3_text, UP, buff=0.3)

        self.play(
            Transform(original_curve, final_curve),
            Transform(original_label, final_label),
            Transform(mean_line_before, final_mean_line),
            FadeOut(var_line_left),
            FadeOut(var_line_right),
            Write(formula),
        )
        self.wait(1.5)

        # Final summary
        summary = VGroup(
            Text("Batch Normalization", font_size=32, color=WHITE),
            Text("Stabilizes training by normalizing activations", font_size=24, color=GRAY),
        ).arrange(DOWN, buff=0.3)
        summary.to_edge(DOWN, buff=0.4)

        self.play(
            FadeOut(step1_text),
            FadeOut(formula),
            FadeOut(original_label),
            Write(summary),
        )
        self.wait(1.5)

        self.play(
            FadeOut(summary),
            FadeOut(axes),
            FadeOut(axes_labels),
            FadeOut(original_curve),
            FadeOut(mean_line_before),
        )
        self.wait(0.5)
