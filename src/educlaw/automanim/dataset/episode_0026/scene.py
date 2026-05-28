from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Set frame dimensions for consistent sizing
        self.camera.frame_width = 16
        self.camera.frame_height = 9
        
        # Title
        title = Text("Activation Functions & Gradients", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.3)
        
        # Create axes for activation functions (top row)
        axes_config = {
            "x_range": [-4, 4, 1],
            "y_range": [-1.5, 3, 1],
            "x_length": 3.5,
            "y_length": 2,
            "axis_config": {"color": GRAY, "stroke_width": 1.5},
        }
        
        # Activation function axes
        axes_relu = Axes(**axes_config)
        axes_sigmoid = Axes(**axes_config)
        
        tanh_config = {
            "x_range": [-4, 4, 1],
            "y_range": [-1.5, 1.5, 1],
            "x_length": 3.5,
            "y_length": 2,
            "axis_config": {"color": GRAY, "stroke_width": 1.5},
        }
        axes_tanh = Axes(**tanh_config)
        
        axes_relu.to_edge(LEFT, buff=0.8).shift(UP * 1.5)
        axes_sigmoid.move_to(ORIGIN).shift(UP * 1.5)
        axes_tanh.to_edge(RIGHT, buff=0.8).shift(UP * 1.5)
        
        # Gradient axes (bottom row)
        grad_relu_config = {
            "x_range": [-4, 4, 1],
            "y_range": [0, 1.5, 0.5],
            "x_length": 3.5,
            "y_length": 2,
            "axis_config": {"color": GRAY, "stroke_width": 1.5},
        }
        
        grad_sigmoid_config = {
            "x_range": [-4, 4, 1],
            "y_range": [0, 0.3, 0.1],
            "x_length": 3.5,
            "y_length": 2,
            "axis_config": {"color": GRAY, "stroke_width": 1.5},
        }
        
        grad_tanh_config = {
            "x_range": [-4, 4, 1],
            "y_range": [0, 1.1, 0.2],
            "x_length": 3.5,
            "y_length": 2,
            "axis_config": {"color": GRAY, "stroke_width": 1.5},
        }
        
        axes_relu_grad = Axes(**grad_relu_config)
        axes_sigmoid_grad = Axes(**grad_sigmoid_config)
        axes_tanh_grad = Axes(**grad_tanh_config)
        
        axes_relu_grad.to_edge(LEFT, buff=0.8).shift(DOWN * 1.5)
        axes_sigmoid_grad.move_to(ORIGIN).shift(DOWN * 1.5)
        axes_tanh_grad.to_edge(RIGHT, buff=0.8).shift(DOWN * 1.5)
        
        # Labels
        relu_label = Text("ReLU", font_size=24, color=RED).next_to(axes_relu, UP, buff=0.2)
        sigmoid_label = Text("Sigmoid", font_size=24, color=BLUE).next_to(axes_sigmoid, UP, buff=0.2)
        tanh_label = Text("Tanh", font_size=24, color=GREEN).next_to(axes_tanh, UP, buff=0.2)
        
        grad_label = Text("Gradients", font_size=28, color=YELLOW).shift(DOWN * 0.2)
        
        # Define functions
        def relu(x):
            return max(0, x)
        
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))
        
        def tanh_func(x):
            return np.tanh(x)
        
        def relu_grad(x):
            return 1 if x > 0 else 0
        
        def sigmoid_grad(x):
            s = sigmoid(x)
            return s * (1 - s)
        
        def tanh_grad(x):
            t = tanh_func(x)
            return 1 - t**2
        
        # Create graphs
        relu_graph = axes_relu.plot(relu, x_range=[-4, 4], color=RED, stroke_width=3)
        sigmoid_graph = axes_sigmoid.plot(sigmoid, x_range=[-4, 4], color=BLUE, stroke_width=3)
        tanh_graph = axes_tanh.plot(tanh_func, x_range=[-4, 4], color=GREEN, stroke_width=3)
        
        # Create gradient graphs
        relu_grad_graph = axes_relu_grad.plot(
            relu_grad, x_range=[-4, 4, 0.1], 
            discontinuities=[0], color=RED, stroke_width=3
        )
        sigmoid_grad_graph = axes_sigmoid_grad.plot(sigmoid_grad, x_range=[-4, 4], color=BLUE, stroke_width=3)
        tanh_grad_graph = axes_tanh_grad.plot(tanh_grad, x_range=[-4, 4], color=GREEN, stroke_width=3)
        
        # Animation sequence
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)
        
        # Show activation function labels and axes
        self.play(
            Create(axes_relu), Create(axes_sigmoid), Create(axes_tanh),
            Write(relu_label), Write(sigmoid_label), Write(tanh_label),
            run_time=1.0
        )
        self.wait(0.2)
        
        # Draw ReLU
        self.play(Create(relu_graph), run_time=1.0)
        self.wait(0.3)
        
        # Draw Sigmoid
        self.play(Create(sigmoid_graph), run_time=1.0)
        self.wait(0.3)
        
        # Draw Tanh
        self.play(Create(tanh_graph), run_time=1.0)
        self.wait(0.3)
        
        # Show gradient section
        self.play(
            Create(axes_relu_grad), Create(axes_sigmoid_grad), Create(axes_tanh_grad),
            Write(grad_label),
            run_time=1.0
        )
        self.wait(0.2)
        
        # Draw gradients
        self.play(
            Create(relu_grad_graph),
            Create(sigmoid_grad_graph),
            Create(tanh_grad_graph),
            run_time=1.5
        )
        self.wait(0.5)
        
        # Highlight vanishing gradients in sigmoid and tanh
        highlight_zone = Rectangle(
            width=2.5, height=6, 
            fill_color=YELLOW, fill_opacity=0.15,
            stroke_width=0
        ).move_to(RIGHT * 3)
        
        zone_text = Text("Vanishing Gradient Zone", font_size=18, color=YELLOW)
        zone_text.next_to(highlight_zone, RIGHT, buff=0.2)
        
        self.play(
            FadeIn(highlight_zone),
            Write(zone_text),
            run_time=0.8
        )
        self.wait(1.5)
        
        # Final comparison highlight
        self.play(
            relu_graph.animate.set_stroke(width=5),
            relu_grad_graph.animate.set_stroke(width=5),
            run_time=0.5
        )
        self.wait(0.5)
        
        self.play(
            relu_graph.animate.set_stroke(width=3),
            relu_grad_graph.animate.set_stroke(width=3),
            run_time=0.3
        )
        self.wait(1)
        
        # Fade out
        self.play(FadeOut(*self.mobjects), run_time=1)
