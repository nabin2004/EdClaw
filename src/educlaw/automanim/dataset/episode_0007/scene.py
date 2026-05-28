"""Manim animation of a single neuron computing weighted sum + ReLU."""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Scene configuration
        self.camera.background_color = "#1a1a2e"

        # Title
        title = Text("Single Neuron: Weighted Sum + ReLU", font_size=32, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(FadeIn(title))
        self.wait(0.3)

        # Input values
        input_vals = [3.0, 2.0, -1.0]
        input_labels = VGroup(*[
            VGroup(
                Circle(radius=0.25, color=BLUE, fill_opacity=0.3),
                Text(f"x{i+1}", font_size=16, color=WHITE),
                Text(f"{v:.1f}", font_size=14, color=YELLOW).shift(DOWN * 0.5)
            ) for i, v in enumerate(input_vals)
        ]).arrange(DOWN, buff=0.6).shift(LEFT * 4)

        # Animate inputs appearing
        for input_group in input_labels:
            self.play(FadeIn(input_group[0]), FadeIn(input_group[1]), FadeIn(input_group[2]), run_time=0.3)
        self.wait(0.3)

        # Neuron (circle in the middle)
        neuron = VGroup(
            Circle(radius=0.6, color=GREEN, fill_opacity=0.4, stroke_width=3),
            Text("Σ", font_size=28, color=WHITE)
        )
        neuron.shift(RIGHT * 0.5)
        self.play(FadeIn(neuron), run_time=0.5)
        self.wait(0.3)

        # Weights and connections with arrows
        weights = [0.5, 1.0, -0.5]
        weight_labels = []
        arrows = []

        for i, (inp, w) in enumerate(zip(input_labels, weights)):
            # Arrow from input to neuron
            arrow = Line(
                inp[0].get_center() + RIGHT * 0.25,
                neuron[0].get_left(),
                stroke_width=2,
                color=GRAY_A
            )
            # Weight label
            weight_text = Text(f"w{i+1}={w}", font_size=12, color=ORANGE)
            weight_text.move_to(arrow.get_center() + UP * 0.25 + RIGHT * 0.1)
            
            arrows.append(arrow)
            weight_labels.append(weight_text)
            
            self.play(
                Create(arrow),
                FadeIn(weight_text),
                run_time=0.3
            )

        self.wait(0.3)

        # Calculate weighted sum
        weighted_terms = [input_vals[i] * weights[i] for i in range(3)]
        sum_result = sum(weighted_terms)

        # Show calculation steps
        calc_texts = [
            f"z = {input_vals[0]:.1f}×{weights[0]}",
            f"  + {input_vals[1]:.1f}×{weights[1]}",
            f"  + ({input_vals[2]:.1f})×({weights[2]})",
            f"  = {weighted_terms[0]:.1f} + {weighted_terms[1]:.1f} + {weighted_terms[2]:.1f}",
            f"  = {sum_result:.1f}"
        ]

        calc_label = VGroup(*[
            Text(t, font_size=18, color=YELLOW_A) for t in calc_texts
        ]).arrange(DOWN, buff=0.15, aligned_edge=LEFT).to_edge(DOWN, buff=0.8).shift(LEFT * 1)

        for line in calc_label:
            self.play(Write(line), run_time=0.3)

        self.wait(0.4)

        # Show ReLU activation
        self.play(
            calc_label[-1].animate.set_color(GREEN_A),
            run_time=0.3
        )

        # ReLU label appearing
        relu_label = Text("ReLU", font_size=20, color=RED).next_to(neuron, RIGHT, buff=0.3)
        self.play(FadeIn(relu_label), run_time=0.3)

        # ReLU formula
        relu_eq = MathTex(r"f(z) = \max(0, z)", font_size=24, color=WHITE)
        relu_eq.next_to(relu_label, DOWN, buff=0.3)
        self.play(Write(relu_eq), run_time=0.4)
        self.wait(0.3)

        # Calculate ReLU output
        relu_output = max(0, sum_result)
        output_val = Text(f"Output: {relu_output:.1f}", font_size=22, color=GREEN_B)
        output_val.next_to(relu_eq, DOWN, buff=0.4)

        # Arrow to output
        output_arrow = Arrow(
            relu_label.get_right(),
            output_val.get_top() + LEFT * 0.5,
            stroke_width=2,
            color=GREEN,
            buff=0.2
        )

        self.play(
            Create(output_arrow),
            FadeIn(output_val),
            run_time=0.5
        )

        # Highlight final result
        self.play(
            output_val.animate.scale(1.2).set_color(YELLOW),
            run_time=0.3
        )
        self.wait(0.3)

        # Show final equation summary
        summary = MathTex(
            f"f({input_vals[0]:.1f} \\cdot {weights[0]} + {input_vals[1]:.1f} \\cdot {weights[1]} + ({input_vals[2]:.1f}) \\cdot ({weights[2]})) = {relu_output:.1f}",
            font_size=18, color=WHITE
        )
        summary.to_edge(DOWN, buff=0.3)
        
        self.play(FadeOut(calc_label), run_time=0.3)
        self.play(Write(summary), run_time=0.5)
        self.wait(0.5)

        # Final highlight
        self.play(
            Indicate(output_val, scale_factor=1.1, color=YELLOW),
            run_time=0.5
        )
        self.wait(0.5)