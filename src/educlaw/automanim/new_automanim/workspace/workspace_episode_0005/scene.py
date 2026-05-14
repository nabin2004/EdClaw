"""
Gradient Descent Visualization
A 2D loss surface with contour lines and gradient descent path tracing.
"""

from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Set up the 3D axes for the loss surface
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[0, 18, 3],
            x_length=6,
            y_length=6,
            z_length=4,
            axis_config={"color": WHITE},
        )
        
        # Labels
        x_label = axes.get_x_axis_label("x")
        y_label = axes.get_y_axis_label("y")
        z_label = axes.get_z_axis_label("Loss")
        
        # Define the loss function: f(x, y) = x^2 + y^2 (convex bowl)
        def loss_func(u, v):
            return u**2 + v**2
        
        # Create the surface
        surface = Surface(
            lambda u, v: axes.c2p(u, v, loss_func(u, v)),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(30, 30),
            fill_opacity=0.7,
        )
        surface.set_style(fill_color=BLUE_D, stroke_color=BLUE_E, stroke_width=0.5)
        surface.set_fill_by_checkerboard(BLUE_D, BLUE_E, opacity=0.7)
        
        # Create contour lines on the bottom plane (z=0)
        contours = VGroup()
        for r in [0.5, 1, 1.5, 2, 2.5]:
            circle = Circle(radius=r, color=YELLOW, stroke_width=2)
            circle.move_to(axes.c2p(0, 0, 0))
            contours.add(circle)
        
        # Point labels for contour values
        contour_labels = VGroup()
        for i, r in enumerate([0.5, 1, 1.5, 2, 2.5]):
            label = MathTex(f"z={r**2:.1f}", font_size=16, color=YELLOW)
            label.move_to(axes.c2p(r * 0.7, r * 0.7, 0))
            contour_labels.add(label)
        
        # Gradient descent path - starting from (2.5, 2)
        # Using learning rate 0.1
        learning_rate = 0.15
        points = [(2.5, 2.0)]
        
        for _ in range(20):
            x, y = points[-1]
            # Gradient of x^2 + y^2 is (2x, 2y)
            grad_x = 2 * x
            grad_y = 2 * y
            new_x = x - learning_rate * grad_x
            new_y = y - learning_rate * grad_y
            points.append((new_x, new_y))
        
        # Create the path on the surface
        path_points_3d = [axes.c2p(x, y, loss_func(x, y)) for x, y in points]
        path_on_surface = VMobject()
        path_on_surface.set_points_as_corners(path_points_3d)
        path_on_surface.set_color(RED)
        path_on_surface.set_stroke(width=3)
        
        # Create path on the base plane (projection)
        path_points_base = [axes.c2p(x, y, 0) for x, y in points]
        path_on_base = VMobject()
        path_on_base.set_points_as_corners(path_points_base)
        path_on_base.set_color(RED_B)
        path_on_base.set_stroke(width=2, opacity=0.5)
        
        # The moving dot
        dot = Dot3D(radius=0.15, color=RED)
        dot.move_to(path_points_3d[0])
        
        # Vertical line connecting dot to base
        vert_line = always_redraw(
            lambda: DashedLine(
                dot.get_center(),
                [dot.get_x(), dot.get_y(), axes.c2p(0, 0, 0)[2]],
                color=WHITE,
                stroke_width=1,
            )
        )
        
        # Shadow dot on base
        shadow_dot = Dot(radius=0.1, color=RED, fill_opacity=0.5)
        shadow_dot.move_to(path_points_base[0])
        
        # Title
        title = Text("Gradient Descent on 2D Loss Surface", font_size=36, color=WHITE)
        title.to_edge(UP)
        
        # Step counter
        step_text = Text("Step: 0", font_size=24, color=WHITE)
        step_text.to_corner(DR)
        
        # Position indicator
        pos_text = MathTex(f"(x, y) = ({points[0][0]:.2f}, {points[0][1]:.2f})", font_size=20, color=WHITE)
        loss_text = MathTex(f"Loss = {loss_func(points[0][0], points[0][1]):.2f}", font_size=20, color=WHITE)
        pos_text.to_corner(UL)
        loss_text.next_to(pos_text, DOWN, aligned_edge=LEFT)
        
        # Animation sequence
        self.play(Write(title), run_time=0.5)
        self.wait(0.3)
        
        # Show axes and surface
        self.play(Create(axes), run_time=0.5)
        self.play(Create(surface), run_time=0.8)
        self.play(Write(x_label), Write(y_label), Write(z_label), run_time=0.3)
        
        # Show contours
        self.play(Create(contours), run_time=0.5)
        self.play(Write(contour_labels), run_time=0.3)
        
        # Show initial point and paths
        self.play(
            FadeIn(dot),
            FadeIn(shadow_dot),
            Create(vert_line),
            run_time=0.3
        )
        
        self.play(
            Write(step_text),
            Write(pos_text),
            Write(loss_text),
            run_time=0.3
        )
        
        # Animate gradient descent
        for i in range(1, len(points)):
            new_step_text = Text(f"Step: {i}", font_size=24, color=WHITE)
            new_step_text.move_to(step_text.get_center())
            
            new_pos_text = MathTex(f"(x, y) = ({points[i][0]:.2f}, {points[i][1]:.2f})", font_size=20, color=WHITE)
            new_pos_text.move_to(pos_text.get_center())
            
            new_loss_text = MathTex(f"Loss = {loss_func(points[i][0], points[i][1]):.2f}", font_size=20, color=WHITE)
            new_loss_text.next_to(new_pos_text, DOWN, aligned_edge=LEFT)
            
            # Draw path segment on surface
            if i == 1:
                path_segment = Line(path_points_3d[i-1], path_points_3d[i], color=RED, stroke_width=3)
            else:
                path_segment = Line(path_points_3d[i-1], path_points_3d[i], color=RED, stroke_width=3)
            
            path_segment_base = Line(path_points_base[i-1], path_points_base[i], color=RED_B, stroke_width=2, stroke_opacity=0.5)
            
            self.play(
                dot.animate.move_to(path_points_3d[i]),
                shadow_dot.animate.move_to(path_points_base[i]),
                Create(path_segment),
                Create(path_segment_base),
                Transform(step_text, new_step_text),
                Transform(pos_text, new_pos_text),
                Transform(loss_text, new_loss_text),
                run_time=0.4,
                rate_func=smooth,
            )
        
        # Final glow effect at minimum
        final_glow = Annulus(inner_radius=0.1, outer_radius=0.4, color=GREEN, fill_opacity=0.3)
        final_glow.move_to(path_points_3d[-1])
        
        self.play(
            FadeIn(final_glow),
            dot.animate.set_color(GREEN),
            run_time=0.5
        )
        
        # Final message
        final_text = Text("Converged to Minimum!", font_size=30, color=GREEN)
        final_text.next_to(title, DOWN)
        
        self.play(Write(final_text), run_time=0.5)
        self.wait(1)
        
        # Fade out
        self.play(
            FadeOut(title),
            FadeOut(final_text),
            FadeOut(axes),
            FadeOut(surface),
            FadeOut(contours),
            FadeOut(contour_labels),
            FadeOut(dot),
            FadeOut(shadow_dot),
            FadeOut(vert_line),
            FadeOut(step_text),
            FadeOut(pos_text),
            FadeOut(loss_text),
            FadeOut(final_glow),
            FadeOut(x_label),
            FadeOut(y_label),
            FadeOut(z_label),
            run_time=0.5
        )
