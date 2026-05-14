from manim import *


class AutoScene(Scene):
    def construct(self):
        # Configure for faster animation
        self.camera.background_color = "#1a1a2e"
        
        # Title
        title = Text("Chain Rule in Backpropagation", font_size=36, color=WHITE)
        title.to_edge(UP)
        self.add(title)
        
        # Create computational graph nodes
        node_x = Circle(radius=0.4, color=BLUE, fill_opacity=0.8)
        node_f = Circle(radius=0.4, color=GREEN, fill_opacity=0.8)
        node_y = Circle(radius=0.4, color=RED, fill_opacity=0.8)
        
        node_x.shift(LEFT * 3)
        node_f.shift(ORIGIN)
        node_y.shift(RIGHT * 3)
        
        # Labels
        label_x = Text("x", font_size=28, color=WHITE).move_to(node_x.get_center())
        label_f = Text("f", font_size=28, color=WHITE).move_to(node_f.get_center())
        label_y = Text("y", font_size=28, color=WHITE).move_to(node_y.get_center())
        
        # Arrows
        arrow_xf = Arrow(node_x.get_right(), node_f.get_left(), buff=0.1, color=WHITE)
        arrow_fy = Arrow(node_f.get_right(), node_y.get_left(), buff=0.1, color=WHITE)
        
        # Function labels
        func1 = MathTex("x^2", font_size=24, color=YELLOW).next_to(arrow_xf, UP, buff=0.1)
        
        # Forward pass label
        forward_label = Text("Forward Pass", font_size=24, color=BLUE_C).next_to(title, DOWN, buff=0.5)
        
        # Build graph
        self.play(
            FadeIn(node_x, node_f, node_y),
            run_time=0.5
        )
        self.play(
            Create(arrow_xf),
            Create(arrow_fy),
            Write(label_x),
            Write(label_f),
            Write(label_y),
            run_time=0.5
        )
        self.play(
            Write(func1),
            Write(forward_label),
            run_time=0.5
        )
        
        # Show forward computation
        x_val = MathTex("x = 2", font_size=22, color=BLUE_A).next_to(node_x, DOWN, buff=0.3)
        f_val = MathTex("f = 4", font_size=22, color=GREEN_A).next_to(node_f, DOWN, buff=0.3)
        y_val = MathTex("y = 4", font_size=22, color=RED_A).next_to(node_y, DOWN, buff=0.3)
        
        self.play(Write(x_val), run_time=0.4)
        self.play(
            arrow_xf.animate.set_color(GREEN),
            run_time=0.3
        )
        self.play(Write(f_val), run_time=0.4)
        self.play(
            arrow_fy.animate.set_color(GREEN),
            arrow_xf.animate.set_color(WHITE),
            run_time=0.3
        )
        self.play(Write(y_val), run_time=0.4)
        self.play(
            arrow_fy.animate.set_color(WHITE),
            run_time=0.2
        )
        
        # Backward pass
        backward_label = Text("Backward Pass (Chain Rule)", font_size=24, color=RED_C).next_to(forward_label, DOWN, buff=0.4)
        self.play(Write(backward_label), run_time=0.5)
        
        # Gradient from
        grad_y = MathTex(r"\frac{\partial y}{\partial y} = 1", font_size=20, color=RED_B).next_to(node_y, UP, buff=0.3)
        self.play(Write(grad_y), run_time=0.4)
        self.wait(0.2)
        
        # Chain rule to f
        grad_f = MathTex(r"\frac{\partial y}{\partial f} = 1", font_size=20, color=GREEN_B).next_to(node_f, UP, buff=0.3)
        arrow_fy_back = Arrow(node_y.get_left(), node_f.get_right(), buff=0.1, color=YELLOW)
        formula1 = MathTex(r"\frac{\partial y}{\partial f} \cdot \frac{\partial f}{\partial x}", font_size=18, color=YELLOW).next_to(node_f, DOWN, buff=0.8)
        
        self.play(
            Create(arrow_fy_back),
            Write(grad_f),
            run_time=0.5
        )
        self.wait(0.2)
        
        # Chain rule to x
        grad_x = MathTex(r"\frac{\partial y}{\partial x} = 4", font_size=20, color=BLUE_B).next_to(node_x, UP, buff=0.3)
        arrow_xf_back = Arrow(node_f.get_left(), node_x.get_right(), buff=0.1, color=YELLOW)
        
        self.play(
            Create(arrow_xf_back),
            Write(grad_x),
            run_time=0.5
        )
        self.wait(0.2)
        
        # Chain rule formula
        chain_rule = MathTex(
            r"\frac{\partial y}{\partial x} = \frac{\partial y}{\partial f} \cdot \frac{\partial f}{\partial x} = 1 \cdot 4 = 4",
            font_size=22,
            color=YELLOW
        ).to_edge(DOWN, buff=0.5)
        
        self.play(Write(chain_rule), run_time=0.6)
        self.wait(0.5)
        
        # Highlight final result
        self.play(
            grad_x.animate.scale(1.3).set_color(GOLD),
            chain_rule.animate.set_color(GOLD),
            run_time=0.5
        )
        self.wait(0.5)
