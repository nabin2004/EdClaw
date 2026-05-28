"""Manim animation showing overfitting: training loss dropping while validation loss rises."""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Set up the coordinate system (axes)
        axes = Axes(
            x_range=[0, 12, 2],
            y_range=[0, 1.2, 0.2],
            x_length=10,
            y_length=6,
            axis_config={"color": WHITE},
            tips=False,
        )
        
        # Labels
        x_label = axes.get_x_axis_label(Tex("Epochs"), edge=DOWN, direction=DOWN)
        y_label = axes.get_y_axis_label(Tex("Loss"), edge=LEFT, direction=LEFT)
        
        # Title
        title = Text("Overfitting in Neural Networks", font_size=36)
        title.to_edge(UP)
        
        # Create axes and labels
        self.play(Create(axes), Write(x_label), Write(y_label), Write(title))
        self.wait(0.5)
        
        # Training loss curve - continuously decreasing
        train_epochs = np.linspace(0, 10, 100)
        train_loss = 0.9 * np.exp(-0.3 * train_epochs) + 0.05
        train_points = [axes.coords_to_point(x, y) for x, y in zip(train_epochs, train_loss)]
        
        # Validation loss curve - decreases then increases (overfitting)
        val_epochs = np.linspace(0, 10, 100)
        val_loss = 0.8 * np.exp(-0.15 * val_epochs) + 0.15 + 0.08 * (1 - np.exp(-0.5 * (val_epochs - 3)**2))
        val_points = [axes.coords_to_point(x, y) for x, y in zip(val_epochs, val_loss)]
        
        # Create curve objects
        train_curve = VMobject()
        train_curve.set_points_smoothly(train_points)
        train_curve.set_stroke(BLUE, width=3)
        
        val_curve = VMobject()
        val_curve.set_points_smoothly(val_points)
        val_curve.set_stroke(RED, width=3)
        
        # Legend
        train_legend = VGroup(
            Line(LEFT * 0.3, RIGHT * 0.3, color=BLUE, stroke_width=3),
            Text("Training Loss", font_size=24)
        ).arrange(RIGHT, buff=0.3)
        
        val_legend = VGroup(
            Line(LEFT * 0.3, RIGHT * 0.3, color=RED, stroke_width=3),
            Text("Validation Loss", font_size=24)
        ).arrange(RIGHT, buff=0.3)
        
        legend = VGroup(train_legend, val_legend).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        legend.to_corner(DR, buff=0.5)
        
        # Animate training loss curve
        self.play(
            Create(train_curve, run_time=3, rate_func=linear),
            FadeIn(legend[0], run_time=1)
        )
        self.wait(0.5)
        
        # Animate validation loss curve
        self.play(
            Create(val_curve, run_time=3, rate_func=linear),
            FadeIn(legend[1], run_time=1)
        )
        self.wait(0.5)
        
        # Highlight the divergence point
        divergence_point = axes.coords_to_point(4.5, 0.35)
        dot = Dot(divergence_point, color=YELLOW, radius=0.1)
        divergence_label = Text("Overfitting Begins", font_size=24, color=YELLOW)
        divergence_label.next_to(dot, UP + RIGHT, buff=0.3)
        
        self.play(
            Flash(dot, color=YELLOW, line_length=0.2, flash_radius=0.3),
            FadeIn(dot),
            FadeIn(divergence_label)
        )
        self.wait(0.5)
        
        # Draw arrow showing widening gap
        gap_start = axes.coords_to_point(8, 0.15)
        gap_end = axes.coords_to_point(8, 0.45)
        arrow = Arrow(gap_end, gap_start, color=GREEN, buff=0.1, stroke_width=2)
        gap_label = Text("Generalization Gap", font_size=22, color=GREEN)
        gap_label.next_to(arrow, RIGHT, buff=0.2)
        
        self.play(Create(arrow), FadeIn(gap_label))
        self.wait(0.5)
        
        # Final explanation text
        explanation = Text(
            "Model memorizes training data but fails on new data",
            font_size=26,
            color=LIGHT_GRAY
        )
        explanation.to_edge(DOWN, buff=0.3)
        
        self.play(Write(explanation))
        self.wait(2)
