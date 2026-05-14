"""
SGD with and without Weight Decay (L2 Regularization) Visualization
Shows how L2 regularization pulls weights toward zero.
"""

from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Title("SGD: With vs Without Weight Decay (L2)")
        self.play(Write(title), run_time=1)
        self.wait(0.5)

        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            axis_config={"include_tip": False, "numbers_to_exclude": [0]},
            x_length=6,
            y_length=6,
        )
        axes.center()
        
        # Labels
        x_label = axes.get_x_axis_label(r"w_1")
        y_label = axes.get_y_axis_label(r"w_2")
        origin_label = MathTex(r"\vec{0}").next_to(axes.c2p(0, 0), DL, buff=0.2)
        
        self.play(Create(axes), Write(x_label), Write(y_label), Write(origin_label), run_time=1)
        self.wait(0.5)

        # Create loss landscape (elliptical bowl) with contour lines
        def loss_func(x, y):
            return 0.5 * ((x - 1.5) ** 2 + 0.5 * (y + 1) ** 2)

        # Draw contour lines (level sets)
        contours = VGroup()
        for level in [0.5, 1.0, 1.5, 2.0, 2.5]:
            # Parametric ellipse: (x-1.5)^2 + 0.5(y+1)^2 = 2*level
            a = np.sqrt(2 * level)
            b = np.sqrt(4 * level)
            ellipse = ParametricFunction(
                lambda t: axes.c2p(
                    1.5 + a * np.cos(t),
                    -1 + b * np.sin(t)
                ),
                t_range=[0, TAU],
                color=BLUE,
                stroke_opacity=0.3,
                stroke_width=1
            )
            contours.add(ellipse)
        
        self.play(Create(contours), run_time=1)

        # Mark the minimum of the loss (without regularization)
        minimum_point = Dot(axes.c2p(1.5, -1), color=YELLOW, radius=0.1)
        minimum_label = MathTex(r"\min L(\vec{w})", color=YELLOW).next_to(minimum_point, UR, buff=0.2).scale(0.8)
        
        self.play(FadeIn(minimum_point), Write(minimum_label), run_time=0.8)
        self.wait(0.5)

        # Starting point
        start_point = np.array([-2.0, 2.0])
        start_dot = Dot(axes.c2p(*start_point), color=WHITE, radius=0.08)
        start_label = MathTex(r"\vec{w}_0").next_to(start_dot, UL, buff=0.2).scale(0.8)
        
        self.play(FadeIn(start_dot), Write(start_label), run_time=0.6)
        self.wait(0.3)

        # === SGD without Weight Decay ===
        # Simulate SGD steps (gradient descent on the loss)
        lr = 0.3
        w = start_point.copy()
        path_no_wd = [w.copy()]
        
        # Gradient of L: grad = (w1 - 1.5, 0.5*(w2 + 1))
        for _ in range(15):
            grad = np.array([w[0] - 1.5, 0.5 * (w[1] + 1)])
            w = w - lr * grad
            path_no_wd.append(w.copy())

        # Draw trajectory without weight decay
        path_points_no_wd = [axes.c2p(p[0], p[1]) for p in path_no_wd]
        trajectory_no_wd = VMobject(color=GREEN, stroke_width=3)
        trajectory_no_wd.set_points_smoothly(path_points_no_wd)
        
        no_wd_label = Text("SGD (no weight decay)", color=GREEN).scale(0.5)
        no_wd_label.to_corner(UL).shift(DOWN * 0.5)
        
        # Animate path
        moving_dot_no_wd = Dot(path_points_no_wd[0], color=GREEN, radius=0.08)
        
        self.play(Write(no_wd_label), run_time=0.5)
        self.add(moving_dot_no_wd)
        
        for i in range(len(path_points_no_wd) - 1):
            line = Line(path_points_no_wd[i], path_points_no_wd[i + 1], color=GREEN, stroke_width=3)
            self.play(
                Transform(moving_dot_no_wd, Dot(path_points_no_wd[i + 1], color=GREEN, radius=0.08)),
                Create(line),
                run_time=0.15
            )
        
        final_dot_no_wd = Dot(path_points_no_wd[-1], color=GREEN, radius=0.1)
        self.play(Transform(moving_dot_no_wd, final_dot_no_wd), run_time=0.2)
        self.wait(0.5)

        # === SGD with Weight Decay ===
        # Simulate SGD with L2 regularization (weight decay)
        weight_decay = 0.1  # lambda
        lr = 0.3
        w = start_point.copy()
        path_wd = [w.copy()]
        
        # With weight decay: w = w - lr * (grad + lambda * w) = w * (1 - lr*lambda) - lr * grad
        for _ in range(15):
            grad = np.array([w[0] - 1.5, 0.5 * (w[1] + 1)])
            w = w * (1 - lr * weight_decay) - lr * grad
            path_wd.append(w.copy())

        # Draw trajectory with weight decay
        path_points_wd = [axes.c2p(p[0], p[1]) for p in path_wd]
        
        wd_label = Text("SGD + Weight Decay", color=RED).scale(0.5)
        wd_label.next_to(no_wd_label, DOWN, aligned_edge=LEFT)
        
        # Animate path
        moving_dot_wd = Dot(path_points_wd[0], color=RED, radius=0.08)
        
        self.play(Write(wd_label), run_time=0.5)
        self.add(moving_dot_wd)
        
        for i in range(len(path_points_wd) - 1):
            line = Line(path_points_wd[i], path_points_wd[i + 1], color=RED, stroke_width=3)
            self.play(
                Transform(moving_dot_wd, Dot(path_points_wd[i + 1], color=RED, radius=0.08)),
                Create(line),
                run_time=0.15
            )
        
        final_dot_wd = Dot(path_points_wd[-1], color=RED, radius=0.1)
        self.play(Transform(moving_dot_wd, final_dot_wd), run_time=0.2)
        self.wait(0.5)

        # Highlight the difference
        # Draw arrows pointing toward origin from both final points
        arrow_no_wd = Arrow(final_dot_no_wd.get_center(), axes.c2p(0, 0), color=YELLOW, buff=0.2)
        arrow_wd = Arrow(final_dot_wd.get_center(), axes.c2p(0, 0), color=YELLOW, buff=0.15)
        
        zero_label = MathTex(r"\vec{0}", color=YELLOW).next_to(axes.c2p(0, 0), DL, buff=0.2)
        
        # Shield to protect labels
        shield = VGroup()
        
        explanation = Tex(
            r"Weight decay: $\vec{w} \leftarrow \vec{w} - \eta(\nabla L + \lambda \vec{w})$",
            color=WHITE
        ).scale(0.7)
        explanation.to_corner(DR).shift(UP * 0.3)
        
        self.play(
            Create(arrow_no_wd),
            Create(arrow_wd),
            Write(explanation),
            run_time=1
        )
        self.wait(0.5)

        # Final emphasis - the pull toward zero
        pull_text = Tex("L2 pulls weights toward zero!", color=YELLOW).scale(0.8)
        pull_text.to_edge(DOWN)
        
        self.play(Write(pull_text), run_time=1)
        self.wait(1)

        # Fade out
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=1)
