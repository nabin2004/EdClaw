from manim import *
import numpy as np

class AutoScene(Scene):
    def construct(self):
        # Set up axes
        axes = Axes(
            x_range=[0, 100, 20],
            y_range=[0, 1.2, 0.2],
            x_length=10,
            y_length=5,
            axis_config={"color": WHITE},
            tips=True,
        )
        
        axes_labels = axes.get_axis_labels(
            x_label=Text("Training Steps", font_size=24),
            y_label=Text("Learning Rate", font_size=24)
        )
        
        self.play(Create(axes), Write(axes_labels))
        self.wait(0.5)
        
        # Parameters for cosine annealing with warm restarts
        eta_max = 1.0
        eta_min = 0.0
        T_i = 25  # cycle length
        num_cycles = 4
        
        # Create title
        title = Text("Cosine Annealing Learning Rate Schedule", font_size=32, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Formula display
        formula = MathTex(
            r"\eta_t = \eta_{min} + \frac{1}{2}(\eta_{max} - \eta_{min})",
            r"(1 + \cos(\frac{\pi T_{cur}}{T_i}))",
            font_size=28
        )
        formula.next_to(title, DOWN, buff=0.3)
        self.play(Write(formula))
        self.wait(0.5)
        
        # Generate cosine annealing curve with warm restarts
        x_vals = np.linspace(0, 100, 500)
        y_vals = []
        
        for x in x_vals:
            T_cur = x % T_i
            eta = eta_min + 0.5 * (eta_max - eta_min) * (1 + np.cos(np.pi * T_cur / T_i))
            y_vals.append(eta)
        
        # Create the curve
        curve = VMobject()
        curve.set_points_as_corners([
            axes.c2p(x, y) for x, y in zip(x_vals, y_vals)
        ])
        curve.set_stroke(YELLOW, opacity=1, width=3)
        
        # Animate the curve being drawn
        self.play(Create(curve, run_time=6))
        
        # Add cycle markers
        cycle_labels = VGroup()
        for i in range(num_cycles + 1):
            x_pos = i * T_i
            if x_pos > 100:
                break
            dashed_line = DashedLine(
                axes.c2p(x_pos, 0),
                axes.c2p(x_pos, 1.0),
                color=GRAY_B,
                dash_length=0.1
            )
            label = Text(f"Cycle {i+1}", font_size=16, color=GRAY_C)
            label.next_to(axes.c2p(x_pos, 1.05), UP, buff=0.1)
            self.play(Create(dashed_line, run_time=0.3))
            self.play(Write(label, run_time=0.3))
            cycle_labels.add(label)
        
        self.wait(0.5)
        
        # Highlight oscillation with arrows
        oscillation_arrows = VGroup()
        for i in range(3):
            start_x = 5 + i * 25
            mid_x = start_x + 12.5
            end_x = start_x + 25
            
            arrow_up = CurvedArrow(
                axes.c2p(start_x, 0.0),
                axes.c2p(mid_x, 1.0),
                color=RED,
                angle=-PI/4
            )
            arrow_down = CurvedArrow(
                axes.c2p(mid_x, 1.0),
                axes.c2p(end_x, 0.0),
                color=RED,
                angle=-PI/4
            )
            self.play(Create(arrow_up, run_time=0.5), Create(arrow_down, run_time=0.5))
            oscillation_arrows.add(arrow_up, arrow_down)
        
        self.wait(0.5)
        
        # Show decay annotation
        decay_arrow = Arrow(
            axes.c2p(50, 0.8),
            axes.c2p(50, 0.2),
            color=GREEN,
            buff=0.1
        )
        decay_text = Text("Decay", font_size=20, color=GREEN)
        decay_text.next_to(decay_arrow, RIGHT, buff=0.2)
        
        self.play(Create(decay_arrow), Write(decay_text))
        
        # Add summary points
        summary_group = VGroup(
            Text("• Oscillates between η_min and η_max", font_size=20),
            Text("• Smooth cosine decay within each cycle", font_size=20),
            Text("• Periodic restarts to η_max", font_size=20),
            Text("• Helps escape local minima", font_size=20)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        
        summary_group.to_edge(RIGHT).shift(LEFT * 0.5)
        
        self.play(Write(summary_group, run_time=3))
        
        self.wait(2)
        
        # Fade out everything
        self.play(
            FadeOut(axes),
            FadeOut(axes_labels),
            FadeOut(curve),
            FadeOut(title),
            FadeOut(formula),
            FadeOut(cycle_labels),
            FadeOut(oscillation_arrows),
            FadeOut(decay_arrow),
            FadeOut(decay_text),
            FadeOut(summary_group)
        )
