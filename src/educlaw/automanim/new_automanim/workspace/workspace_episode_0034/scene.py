"""Feedforward Sublayer Animation for Transformer Visualization."""

from manim import *


class AutoScene(Scene):
    """Visualizes the feedforward sublayer: Linear -> ReLU -> Linear with dimensions."""

    def construct(self):
        # Title
        title = Text("Transformer Feedforward Sublayer", font_size=36)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        self.wait(0.5)

        # Define dimensions
        d_model = 512
        d_ff = 2048

        # Create input vector
        input_vec = Rectangle(height=3, width=0.8, fill_color=BLUE, fill_opacity=0.8)
        input_vec.shift(LEFT * 5)
        input_label = Text(f"{d_model}", font_size=20, color=WHITE)
        input_label.move_to(input_vec)
        input_group = VGroup(input_vec, input_label)
        input_text = Text("Input", font_size=20).next_to(input_vec, DOWN, buff=0.3)

        # Create first Linear layer representation (weight matrix)
        linear1 = Rectangle(height=3.5, width=0.8, fill_color=GREEN, fill_opacity=0.8)
        linear1.shift(LEFT * 2.5)
        linear1_label = Text("W₁", font_size=24, color=WHITE)
        linear1_label.move_to(linear1)
        linear1_group = VGroup(linear1, linear1_label)

        # Bias 1
        bias1 = Rectangle(height=0.5, width=0.8, fill_color=YELLOW, fill_opacity=0.8)
        bias1.next_to(linear1, DOWN, buff=0.5)
        bias1_label = Text("b₁", font_size=20, color=WHITE)
        bias1_label.move_to(bias1)
        bias1_group = VGroup(bias1, bias1_label)

        # Dimension label for W1
        dim_w1 = Text(f"{d_ff} × {d_model}", font_size=18, color=YELLOW)
        dim_w1.next_to(linear1, UP, buff=0.2)

        # Create hidden state (after first linear)
        hidden_vec = Rectangle(height=4, width=0.8, fill_color=PURPLE, fill_opacity=0.8)
        hidden_vec.shift(RIGHT * 0.5)
        hidden_label = Text(f"{d_ff}", font_size=20, color=WHITE)
        hidden_label.move_to(hidden_vec)
        hidden_group = VGroup(hidden_vec, hidden_label)
        hidden_text = Text("Hidden", font_size=20).next_to(hidden_vec, DOWN, buff=0.3)

        # Create ReLU activation
        relu_box = RoundedRectangle(height=1.5, width=1.2, corner_radius=0.2, fill_color=RED, fill_opacity=0.8)
        relu_box.shift(RIGHT * 3)
        relu_label = Text("ReLU", font_size=22, color=WHITE)
        relu_label.move_to(relu_box)
        relu_group = VGroup(relu_box, relu_label)

        # Create second Linear layer (weight matrix)
        linear2 = Rectangle(height=4, width=0.8, fill_color=GREEN, fill_opacity=0.8)
        linear2.shift(RIGHT * 5.5)
        linear2_label = Text("W₂", font_size=24, color=WHITE)
        linear2_label.move_to(linear2)
        linear2_group = VGroup(linear2, linear2_label)

        # Bias 2
        bias2 = Rectangle(height=0.5, width=0.8, fill_color=YELLOW, fill_opacity=0.8)
        bias2.next_to(linear2, DOWN, buff=0.5)
        bias2_label = Text("b₂", font_size=20, color=WHITE)
        bias2_label.move_to(bias2)
        bias2_group = VGroup(bias2, bias2_label)

        # Dimension label for W2
        dim_w2 = Text(f"{d_model} × {d_ff}", font_size=18, color=YELLOW)
        dim_w2.next_to(linear2, UP, buff=0.2)

        # Create output vector
        output_vec = Rectangle(height=3, width=0.8, fill_color=BLUE, fill_opacity=0.8)
        output_vec.shift(RIGHT * 8.5)
        output_label = Text(f"{d_model}", font_size=20, color=WHITE)
        output_label.move_to(output_vec)
        output_group = VGroup(output_vec, output_label)
        output_text = Text("Output", font_size=20).next_to(output_vec, DOWN, buff=0.3)

        # Arrows
        arrow1 = Arrow(input_vec.get_right(), linear1.get_left(), buff=0.3, color=WHITE)
        arrow2 = Arrow(linear1.get_right(), hidden_vec.get_left(), buff=0.3, color=WHITE)
        arrow3 = Arrow(hidden_vec.get_right(), relu_box.get_left(), buff=0.3, color=WHITE)
        arrow4 = Arrow(relu_box.get_right(), linear2.get_left(), buff=0.3, color=WHITE)
        arrow5 = Arrow(linear2.get_right(), output_vec.get_left(), buff=0.3, color=WHITE)

        # Dimension arrows showing expansion and contraction
        dim_arrow1 = Arrow(
            input_vec.get_top() + UP * 0.5,
            hidden_vec.get_top() + UP * 0.5,
            buff=0.1,
            color=YELLOW,
            stroke_width=2
        )
        expand_text = Text("Expand", font_size=16, color=YELLOW)
        expand_text.next_to(dim_arrow1, UP, buff=0.1)

        dim_arrow2 = Arrow(
            hidden_vec.get_top() + UP * 0.5,
            output_vec.get_top() + UP * 1.3,
            buff=0.1,
            color=YELLOW,
            stroke_width=2
        )
        project_text = Text("Project", font_size=16, color=YELLOW)
        project_text.next_to(dim_arrow2, UP, buff=0.1)

        # Animation sequence
        self.play(Create(input_group), Write(input_text))
        self.wait(0.3)

        self.play(Create(linear1_group), Create(bias1_group), Write(dim_w1))
        self.wait(0.3)

        self.play(GrowArrow(arrow1))
        self.wait(0.2)
        self.play(GrowArrow(arrow2))
        self.wait(0.3)

        self.play(Create(hidden_group), Write(hidden_text))
        self.wait(0.3)

        self.play(GrowArrow(dim_arrow1), Write(expand_text))
        self.wait(0.3)

        self.play(Create(relu_group))
        self.wait(0.3)

        self.play(GrowArrow(arrow3))
        self.wait(0.2)
        self.play(GrowArrow(arrow4))
        self.wait(0.3)

        self.play(Create(linear2_group), Create(bias2_group), Write(dim_w2))
        self.wait(0.3)

        self.play(GrowArrow(dim_arrow2), Write(project_text))
        self.wait(0.3)

        self.play(GrowArrow(arrow5))
        self.wait(0.3)

        self.play(Create(output_group), Write(output_text))
        self.wait(0.3)

        # Formula at bottom
        formula = MathTex(r"FFN(x) = W_2 \cdot ReLU(W_1 x + b_1) + b_2", font_size=28)
        formula.to_edge(DOWN, buff=0.5)
        self.play(Write(formula))
        self.wait(1)

        # Highlight the flow
        flow_highlight = VGroup(
            input_group, arrow1, linear1_group, arrow2, hidden_group,
            arrow3, relu_group, arrow4, linear2_group, arrow5, output_group
        )
        self.play(
            flow_highlight.animate.scale(1.05),
            run_time=0.5
        )
        self.play(
            flow_highlight.animate.scale(1/1.05),
            run_time=0.5
        )
        self.wait(0.5)
