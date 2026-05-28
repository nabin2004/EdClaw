"""
Manim animation comparing SGD, Adam, and RMSProp optimizers.
Shows three colored paths traversing the same loss surface.
"""
from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        self.camera.background_color = "#1a1a1a"
        
        # Title
        title = Text("Optimizer Comparison: SGD vs Adam vs RMSProp", 
                     font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1)
        self.wait(0.2)
        
        # Create coordinate system for loss surface visualization
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-3, 3, 1],
            x_length=10,
            y_length=6,
            axis_config={
                "color": GRAY_C,
                "stroke_width": 1.5,
                "include_tip": False,
            },
        )
        axes.to_edge(DOWN, buff=0.8)
        
        # Labels
        x_label = Text("Parameter w₁", font_size=20, color=GRAY_B).next_to(axes.x_axis, DOWN, buff=0.2)
        y_label = Text("Parameter w₂", font_size=20, color=GRAY_B).next_to(axes.y_axis, LEFT, buff=0.2)
        
        self.play(Create(axes), Write(x_label), Write(y_label), run_time=1)
        self.wait(0.2)
        
        # Create loss surface visualization using contour-like ellipses
        # Using elliptical contours to show the optimization paths clearly
        contours = VGroup()
        colors = [BLUE_E, BLUE_D, BLUE_C, TEAL_C, GREEN_C, YELLOW_C, ORANGE, RED_C]
        
        for i, scale in enumerate([0.5, 0.8, 1.2, 1.8, 2.5, 3.5, 4.5, 6]):
            ellipse = Ellipse(
                width=scale * 1.5,
                height=scale * 0.8,
                color=colors[i],
                stroke_width=1.5,
                fill_opacity=0,
            )
            ellipse.move_to(axes.c2p(0, 0))
            contours.add(ellipse)
        
        # Add gradient direction arrows
        arrows = VGroup()
        for angle in np.linspace(0, 2*PI, 8, endpoint=False):
            start_point = axes.c2p(2.5 * np.cos(angle), 1.3 * np.sin(angle))
            end_point = axes.c2p(1.5 * np.cos(angle), 0.8 * np.sin(angle))
            arrow = Arrow(start_point, end_point, buff=0, color=GRAY_D, stroke_width=1)
            arrows.add(arrow)
        
        self.play(FadeIn(contours), FadeIn(arrows), run_time=1)
        self.wait(0.3)
        
        # Minimum point
        min_point = Dot(axes.c2p(0, 0), color=YELLOW, radius=0.1)
        min_label = Text("Minimum", font_size=18, color=YELLOW).next_to(min_point, UR, buff=0.15)
        self.play(FadeIn(min_point), Write(min_label), run_time=0.5)
        self.wait(0.2)
        
        # Starting point
        start_pos = axes.c2p(2.8, 2.2)
        start_dot = Dot(start_pos, color=WHITE, radius=0.08)
        start_label = Text("Start", font_size=18, color=WHITE).next_to(start_dot, UR, buff=0.1)
        self.play(FadeIn(start_dot), Write(start_label), run_time=0.5)
        self.wait(0.2)
        
        # Legend
        legend = VGroup()
        sgd_legend = VGroup(
            Line(ORIGIN, RIGHT*0.4, color=RED, stroke_width=3),
            Text("SGD", font_size=20, color=RED)
        ).arrange(RIGHT, buff=0.2)
        adam_legend = VGroup(
            Line(ORIGIN, RIGHT*0.4, color=BLUE, stroke_width=3),
            Text("Adam", font_size=20, color=BLUE)
        ).arrange(RIGHT, buff=0.2)
        rmsprop_legend = VGroup(
            Line(ORIGIN, RIGHT*0.4, color=GREEN, stroke_width=3),
            Text("RMSProp", font_size=20, color=GREEN)
        ).arrange(RIGHT, buff=0.2)
        
        legend.add(sgd_legend, adam_legend, rmsprop_legend)
        legend.arrange(RIGHT, buff=0.8)
        legend.to_edge(RIGHT, buff=0.5)
        legend.shift(UP * 2.2)
        
        self.play(Write(legend), run_time=1)
        self.wait(0.2)
        
        # Define optimization paths (simulated)
        # SGD: Oscillatory, slower convergence (RED)
        sgd_points = [
            [2.8, 2.2],
            [2.2, 1.6],
            [1.8, 0.8],
            [1.4, 0.3],
            [1.1, -0.1],
            [0.8, 0.1],
            [0.5, -0.05],
            [0.3, 0.02],
            [0.15, 0],
            [0.05, 0],
        ]
        
        # Adam: Smooth, fast convergence with adaptive learning (BLUE)
        adam_points = [
            [2.8, 2.2],
            [1.6, 1.0],
            [0.7, 0.3],
            [0.25, 0.08],
            [0.05, 0.01],
        ]
        
        # RMSProp: Reduces oscillations, adapts per-parameter (GREEN)
        rmsprop_points = [
            [2.8, 2.2],
            [1.9, 1.3],
            [1.0, 0.5],
            [0.4, 0.15],
            [0.12, 0.03],
            [0.02, 0],
        ]
        
        # Convert to scene coordinates
        sgd_path_points = [axes.c2p(p[0], p[1]) for p in sgd_points]
        adam_path_points = [axes.c2p(p[0], p[1]) for p in adam_points]
        rmsprop_path_points = [axes.c2p(p[0], p[1]) for p in rmsprop_points]
        
        # Create path objects
        sgd_path = VMobject(color=RED, stroke_width=4)
        sgd_path.set_points_as_corners([sgd_path_points[0], sgd_path_points[0]])
        
        adam_path = VMobject(color=BLUE, stroke_width=4)
        adam_path.set_points_as_corners([adam_path_points[0], adam_path_points[0]])
        
        rmsprop_path = VMobject(color=GREEN, stroke_width=4)
        rmsprop_path.set_points_as_corners([rmsprop_path_points[0], rmsprop_path_points[0]])
        
        # Moving dots
        sgd_dot = Dot(sgd_path_points[0], color=RED, radius=0.1)
        adam_dot = Dot(adam_path_points[0], color=BLUE, radius=0.1)
        rmsprop_dot = Dot(rmsprop_path_points[0], color=GREEN, radius=0.1)
        
        # Animate all three paths simultaneously with different speeds
        self.play(
            FadeIn(sgd_path),
            FadeIn(adam_path),
            FadeIn(rmsprop_path),
            FadeIn(sgd_dot),
            FadeIn(adam_dot),
            FadeIn(rmsprop_dot),
            run_time=0.5
        )
        
        # Animate SGD path (step by step with oscillation)
        sgd_animations = []
        for i in range(1, len(sgd_path_points)):
            new_path = VMobject(color=RED, stroke_width=4)
            new_path.set_points_as_corners(sgd_path_points[:i+1])
            sgd_animations.append(Transform(sgd_path, new_path))
            sgd_animations.append(sgd_dot.animate.move_to(sgd_path_points[i]))
        
        # Animate Adam path (smooth, fast)
        adam_full_path = VMobject(color=BLUE, stroke_width=4)
        adam_full_path.set_points_as_corners(adam_path_points)
        
        # Animate RMSProp path (moderate)
        rmsprop_full_path = VMobject(color=GREEN, stroke_width=4)
        rmsprop_full_path.set_points_as_corners(rmsprop_path_points)
        
        # Play animations with appropriate timing
        # Adam converges fastest
        self.play(
            Transform(adam_path, adam_full_path),
            adam_dot.animate.move_to(adam_path_points[-1]),
            AnimationGroup(*sgd_animations[:4], lag_ratio=0.8),
            run_time=2.5
        )
        
        # Continue SGD and RMSProp
        sgd_remaining = []
        for i in range(4, len(sgd_path_points)):
            new_path = VMobject(color=RED, stroke_width=4)
            new_path.set_points_as_corners(sgd_path_points[:i+1])
            sgd_remaining.append(Transform(sgd_path, new_path))
            sgd_remaining.append(sgd_dot.animate.move_to(sgd_path_points[i]))
        
        self.play(
            AnimationGroup(*sgd_remaining[:6], lag_ratio=0.5),
            Transform(rmsprop_path, rmsprop_full_path),
            rmsprop_dot.animate.move_to(rmsprop_path_points[-1]),
            run_time=2.5
        )
        
        # Finish SGD
        if len(sgd_remaining) > 6:
            self.play(
                AnimationGroup(*sgd_remaining[6:], lag_ratio=0.3),
                run_time=1.5
            )
        
        self.wait(0.5)
        
        # Add convergence labels
        adam_converged = Text("Converged!", font_size=16, color=BLUE).next_to(adam_dot, DR, buff=0.1)
        rmsprop_converged = Text("Converged!", font_size=16, color=GREEN).next_to(rmsprop_dot, DR, buff=0.1)
        sgd_converged = Text("Converged!", font_size=16, color=RED).next_to(sgd_dot, UR, buff=0.1)
        
        self.play(
            FadeIn(adam_converged),
            FadeIn(rmsprop_converged),
            FadeIn(sgd_converged),
            run_time=0.5
        )
        
        self.wait(0.5)
        
        # Key observations text
        observations = VGroup(
            Text("Key Observations:", font_size=22, color=YELLOW),
            Text("• SGD: Slower, oscillates more", font_size=18, color=RED),
            Text("• Adam: Fastest, smooth convergence", font_size=18, color=BLUE),
            Text("• RMSProp: Balanced, adaptive steps", font_size=18, color=GREEN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        observations.to_edge(LEFT, buff=0.5)
        observations.shift(UP * 1.5)
        
        self.play(Write(observations), run_time=2)
        self.wait(2)
        
        # Final fade
        self.play(
            FadeOut(title),
            FadeOut(axes),
            FadeOut(x_label),
            FadeOut(y_label),
            FadeOut(contours),
            FadeOut(arrows),
            FadeOut(min_point),
            FadeOut(min_label),
            FadeOut(start_dot),
            FadeOut(start_label),
            FadeOut(legend),
            FadeOut(sgd_path),
            FadeOut(adam_path),
            FadeOut(rmsprop_path),
            FadeOut(sgd_dot),
            FadeOut(adam_dot),
            FadeOut(rmsprop_dot),
            FadeOut(adam_converged),
            FadeOut(rmsprop_converged),
            FadeOut(sgd_converged),
            FadeOut(observations),
            run_time=1
        )
        
        self.wait(0.5)
