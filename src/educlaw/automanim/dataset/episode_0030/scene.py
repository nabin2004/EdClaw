from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Set up example logits
        logits = np.array([2.0, 1.0, 0.0, -0.5])
        labels = ["dog", "cat", "bird", "fish"]

        # Title
        title = Text("Temperature Scaling in Softmax", font_size=40)
        title.to_edge(UP, buff=0.5)

        # Subtitle/description
        subtitle = Text("Controlling probability distribution sharpness", font_size=24)
        subtitle.next_to(title, DOWN, buff=0.2)

        # Formula
        formula = MathTex(r"P(i) = \frac{e^{z_i/T}}{\sum_j e^{z_j/T}}")
        formula.next_to(subtitle, DOWN, buff=0.3)

        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.play(Write(formula))
        self.wait(0.5)

        # Create axes for bar chart
        axes = Axes(
            x_range=[0, 5, 1],
            y_range=[0, 1.2, 0.2],
            x_length=8,
            y_length=4,
            axis_config={"include_tip": False, "numbers_to_exclude": [0, 5]},
            y_axis_config={"numbers_to_include": [0, 0.2, 0.4, 0.6, 0.8, 1.0]},
        )
        axes.to_edge(DOWN, buff=1.5)

        # X-axis labels
        x_labels = VGroup()
        for i, label in enumerate(labels):
            tex = Tex(label, font_size=30)
            tex.next_to(axes.c2p(i + 1, 0), DOWN, buff=0.3)
            x_labels.add(tex)

        # Y-axis label
        y_label = Text("Probability", font_size=20)
        y_label.next_to(axes.y_axis, LEFT, buff=0.3)
        y_label.rotate(90 * DEGREES)

        self.play(Create(axes), Create(x_labels), Write(y_label))

        # Temperature display
        temp_label = Text("Temperature:", font_size=32)
        temp_value = DecimalNumber(1.0, num_decimal_places=1, font_size=40, color=YELLOW)
        temp_display = VGroup(temp_label, temp_value)
        temp_display.arrange(RIGHT, buff=0.3)
        temp_display.next_to(axes, UP, buff=0.5)

        # Effect indicator
        effect_text = Text("", font_size=28)
        effect_text.next_to(temp_display, RIGHT, buff=0.5)

        self.play(Write(temp_display))

        # Softmax calculation with temperature
        def softmax_with_temp(logits, temp):
            scaled = logits / temp
            exp_scaled = np.exp(scaled - np.max(scaled))  # numerical stability
            return exp_scaled / np.sum(exp_scaled)

        # Create initial bars
        def create_bars(probs, color):
            bars = VGroup()
            for i, prob in enumerate(probs):
                bar = Rectangle(
                    width=0.8,
                    height=prob * axes.y_length / 1.2,
                    fill_color=color,
                    fill_opacity=0.9,
                    stroke_color=WHITE,
                    stroke_width=2,
                )
                bar.move_to(axes.c2p(i + 1, 0), aligned_edge=DOWN)

                # Value label on top
                val_label = DecimalNumber(prob, num_decimal_places=2, font_size=20)
                val_label.next_to(bar, UP, buff=0.1)

                bar_group = VGroup(bar, val_label)
                bars.add(bar_group)
            return bars

        # Initial softmax
        probs = softmax_with_temp(logits, 1.0)
        bars = create_bars(probs, BLUE)
        self.play(*[Create(bar_group) for bar_group in bars], run_time=1)
        self.wait(0.5)

        # Animate through different temperatures
        temp_values = [0.3, 0.8, 2.0, 5.0, 1.0]
        colors = [RED_E, RED_D, GREEN_D, GREEN_C, BLUE]
        effects = ["SHARP (peak)", "somewhat sharp", "FLAT (spread)", "very flat", "balanced"]

        for temp, color, effect in zip(temp_values, colors, effects):
            new_probs = softmax_with_temp(logits, temp)
            new_bars = create_bars(new_probs, color)

            # Update effect text
            new_effect_text = Text(effect, font_size=28, color=color)
            new_effect_text.next_to(temp_display, RIGHT, buff=0.5)

            self.play(
                Transform(bars, new_bars),
                temp_value.animate.set_value(temp),
                FadeOut(effect_text) if effect_text.text else FadeIn(new_effect_text),
                run_time=1.5,
            )

            if not effect_text.text:
                effect_text = new_effect_text
            else:
                effect_text = new_effect_text
                self.play(FadeIn(effect_text))

            self.wait(0.7)

        # Final summary
        self.wait(0.5)
        summary = Text("Low T → Confident  |  High T → Uncertain", font_size=24)
        summary.next_to(axes, DOWN, buff=0.5)
        self.play(Write(summary))
        self.wait(1)

        # Fade out
        self.play(
            FadeOut(title),
            FadeOut(subtitle),
            FadeOut(formula),
            FadeOut(axes),
            FadeOut(x_labels),
            FadeOut(y_label),
            FadeOut(bars),
            FadeOut(temp_display),
            FadeOut(effect_text),
            FadeOut(summary),
        )
        self.wait(0.5)
