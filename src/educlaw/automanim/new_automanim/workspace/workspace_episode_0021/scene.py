from manim import *
import numpy as np

class AutoScene(Scene):
    def construct(self):
        # Config
        max_steps = 100
        warmup_steps = 20
        max_lr = 2.5
        
        # Axes
        axes = Axes(
            x_range=[0, max_steps, 20],
            y_range=[0, max_lr, 0.5],
            x_length=10,
            y_length=5,
            axis_config={"include_tip": True, "include_numbers": True},
            tips=True,
        ).to_edge(DOWN, buff=0.5)
        
        # Labels
        x_label = axes.get_x_axis_label(Tex("Training Steps"))
        y_label = axes.get_y_axis_label(Tex("Learning Rate")).rotate(90 * DEGREES)
        
        # Title
        title = Text("Learning Rate Warmup", font_size=36, weight=BOLD).to_edge(UP, buff=0.8)
        
        # Phase labels
        warmup_label = Text("Warmup Phase", font_size=24, color=BLUE).to_corner(UR, buff=1.0)
        decay_label = Text("Cosine Decay", font_size=24, color=RED).to_corner(UR, buff=1.0)
        
        # Step counter
        step_text = Text("Step: 0", font_size=24).next_to(title, DOWN, buff=0.3)
        lr_text = Text("LR: 0.000", font_size=24).next_to(step_text, RIGHT, buff=0.5)
        
        # Show axes
        self.play(Create(axes), Write(x_label), Write(y_label), Write(title))
        self.play(Write(step_text), Write(lr_text), Write(warmup_label))
        
        # LR function
        def lr_schedule(step):
            if step <= warmup_steps:
                return max_lr * (step / warmup_steps)
            else:
                progress = (step - warmup_steps) / (max_steps - warmup_steps)
                return max_lr * 0.5 * (1 + np.cos(np.pi * progress))
        
        # Generate curve points
        warmup_points = [axes.c2p(s, lr_schedule(s)) for s in range(0, warmup_steps + 1)]
        decay_points = [axes.c2p(s, lr_schedule(s)) for s in range(warmup_steps, max_steps + 1)]
        
        # Warmup curve (blue)
        warmup_curve = VMobject(color=BLUE, stroke_width=4)
        warmup_curve.set_points_as_corners(warmup_points)
        
        # Decay curve (red)
        decay_curve = VMobject(color=RED, stroke_width=4)
        decay_curve.set_points_smoothly(decay_points)
        
        # Current position dot
        dot = Dot(color=BLUE, radius=0.15)
        dot.move_to(axes.c2p(0, 0))
        
        self.play(Create(dot))
        
        # Animate warmup phase
        for step in range(1, warmup_steps + 1):
            new_pos = axes.c2p(step, lr_schedule(step))
            lr_val = lr_schedule(step)
            
            new_step_text = Text(f"Step: {step}", font_size=24).next_to(title, DOWN, buff=0.3)
            new_lr_text = Text(f"LR: {lr_val:.3f}", font_size=24).next_to(new_step_text, RIGHT, buff=0.5)
            
            if step == 1:
                self.play(
                    MoveToTarget(dot.move_to(new_pos)),
                    Transform(step_text, new_step_text),
                    Transform(lr_text, new_lr_text),
                    Create(warmup_curve, rate_func=linear, run_time=0.03)
                )
            else:
                self.play(
                    dot.animate.move_to(new_pos),
                    Transform(step_text, new_step_text),
                    Transform(lr_text, new_lr_text),
                    ShowIncreasingSubsets(warmup_curve, run_time=0.03)
                )
            step_text = new_step_text
            lr_text = new_lr_text
        
        # Switch to decay phase
        self.play(
            dot.animate.set_color(RED),
            Transform(warmup_label, decay_label),
            run_time=0.3
        )
        
        # Animate decay phase
        for step in range(warmup_steps + 1, max_steps + 1):
            new_pos = axes.c2p(step, lr_schedule(step))
            lr_val = lr_schedule(step)
            
            new_step_text = Text(f"Step: {step}", font_size=24).next_to(title, DOWN, buff=0.3)
            new_lr_text = Text(f"LR: {lr_val:.3f}", font_size=24).next_to(new_step_text, RIGHT, buff=0.5)
            
            self.play(
                dot.animate.move_to(new_pos),
                Transform(step_text, new_step_text),
                Transform(lr_text, new_lr_text),
                ShowIncreasingSubsets(decay_curve, run_time=0.03)
            )
            step_text = new_step_text
            lr_text = new_lr_text
        
        # Pause at end
        self.wait(1)
