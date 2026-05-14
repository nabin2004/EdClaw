from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Set up the coordinate system for loss surface
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-1, 15, 2],
            x_length=10,
            y_length=6,
            axis_config={"include_tip": True},
        )
        
        axes_labels = axes.get_axis_labels(x_label="w (weight)", y_label="L (loss)")
        
        # A simple quadratic loss surface: L = w^2
        loss_curve = axes.plot(lambda x: x**2, x_range=[-3.5, 3.5], color=BLUE)
        loss_label = MathTex("L = w^2").next_to(loss_curve, UP, buff=0.3)
        
        self.play(Create(axes), Write(axes_labels))
        self.play(Create(loss_curve), Write(loss_label))
        self.wait(0.5)
        
        # Initial weight position
        w_init = 3.0
        dot = Dot(axes.c2p(w_init, w_init**2), color=YELLOW, radius=0.1)
        dot_label = MathTex("w_0").next_to(dot, RIGHT)
        self.play(FadeIn(dot), Write(dot_label))
        self.wait(0.5)
        
        # Show gradient computation
        gradient_text = MathTex(r"\nabla L = 2w = " + f"{2*w_init:.1f}").to_edge(UP)
        self.play(Write(gradient_text))
        self.wait(0.5)
        
        # Show gradient arrow
        gradient_arrow = Arrow(
            axes.c2p(w_init, w_init**2),
            axes.c2p(w_init - 0.8, w_init**2),
            buff=0,
            color=GREEN,
            stroke_width=4
        )
        gradient_label = MathTex(r"-\nabla L").next_to(gradient_arrow, DOWN, buff=0.1)
        self.play(GrowArrow(gradient_arrow), Write(gradient_label))
        self.wait(0.5)
        
        # First update: normal learning rate
        lr_normal = 0.1
        w_new = w_init - lr_normal * 2 * w_init
        new_dot = Dot(axes.c2p(w_new, w_new**2), color=YELLOW, radius=0.1)
        update_arrow = Arrow(dot.get_center(), new_dot.get_center(), buff=0.05, color=ORANGE)
        
        self.play(
            Transform(dot.copy(), new_dot),
            Create(update_arrow)
        )
        self.wait(0.5)
        
        # Show multiple converging steps (normal learning rate)
        current_w = w_new
        dots_normal = [new_dot]
        arrows_normal = [update_arrow]
        
        for i in range(3):
            next_w = current_w - lr_normal * 2 * current_w
            next_dot = Dot(axes.c2p(next_w, next_w**2), color=YELLOW, radius=0.08)
            arrow = Arrow(
                axes.c2p(current_w, current_w**2),
                axes.c2p(next_w, next_w**2),
                buff=0.05,
                color=ORANGE,
                stroke_width=2
            )
            dots_normal.append(next_dot)
            arrows_normal.append(arrow)
            self.play(FadeIn(next_dot, scale=0.5), Create(arrow), run_time=0.4)
            current_w = next_w
        
        self.wait(0.5)
        
        # Clear and reset for exploding gradient demo
        self.play(
            *[FadeOut(m) for m in [gradient_text, gradient_arrow, gradient_label, 
                                   *dots_normal, *arrows_normal]]
        )
        self.wait(0.3)
        
        # Title for exploding gradient
        explode_title = Text("Exploding Gradient Problem", color=RED, font_size=36)
        explode_title.to_edge(UP)
        self.play(Write(explode_title))
        self.wait(0.3)
        
        # Reset to initial position
        dot_reset = Dot(axes.c2p(w_init, w_init**2), color=RED, radius=0.1)
        explode_label = MathTex("w_0").next_to(dot_reset, RIGHT)
        self.play(FadeIn(dot_reset), Write(explode_label))
        
        # Show large learning rate
        lr_explode = 1.5  # Way too large
        explosion_text = MathTex(r"\eta = " + f"{lr_explode}" + r" \gg " + r"\eta_{critical}").to_edge(UP)
        explosion_text.shift(DOWN * 0.8)
        self.play(Write(explosion_text))
        self.wait(0.5)
        
        # First explosive update
        w_explode = w_init
        path_dots_explode = [dot_reset]
        
        # Calculate new position: w_new = w - lr * 2w = w * (1 - 2*lr)
        factor = 1 - 2 * lr_explode
        w_first = w_explode * factor
        
        # Shows it shoots to the other side
        dot_explode1 = Dot(axes.c2p(w_first, w_first**2), color=RED, radius=0.1)
        arrow_explode = Arrow(
            axes.c2p(w_explode, w_explode**2),
            axes.c2p(w_first, w_first**2),
            buff=0.05,
            color=RED,
            stroke_width=6
        )
        overshoot_text = Text("OVERSHOOT!", color=RED, font_size=28)
        overshoot_text.next_to(arrow_explode, DOWN, buff=0.3)
        
        self.play(
            GrowArrow(arrow_explode),
            FadeIn(dot_explode1, scale=0.5),
            Write(overshoot_text)
        )
        self.wait(0.5)
        
        # Continue showing divergence
        w_explode = w_first
        for i in range(3):
            next_w = w_explode * factor
            next_dot = Dot(axes.c2p(next_w, next_w**2), color=RED, radius=0.08)
            arrow = Arrow(
                axes.c2p(w_explode, w_explode**2),
                axes.c2p(next_w, next_w**2),
                buff=0.05,
                color=RED,
                stroke_width=3
            )
            self.play(FadeIn(next_dot, scale=0.5), Create(arrow), run_time=0.5)
            w_explode = next_w
        
        # Show final divergence off-screen
        divergence_text = Text("DIVERGES!", color=RED, font_size=40)
        divergence_text.move_to(axes.c2p(-5, 12))
        self.play(Write(divergence_text), run_time=0.8)
        
        # Final explosion effect
        final_dots = VGroup(*[
            Dot(axes.c2p(-5 - i*0.5, 12 + i*2), color=RED, radius=0.05)
            for i in range(5)
        ])
        self.play(FadeIn(final_dots, scale=2), run_time=0.5)
        
        # Summary text
        summary = Text("Large learning rate causes weights to explode", 
                      font_size=24, color=WHITE)
        summary.to_edge(DOWN)
        self.wait(0.5)
        self.play(Write(summary))
        
        self.wait(1)
