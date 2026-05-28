"""
AutoScene: Softmax Animation
Animates the softmax transformation from raw logits to probability distribution.
"""
from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Set up colors
        self.camera.background_color = "#1a1a2e"
        
        # Initial logits
        logits = np.array([2.0, 1.0, 0.1])
        labels = ["Class A", "Class B", "Class C"]
        colors = ["#ff6b6b", "#4ecdc4", "#ffe66d"]
        
        # Calculate softmax values
        exp_values = np.exp(logits)
        sum_exp = np.sum(exp_values)
        softmax_probs = exp_values / sum_exp
        
        # Title
        title = Text("Softmax Transformation", font_size=36, color="white")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        
        # Create initial bars for logits (scaled for visibility)
        max_logit = max(logits)
        logit_bars = VGroup()
        logit_values = VGroup()
        
        for i, (logit, label, color) in enumerate(zip(logits, labels, colors)):
            # Bar height proportional to value (clamped for visibility)
            bar_height = max(logit * 0.8, 0.3)
            bar = Rectangle(
                width=0.8,
                height=bar_height,
                fill_color=color,
                fill_opacity=0.8,
                stroke_color="white",
                stroke_width=2
            )
            bar.shift(i * 1.5 * RIGHT)
            
            # Value label
            val_text = MathTex(f"{logit:.1f}", font_size=24, color="white")
            val_text.next_to(bar, UP, buff=0.2)
            
            # Class label
            label_text = Text(label, font_size=16, color="white")
            label_text.next_to(bar, DOWN, buff=0.2)
            label_text.rotate(PI/2)
            
            logit_bars.add(bar)
            logit_values.add(val_text, label_text)
        
        logit_group = VGroup(logit_bars, logit_values)
        logit_group.center().shift(UP * 0.5)
        
        # Step 1 label
        step1_label = Text("1. Input Logits", font_size=24, color="#a0a0a0")
        step1_label.next_to(logit_group, DOWN, buff=1.0)
        
        self.play(
            Create(logit_bars),
            Write(logit_values),
            Write(step1_label),
            run_time=1.5
        )
        self.wait(0.5)
        
        # Step 2: Apply exp() function
        exp_bars = VGroup()
        exp_values_group = VGroup()
        
        for i, (exp_val, exp_height, color) in enumerate(
            zip(exp_values, exp_values / max(exp_values) * 2.0, colors)
        ):
            bar = Rectangle(
                width=0.8,
                height=max(exp_height, 0.3),
                fill_color=color,
                fill_opacity=0.9,
                stroke_color="white",
                stroke_width=2
            )
            bar.shift(i * 1.5 * RIGHT)
            
            val_text = MathTex(f"e^{{{logits[i]:.1f}}}", font_size=22, color="white")
            val_text.next_to(bar, UP, buff=0.2)
            
            # Actual value
            val_actual = MathTex(f"={exp_val:.2f}", font_size=18, color="#dddddd")
            val_actual.next_to(val_text, RIGHT, buff=0.1)
            
            exp_bars.add(bar)
            exp_values_group.add(val_text, val_actual)
        
        exp_group = VGroup(exp_bars, exp_values_group)
        exp_group.center().shift(UP * 0.5)
        
        step2_label = Text("2. Apply Exponential (e^x)", font_size=24, color="#a0a0a0")
        step2_label.next_to(exp_group, DOWN, buff=1.0)
        
        # Transform to exp values
        self.play(
            ReplacementTransform(logit_bars, exp_bars),
            ReplacementTransform(logit_values, exp_values_group),
            ReplacementTransform(step1_label, step2_label),
            run_time=1.5
        )
        self.wait(0.3)
        
        # Show summation
        sum_formula = MathTex(r"\text{Sum} = e^{2.0} + e^{1.0} + e^{0.1}", font_size=28, color="white")
        sum_formula = MathTex(f"\\text{{Sum}} = {sum_exp:.2f}", font_size=28, color="white")
        sum_formula.next_to(exp_group, LEFT, buff=1.0)
        
        self.play(Write(sum_formula), run_time=1.0)
        self.wait(0.3)
        
        # Step 3: Normalize to get probabilities
        prob_bars = VGroup()
        prob_values_group = VGroup()
        
        for i, (prob, color) in enumerate(zip(softmax_probs, colors)):
            bar = Rectangle(
                width=0.8,
                height=prob * 5,  # Scale for visibility
                fill_color=color,
                fill_opacity=1.0,
                stroke_color="white",
                stroke_width=2
            )
            bar.shift(i * 1.5 * RIGHT)
            
            # Percentage label
            pct = prob * 100
            val_text = MathTex(f"{pct:.1f}\\%", font_size=24, color="white")
            val_text.next_to(bar, UP, buff=0.2)
            
            prob_bars.add(bar)
            prob_values_group.add(val_text)
        
        prob_group = VGroup(prob_bars, prob_values_group)
        prob_group.center().shift(UP * 0.5)
        
        step3_label = Text("3. Normalize (Divide by Sum)", font_size=24, color="#a0a0a0")
        step3_label.next_to(prob_group, DOWN, buff=1.0)
        
        # Transform to probabilities
        self.play(
            FadeOut(sum_formula),
            ReplacementTransform(exp_bars, prob_bars),
            ReplacementTransform(exp_values_group, prob_values_group),
            ReplacementTransform(step2_label, step3_label),
            run_time=1.5
        )
        self.wait(0.3)
        
        # Highlight that probabilities sum to 1
        sum_equals_1 = MathTex(r"\sum p_i = 1.0", font_size=32, color="#4ecdc4")
        sum_equals_1.next_to(prob_group, LEFT, buff=1.0)
        
        self.play(
            Write(sum_equals_1),
            run_time=1.0
        )
        
        # Pulse effect on the bars
        for _ in range(2):
            self.play(
                prob_bars.animate.scale(1.05),
                rate_func=there_and_back,
                run_time=0.5
            )
        
        self.wait(0.5)
        
        # Final formula at bottom
        formula = MathTex(
            r"\text{softmax}(x_i) = \frac{e^{x_i}}{\sum_{j} e^{x_j}}",
            font_size=32,
            color="white"
        )
        formula.to_edge(DOWN, buff=0.5)
        
        self.play(Write(formula), run_time=1.5)
        self.wait(1.0)
        
        # Fade out everything
        self.play(
            FadeOut(prob_group),
            FadeOut(step3_label),
            FadeOut(sum_equals_1),
            FadeOut(formula),
            FadeOut(title),
            run_time=1.0
        )
