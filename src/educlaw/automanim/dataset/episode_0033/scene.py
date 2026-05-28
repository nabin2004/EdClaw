from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Layer Normalization", font_size=36)
        title.to_edge(UP, buff=0.5)
        self.play(FadeIn(title))
        self.wait(0.5)

        # Create input matrix representation (batch x features)
        # Visual: 3 rows (samples) x 6 cols (features)
        np.random.seed(42)
        data = np.array([
            [2.0, 1.5, 3.0, 0.5, 2.5, 1.0],
            [1.0, 2.5, 0.5, 3.0, 1.5, 2.0],
            [3.0, 0.5, 2.0, 1.5, 0.5, 3.0]
        ])

        # Create the input matrix visualization
        matrix = VGroup()
        cells = []
        for i, row in enumerate(data):
            row_group = VGroup()
            for j, val in enumerate(row):
                cell = Rectangle(height=0.6, width=0.8, stroke_color=BLUE, fill_opacity=0.1, fill_color=BLUE)
                value = Text(f"{val:.1f}", font_size=16)
                cell_group = VGroup(cell, value)
                row_group.add(cell_group)
                cells.append((i, j, cell_group, val))
            row_group.arrange(RIGHT, buff=0.1)
            matrix.add(row_group)

        matrix.arrange(DOWN, buff=0.1)
        matrix.move_to(LEFT * 3)

        # Labels
        input_label = Text("Input", font_size=20, color=BLUE)
        input_label.next_to(matrix, UP, buff=0.3)

        batch_label = Text("Batch", font_size=14, color=GRAY)
        batch_label.next_to(matrix, LEFT, buff=0.3)
        batch_label.rotate(90 * DEGREES)

        feat_label = Text("Features", font_size=14, color=GRAY)
        feat_label.next_to(matrix, DOWN, buff=0.3)

        self.play(FadeIn(input_label), Create(matrix), FadeIn(batch_label), FadeIn(feat_label))
        self.wait(0.3)

        # Highlight one row to show computation
        highlight_row = SurroundingRectangle(matrix[1], color=YELLOW, stroke_width=3)
        self.play(Create(highlight_row))
        self.wait(0.3)

        # Create mean and variance formulas
        center_x = RIGHT * 2.5

        mean_eq = MathTex(r"\mu = \frac{1}{H} \sum_{i=1}^{H} x_i", font_size=28)
        mean_eq.move_to(center_x + UP * 1.5)

        var_eq = MathTex(r"\sigma^2 = \frac{1}{H} \sum_{i=1}^{H} (x_i - \mu)^2", font_size=24)
        var_eq.move_to(center_x + UP * 0.3)

        norm_eq = MathTex(r"y_i = \frac{x_i - \mu}{\sqrt{\sigma^2 + \epsilon}}", font_size=26)
        norm_eq.move_to(center_x + DOWN * 1.0)

        self.play(Write(mean_eq))
        self.wait(0.3)

        # Highlight cells in the middle row to show feature-wise computation
        row_cells = [c for c in cells if c[0] == 1]
        cell_highlights = VGroup()
        for _, _, cell_group, _ in row_cells:
            hl = SurroundingRectangle(cell_group, color=ORANGE, stroke_width=2)
            cell_highlights.add(hl)

        self.play(FadeIn(cell_highlights))
        self.wait(0.3)

        # Calculate mean for the highlighted row
        row_vals = [c[3] for c in row_cells]
        mean_val = np.mean(row_vals)
        mean_text = Text(f"μ = {mean_val:.2f}", font_size=22, color=GREEN)
        mean_text.next_to(mean_eq, RIGHT, buff=0.8)

        self.play(TransformFromCopy(cell_highlights, mean_text))
        self.wait(0.3)

        # Show variance calculation
        self.play(Write(var_eq))
        var_val = np.var(row_vals)
        var_text = Text(f"σ² = {var_val:.2f}", font_size=22, color=RED)
        var_text.next_to(var_eq, RIGHT, buff=0.5)
        self.wait(0.3)

        self.play(FadeIn(var_text))
        self.wait(0.3)

        # Show normalization
        self.play(Write(norm_eq))
        self.wait(0.3)

        # Create output matrix (normalized values)
        norm_data = (row_vals - mean_val) / np.sqrt(var_val + 1e-8)
        output_cells = []
        output_matrix = VGroup()
        for i, val in enumerate(norm_data):
            cell = Rectangle(height=0.6, width=0.8, stroke_color=GREEN, fill_opacity=0.2, fill_color=GREEN)
            value = Text(f"{val:.2f}", font_size=16, color=GREEN)
            if abs(val) > 1.5:
                value = Text(f"{val:.1f}", font_size=16, color=GREEN)
            cell_group = VGroup(cell, value)
            output_matrix.add(cell_group)
            output_cells.append(cell_group)

        output_matrix.arrange(RIGHT, buff=0.1)
        output_matrix.move_to(center_x + DOWN * 2.5)

        output_label = Text("Normalized", font_size=18, color=GREEN)
        output_label.next_to(output_matrix, UP, buff=0.3)

        # Transform to output - arrows between input and normalized cells
        arrows = VGroup()
        for i, (_, _, _, _) in enumerate(row_cells):
            arrow = Arrow(
                row_cells[i][2].get_right(),
                output_cells[i].get_left(),
                color=YELLOW,
                stroke_width=2,
                tip_length=0.15
            )
            arrows.add(arrow)

        self.play(Create(arrows))
        self.wait(0.2)

        self.play(
            FadeOut(cell_highlights),
            FadeIn(output_matrix),
            FadeIn(output_label)
        )
        self.wait(0.5)

        # Show epsilon small value
        epsilon_text = MathTex(r"\epsilon = 10^{-8}", font_size=20, color=GRAY)
        epsilon_text.next_to(norm_eq, DOWN, buff=0.3)
        self.play(FadeIn(epsilon_text))
        self.wait(0.3)

        # Final summary text
        summary = Text("Feature-wise normalization across each sample", font_size=18, color=WHITE)
        summary.next_to(title, DOWN, buff=0.5)
        self.play(FadeIn(summary))
        self.wait(1.0)

        # Fade out everything
        self.play(FadeOut(title), FadeOut(summary), FadeOut(matrix), FadeOut(highlight_row),
                 FadeOut(mean_eq), FadeOut(var_eq), FadeOut(norm_eq), FadeOut(mean_text),
                 FadeOut(var_text), FadeOut(epsilon_text), FadeOut(output_matrix),
                 FadeOut(output_label), FadeOut(input_label), FadeOut(batch_label),
                 FadeOut(feat_label), FadeOut(arrows))
        self.wait(0.5)
