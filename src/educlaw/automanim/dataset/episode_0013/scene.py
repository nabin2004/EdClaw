"""
Max Pooling Visualization Animation
Visualizes 4x4 feature map reducing to 2x2 with max values highlighted.
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Initialize 4x4 feature map with example values
        feature_map = [
            [1, 3, 2, 8],
            [4, 6, 5, 1],
            [7, 2, 9, 3],
            [3, 8, 4, 6]
        ]
        
        # Create title
        title = Text("Max Pooling Operation", font_size=36, color=BLUE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)
        
        # Create input feature map visualization
        input_grid = VGroup()
        cell_size = 0.5
        
        for i in range(4):
            for j in range(4):
                # Create cell square
                cell = Square(side_length=cell_size)
                cell.set_stroke(WHITE, 2)
                cell.set_fill(DARK_GRAY, opacity=0.5)
                cell.move_to(np.array([
                    j * cell_size - 1.5 * cell_size,
                    (3 - i) * cell_size - 1.5 * cell_size,
                    0
                ]))
                
                # Create value text
                value = Text(str(feature_map[i][j]), font_size=20, color=WHITE)
                value.move_to(cell.get_center())
                
                input_grid.add(VGroup(cell, value))
        
        input_grid.scale(1.2)
        input_grid.shift(LEFT * 2.5)
        
        # Create input label
        input_label = Text("Input (4×4)", font_size=24, color=YELLOW)
        input_label.next_to(input_grid, UP, buff=0.3)
        
        self.play(
            Write(input_label),
            Create(input_grid),
            run_time=1
        )
        self.wait(0.5)
        
        # Define pooling windows and their max values
        windows = [
            # (row_start, col_start, max_value_pos_in_window)
            (0, 0, (1, 1)),  # Top-left window, max at row 1, col 1
            (0, 2, (1, 0)),  # Top-right window, max at row 1, col 0
            (2, 0, (2, 0)),  # Bottom-left window, max at row 2, col 0
            (2, 2, (2, 1)),  # Bottom-right window, max at row 2, col 1
        ]
        
        max_values = [6, 8, 7, 9]  # Max values for each window
        max_positions = [
            (1, 1),  # Position of 6
            (0, 3),  # Position of 8
            (2, 0),  # Position of 7
            (2, 2),  # Position of 9
        ]
        
        # Highlight max values with colors
        highlight_boxes = VGroup()
        colors = [RED, GREEN, ORANGE, PURPLE]
        
        for idx, (window_row, window_col, (max_row_offset, max_col_offset)) in enumerate(windows):
            actual_row = window_row + max_row_offset
            actual_col = window_col + max_col_offset
            
            # Find the corresponding cell in input_grid
            # The grid is stored row by row but y-position is flipped, so we map visual row to storage index
            cell_idx = (3 - actual_row) * 4 + actual_col
            cell_group = input_grid[cell_idx]
            cell = cell_group[0]
            
            # Create highlight rectangle
            highlight = Rectangle(
                width=cell.width + 0.1,
                height=cell.height + 0.1,
                color=colors[idx],
                stroke_width=4
            )
            highlight.move_to(cell.get_center())
            highlight_boxes.add(highlight)
        
        # Animate highlighting max values
        self.play(
            LaggedStart(*[Create(box) for box in highlight_boxes], lag_ratio=0.3),
            run_time=1.5
        )
        self.wait(0.5)
        
        # Create pooling operation arrow
        arrow = Arrow(
            input_grid.get_right(),
            input_grid.get_right() + RIGHT * 1.5,
            buff=0.3,
            color=BLUE
        )
        
        pool_text = Text("MaxPool 2×2", font_size=18, color=BLUE)
        pool_text.next_to(arrow, UP, buff=0.1)
        
        self.play(
            Create(arrow),
            Write(pool_text),
            run_time=0.8
        )
        self.wait(0.5)
        
        # Create output feature map
        output_grid = VGroup()
        output_values = [[6, 8], [7, 9]]
        
        for i in range(2):
            for j in range(2):
                cell = Square(side_length=cell_size * 1.2)
                cell.set_stroke(WHITE, 2)
                cell.set_fill(colors[i * 2 + j], opacity=0.3)
                cell.move_to(np.array([
                    j * cell_size * 1.5,
                    (1 - i) * cell_size * 1.5,
                    0
                ]))
                
                value = Text(str(output_values[i][j]), font_size=28, color=WHITE)
                value.move_to(cell.get_center())
                
                output_grid.add(VGroup(cell, value))
        
        output_grid.scale(1.2)
        output_grid.shift(RIGHT * 2.5)
        
        output_label = Text("Output (2×2)", font_size=24, color=GREEN)
        output_label.next_to(output_grid, UP, buff=0.3)
        
        # Animate output creation with pulsing effect
        self.play(
            Write(output_label),
            Create(output_grid),
            run_time=1
        )
        
        # Create connecting lines from max values to output
        lines = VGroup()
        for i, (max_row, max_col) in enumerate(max_positions):
            # Get source cell
            # The grid is stored row by row but y-position is flipped, so we map visual row to storage index
            cell_idx = (3 - max_row) * 4 + max_col
            source_cell = input_grid[cell_idx][0]
            
            # Get target cell in output
            target_row = i // 2
            target_col = i % 2
            target_cell = output_grid[i][0]
            
            # Create curved arrow
            line = DashedLine(
                source_cell.get_center(),
                target_cell.get_left(),
                color=colors[i],
                dash_length=0.1
            )
            lines.add(line)
        
        self.play(Create(lines, lag_ratio=0.3), run_time=1.5)
        
        # Pulse highlight on output
        for _ in range(2):
            self.play(
                *[cell[0].animate.scale(1.1) for cell in output_grid],
                run_time=0.3
            )
            self.play(
                *[cell[0].animate.scale(1/1.1) for cell in output_grid],
                run_time=0.3
            )
        
        self.wait(0.5)
        
        # Final summary text
        summary = Text("Downsampling: 4×4 → 2×2", font_size=20, color=WHITE)
        summary.next_to(VGroup(input_grid, output_grid), DOWN, buff=0.5)
        
        self.play(Write(summary), run_time=0.8)
        self.wait(1)
        
        # Fade out everything
        self.play(
            FadeOut(title),
            FadeOut(input_label),
            FadeOut(output_label),
            FadeOut(input_grid),
            FadeOut(output_grid),
            FadeOut(highlight_boxes),
            FadeOut(arrow),
            FadeOut(pool_text),
            FadeOut(lines),
            FadeOut(summary),
            run_time=1
        )


if __name__ == "__main__":
    pass
