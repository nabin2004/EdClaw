"""
Momentum in SGD Visualization
Shows a ball rolling down a loss landscape with velocity accumulating
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Momentum in SGD", font_size=48, color=BLUE)
        subtitle = Text("Velocity Accumulation in Loss Landscape", font_size=24, color=GRAY)
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.3)
        
        self.play(Write(title), run_time=1)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.wait(0.5)
        self.play(FadeOut(title_group), run_time=0.5)
        
        # Create axes for the loss landscape
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-2, 8, 1],
            x_length=10,
            y_length=5,
            axis_config={"color": WHITE, "stroke_width": 2},
        )
        
        # Labels
        x_label = Text("Parameters", font_size=20).next_to(axes.x_axis, DOWN)
        y_label = Text("Loss", font_size=20).next_to(axes.y_axis, LEFT).rotate(90 * DEGREES)
        
        self.play(Create(axes), run_time=1)
        self.play(FadeIn(x_label), FadeIn(y_label), run_time=0.5)
        
        # Create the loss function curve (valley/parabola)
        loss_curve = axes.plot(
            lambda x: (x**2) * 0.5,
            color=YELLOW,
            stroke_width=3,
        )
        
        loss_label = Text("Loss Landscape", font_size=20, color=YELLOW)
        loss_label.move_to(axes.c2p(3, 4))
        
        self.play(Create(loss_curve), run_time=1)
        self.play(FadeIn(loss_label), run_time=0.5)
        
        # Create the ball at starting position (high on the left)
        start_x = -4
        ball = Dot(
            point=axes.c2p(start_x, 0.5 * start_x**2),
            radius=0.2,
            color=RED,
        )
        
        ball_glow = ball.copy().set_color(ORANGE).set_opacity(0.3)
        ball_group = VGroup(ball, ball_glow)
        
        self.play(FadeIn(ball_group), run_time=0.5)
        
        # Gradient arrow at starting point
        gradient = -start_x  # derivative of 0.5*x^2 is x
        grad_arrow = Arrow(
            start=ball.get_center(),
            end=ball.get_center() + RIGHT * 0.5 * abs(gradient),
            color=GREEN,
            buff=0,
        )
        grad_label = Text("Gradient", font_size=16, color=GREEN)
        grad_label.next_to(grad_arrow, UP, buff=0.1)
        
        self.play(Create(grad_arrow), FadeIn(grad_label), run_time=0.5)
        self.wait(0.5)
        
        # Remove gradient indication
        self.play(FadeOut(grad_arrow), FadeOut(grad_label), run_time=0.3)
        
        # Animate momentum movement with velocity accumulation
        # Using momentum: v = 0.8*v - 0.3*grad, x = x + v
        positions_x = [start_x]
        velocities = [0]
        momentum = 0.8
        lr = 0.3
        
        for i in range(20):
            x = positions_x[-1]
            grad = x  # derivative of loss
            v = momentum * velocities[-1] - lr * grad
            new_x = x + v
            positions_x.append(new_x)
            velocities.append(v)
        
        # Create velocity arrow that grows
        velocity_arrow = Arrow(
            start=ORIGIN,
            end=RIGHT * 0.1,
            color=BLUE,
            buff=0,
        )
        velocity_arrow.set_opacity(0)
        velocity_label = Text("Velocity", font_size=16, color=BLUE)
        velocity_label.next_to(velocity_arrow, UP, buff=0.1)
        
        self.add(velocity_arrow, velocity_label)
        
        # Animate the ball movement showing momentum
        traj_dots = VGroup()
        prev_pos = ball.get_center()
        
        for i, (x, v) in enumerate(zip(positions_x[1:], velocities[1:])):
            y = 0.5 * x**2
            new_pos = axes.c2p(x, y)
            
            # Update velocity arrow
            velocity_dir = RIGHT * np.sign(v)
            arrow_length = min(abs(v) * 0.8, 1.5)
            
            new_arrow = Arrow(
                start=new_pos,
                end=new_pos + velocity_dir * arrow_length,
                color=BLUE,
                buff=0,
            )
            new_label = Text(f"v={v:.2f}", font_size=14, color=BLUE)
            new_label.next_to(new_arrow, UP, buff=0.05)
            
            # Trail dot
            if i > 1:
                trail = Dot(prev_pos, radius=0.05, color=BLUE, fill_opacity=0.5 - i*0.02)
                traj_dots.add(trail)
            
            # Animate
            self.play(
                ball_group.animate.move_to(new_pos),
                Transform(velocity_arrow, new_arrow),
                Transform(velocity_label, new_label),
                run_time=0.25,
            )
            
            if i % 3 == 0:
                self.add(traj_dots)
            
            prev_pos = new_pos.copy()
        
        self.wait(0.5)
        
        # Fade out velocity indicator
        self.play(FadeOut(velocity_arrow), FadeOut(velocity_label), run_time=0.3)
        
        # Show the valley/minimum reached
        minimum_dot = Dot(axes.c2p(0, 0), radius=0.15, color=GREEN)
        min_label = Text("Minimum", font_size=18, color=GREEN)
        min_label.next_to(minimum_dot, DOWN, buff=0.2)
        
        self.play(
            Flash(minimum_dot, color=GREEN, flash_radius=0.4),
            FadeIn(minimum_dot),
            FadeIn(min_label),
            run_time=0.8
        )
        
        self.wait(0.5)
        
        # Final summary text
        summary = VGroup(
            Text("Momentum accumulates velocity", font_size=24, color=BLUE),
            Text("Ball overshoots but converges", font_size=24, color=YELLOW),
        ).arrange(DOWN, buff=0.4)
        summary.to_edge(UP)
        
        self.play(FadeIn(summary, shift=DOWN), run_time=1)
        self.wait(1)
        
        # Outro
        self.play(
            FadeOut(summary),
            FadeOut(ball_group),
            FadeOut(traj_dots),
            FadeOut(loss_curve),
            FadeOut(loss_label),
            FadeOut(minimum_dot),
            FadeOut(min_label),
            FadeOut(axes),
            FadeOut(x_label),
            FadeOut(y_label),
            run_time=1
        )
        
        self.wait(0.5)
