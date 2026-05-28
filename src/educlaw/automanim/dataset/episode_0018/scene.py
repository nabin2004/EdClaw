"""Gradient Clipping Animation - Comparing unclipped vs clipped gradients"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Set up the scene
        self.camera.background_color = "#1a1a1a"
        
        # Title
        title = Text("Gradient Clipping in Action", font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title))
        
        # Create side-by-side comparison labels
        unclipped_label = Text("Unclipped", font_size=28, color=RED)
        clipped_label = Text("Clipped", font_size=28, color=GREEN)
        
        unclipped_label.to_edge(LEFT, buff=1.5).shift(UP * 2)
        clipped_label.to_edge(RIGHT, buff=1.5).shift(UP * 2)
        
        # Create loss landscapes (simplified parabolas)
        axes_left = Axes(
            x_range=[-5, 5, 1],
            y_range=[0, 8, 1],
            x_length=4,
            y_length=3,
            axis_config={"color": GRAY, "include_tip": False},
        ).shift(LEFT * 3 + DOWN * 0.5)
        
        axes_right = Axes(
            x_range=[-5, 5, 1],
            y_range=[0, 8, 1],
            x_length=4,
            y_length=3,
            axis_config={"color": GRAY, "include_tip": False},
        ).shift(RIGHT * 3 + DOWN * 0.5)
        
        # Loss curves
        loss_curve = axes_left.plot(lambda x: 0.3 * x**2, color=BLUE, stroke_width=2)
        loss_curve_right = axes_right.plot(lambda x: 0.3 * x**2, color=BLUE, stroke_width=2)
        
        # Starting position (high loss region)
        start_x = -4
        start_point_left = axes_left.c2p(start_x, 0.3 * start_x**2)
        start_point_right = axes_right.c2p(start_x, 0.3 * start_x**2)
        
        # Create dots for current position
        dot_left = Dot(start_point_left, color=YELLOW, radius=0.12)
        dot_right = Dot(start_point_right, color=YELLOW, radius=0.12)
        
        # Animate setup
        self.play(
            Write(unclipped_label),
            Write(clipped_label),
            Create(axes_left),
            Create(axes_right),
            Create(loss_curve),
            Create(loss_curve_right),
            Create(dot_left),
            Create(dot_right),
            run_time=2
        )
        
        # Show gradient computation
        gradient_text = Text("Compute Gradient", font_size=20, color=TEAL)
        gradient_text.next_to(title, DOWN, buff=0.3)
        self.play(Write(gradient_text))
        
        # Calculate gradients (derivative of 0.3*x^2 is 0.6*x)
        # At x=-4, gradient = -2.4 (very large!)
        gradient_value = 0.6 * start_x  # = -2.4
        
        # Draw gradient arrows (scaled for visibility)
        arrow_scale = 0.8
        grad_arrow_left = Arrow(
            start_point_left,
            [start_point_left[0] - gradient_value * arrow_scale * 4, start_point_left[1], 0],
            color=RED,
            buff=0,
            max_tip_length_to_length_ratio=0.15
        )
        
        grad_arrow_right = Arrow(
            start_point_right,
            [start_point_right[0] - gradient_value * arrow_scale * 4, start_point_right[1], 0],
            color=ORANGE,
            buff=0,
            max_tip_length_to_length_ratio=0.15
        )
        
        # Gradient value display
        grad_val_text = MathTex(f"\\nabla L = {gradient_value:.1f}", font_size=24, color=YELLOW)
        grad_val_text.to_edge(DOWN, buff=0.5)
        
        self.play(
            Create(grad_arrow_left),
            Create(grad_arrow_right),
            Write(grad_val_text),
            run_time=1.5
        )
        
        self.wait(0.5)
        
        # Show clipping threshold
        self.play(FadeOut(gradient_text))
        clip_text = Text("Apply Clipping (threshold = 1.0)", font_size=20, color=GREEN)
        clip_text.next_to(title, DOWN, buff=0.3)
        self.play(Write(clip_text))
        
        # Threshold line on left (no clipping - still large)
        threshold = 1.0
        clipped_gradient = max(min(gradient_value, threshold), -threshold)
        
        # Update right arrow to show clipped version
        clipped_arrow = Arrow(
            start_point_right,
            [start_point_right[0] - clipped_gradient * arrow_scale * 4, start_point_right[1], 0],
            color=GREEN,
            buff=0,
            max_tip_length_to_length_ratio=0.15
        )
        
        # Clipped value text
        clipped_val_text = MathTex(f"\\text{{clipped}} = {clipped_gradient:.1f}", font_size=24, color=GREEN)
        clipped_val_text.next_to(grad_val_text, RIGHT, buff=1)
        
        self.play(
            Transform(grad_arrow_right, clipped_arrow),
            Write(clipped_val_text),
            run_time=1.5
        )
        
        self.wait(0.5)
        
        # Now show the step update
        self.play(FadeOut(clip_text))
        update_text = Text("Update Step", font_size=20, color=WHITE)
        update_text.next_to(title, DOWN, buff=0.3)
        self.play(Write(update_text))
        
        # Calculate new positions
        lr = 0.5  # learning rate
        
        # Unclipped: large jump (explodes across the landscape)
        unclipped_step = lr * gradient_value  # = -1.2
        new_x_unclipped = start_x - unclipped_step  # lands at -2.8, but we'll show it overshooting
        # Actually let's make it more dramatic - explode to the other side
        new_x_unclipped = 3.5  # Exploded across
        
        # Clipped: controlled step
        clipped_step = lr * clipped_gradient
        new_x_clipped = start_x - clipped_step  # = -4 - (-0.5) = -3.5
        
        new_point_left = axes_left.c2p(new_x_unclipped, 0.3 * new_x_unclipped**2)
        new_point_right = axes_right.c2p(new_x_clipped, 0.3 * new_x_clipped**2)
        
        # Animate the updates
        path_left = TracedPath(dot_left.get_center, stroke_color=RED, stroke_width=2)
        path_right = TracedPath(dot_right.get_center, stroke_color=GREEN, stroke_width=2)
        
        self.add(path_left, path_right)
        
        # Unclipped explodes (fast, erratic movement)
        self.play(
            dot_left.animate.move_to(new_point_left),
            run_time=0.8,
            rate_func=rate_functions.ease_in_expo
        )
        
        # Clipped moves smoothly
        self.play(
            dot_right.animate.move_to(new_point_right),
            run_time=1.2,
            rate_func=rate_functions.smooth
        )
        
        self.wait(0.3)
        
        # Show the explosion effect on unclipped
        explosion = Text("EXPLOSION!", font_size=32, color=RED)
        explosion.move_to(axes_left.get_center() + UP * 0.5)
        
        stable = Text("Stable", font_size=32, color=GREEN)
        stable.move_to(axes_right.get_center() + UP * 0.5)
        
        self.play(
            FadeOut(grad_arrow_left),
            FadeOut(grad_arrow_right),
            FadeOut(grad_val_text),
            FadeOut(clipped_val_text),
            FadeOut(update_text),
            run_time=0.5
        )
        
        self.play(
            Write(explosion),
            Write(stable),
            run_time=0.8
        )
        
        self.wait(0.5)
        
        # Final comparison summary
        summary = Text(
            "Without clipping: gradients explode → unstable training\n"
            "With clipping: gradients bounded → stable convergence",
            font_size=18,
            color=WHITE,
            line_spacing=1.5
        )
        summary.to_edge(DOWN, buff=0.3)
        
        self.play(Write(summary), run_time=1.5)
        
        self.wait(2)
        
        # Fade out everything
        self.play(
            FadeOut(title),
            FadeOut(unclipped_label),
            FadeOut(clipped_label),
            FadeOut(axes_left),
            FadeOut(axes_right),
            FadeOut(loss_curve),
            FadeOut(loss_curve_right),
            FadeOut(dot_left),
            FadeOut(dot_right),
            FadeOut(path_left),
            FadeOut(path_right),
            FadeOut(explosion),
            FadeOut(stable),
            FadeOut(summary),
            run_time=1
        )
