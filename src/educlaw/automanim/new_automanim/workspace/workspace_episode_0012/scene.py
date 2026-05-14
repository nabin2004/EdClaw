from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Convolution: Filter Sliding Over Image", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Input image (5x5)
        image_size = 5
        filter_size = 3
        cell_size = 0.6

        # Create input image grid
        image_grid = VGroup()
        image_values = [
            [1, 2, 3, 4, 5],
            [2, 3, 4, 5, 6],
            [3, 4, 5, 6, 7],
            [4, 5, 6, 7, 8],
            [5, 6, 7, 8, 9]
        ]

        for i in range(image_size):
            for j in range(image_size):
                cell = Square(side_length=cell_size, stroke_color=BLUE, stroke_width=2)
                cell.shift((j - image_size/2 + 0.5) * cell_size * RIGHT +
                          (image_size/2 - i - 0.5) * cell_size * UP)
                value = Text(str(image_values[i][j]), font_size=20)
                value.move_to(cell.get_center())
                image_grid.add(VGroup(cell, value))

        image_group = VGroup(*image_grid)
        image_group.shift(2 * LEFT + 0.5 * DOWN)

        input_label = Text("Input Image (5x5)", font_size=24)
        input_label.next_to(image_group, DOWN, buff=0.5)

        self.play(Create(image_grid), Write(input_label))
        self.wait(0.5)

        # Create filter/kernel
        kernel_values = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        kernel_grid = VGroup()

        for i in range(filter_size):
            for j in range(filter_size):
                cell = Square(side_length=cell_size, stroke_color=RED, stroke_width=3,
                            fill_color=RED, fill_opacity=0.2)
                cell.shift((j - filter_size/2 + 0.5) * cell_size * RIGHT +
                          (filter_size/2 - i - 0.5) * cell_size * UP)
                value = Text(str(kernel_values[i][j]), font_size=20, color=RED)
                value.move_to(cell.get_center())
                kernel_grid.add(VGroup(cell, value))

        kernel_group = VGroup(*kernel_grid)
        kernel_group.move_to(image_grid[0].get_center())

        kernel_label = Text("Filter (3x3)", font_size=24, color=RED)
        kernel_label.to_edge(RIGHT).shift(2 * UP)

        self.play(Create(kernel_grid), Write(kernel_label))
        self.wait(0.5)

        # Output feature map (3x3)
        output_values = [[0 for _ in range(3)] for _ in range(3)]
        output_grid = VGroup()

        for i in range(3):
            for j in range(3):
                cell = Square(side_length=cell_size, stroke_color=GREEN, stroke_width=2)
                cell.shift((j - 1.5 + 0.5) * cell_size * RIGHT +
                          (1.5 - i - 0.5) * cell_size * UP)
                value = Text("?", font_size=24, color=YELLOW)
                value.move_to(cell.get_center())
                output_grid.add(VGroup(cell, value))

        output_group = VGroup(*output_grid)
        output_group.to_edge(RIGHT).shift(0.5 * DOWN)

        output_label = Text("Output Feature Map", font_size=24)
        output_label.next_to(output_group, DOWN, buff=0.5)

        self.play(Create(output_grid), Write(output_label))
        self.wait(0.5)

        # Animate convolution - sliding filter
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]

        calc_text = MathTex(r"\text{Dot Product} = \sum (i \cdot k)", font_size=24)
        calc_text.to_edge(UP).shift(DOWN)

        for idx, (row, col) in enumerate(positions):
            # Calculate target position
            target_idx = row * image_size + col
            target_pos = image_grid[target_idx].get_center()

            # Move kernel to position
            self.play(kernel_group.animate.move_to(target_pos), run_time=0.4)

            if idx == 0:
                self.play(Write(calc_text))

            # Highlight overlapping cells
            overlaps = []
            dot_products = []

            for ki in range(filter_size):
                for kj in range(filter_size):
                    ii = row + ki
                    ij = col + kj
                    img_idx = ii * image_size + ij
                    img_cell = image_grid[img_idx][0]
                    kern_cell = kernel_grid[ki * filter_size + kj][1]

                    # Highlight
                    highlight = Rectangle(
                        width=cell_size * 0.9,
                        height=cell_size * 0.9,
                        stroke_color=YELLOW,
                        stroke_width=4,
                        fill_color=YELLOW,
                        fill_opacity=0.3
                    )
                    highlight.move_to(img_cell.get_center())
                    overlaps.append(highlight)

                    # Calculate individual product
                    iv = image_values[ii][ij]
                    kv = kernel_values[ki][kj]
                    dot_products.append(iv * kv)

            self.play(*[Create(h) for h in overlaps], run_time=0.3)

            # Show calculation
            total = sum(dot_products)

            calc_display = MathTex(
                f"{image_values[row][col]}\\cdot{kernel_values[0][0]} + "
                f"{image_values[row][col+1]}\\cdot{kernel_values[0][1]} + ... = {total}",
                font_size=20
            )
            calc_display.next_to(calc_text, DOWN)

            self.play(Write(calc_display), run_time=0.3)

            # Update output grid
            output_values[row][col] = total
            new_value = Text(str(total), font_size=24, color=GREEN)
            new_value.move_to(output_grid[row * 3 + col][0].get_center())

            self.play(
                Transform(output_grid[row * 3 + col][1], new_value),
                FadeOut(calc_display),
                *[FadeOut(h) for h in overlaps],
                run_time=0.3
            )

            self.wait(0.2)

        # Final summary
        self.play(FadeOut(calc_text))

        summary = Text("Output Feature Map computed!", font_size=28, color=YELLOW)
        summary.to_edge(UP).shift(DOWN * 0.5)

        self.play(Write(summary))

        # Show final output with values
        highlight_box = SurroundingRectangle(output_group, color=GREEN, buff=0.2)
        self.play(Create(highlight_box))

        self.wait(2)

        # Fade out everything
        self.play(
            FadeOut(title),
            FadeOut(summary),
            FadeOut(image_group),
            FadeOut(input_label),
            FadeOut(kernel_group),
            FadeOut(kernel_label),
            FadeOut(output_group),
            FadeOut(output_label),
            FadeOut(highlight_box)
        )

        # Final message
        final = Text("Convolution Complete!", font_size=40, color=BLUE)
        self.play(Write(final))
        self.wait(1.5)
