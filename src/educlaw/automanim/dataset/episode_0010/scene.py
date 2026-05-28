"""Dropout Training vs Inference Animation"""

from manim import *
import random


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Dropout: Training vs Inference", font_size=36)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        self.wait(0.3)
        
        # Create side-by-side labels
        training_label = Text("Training (Dropout)", font_size=28, color=YELLOW)
        inference_label = Text("Inference (Active)", font_size=28, color=GREEN)
        
        training_label.to_edge(LEFT, buff=2)
        training_label.shift(DOWN * 0.5)
        inference_label.to_edge(RIGHT, buff=2)
        inference_label.shift(DOWN * 0.5)
        
        self.play(
            FadeIn(training_label),
            FadeIn(inference_label),
            run_time=0.5
        )
        
        # Create network structure for both sides
        left_network = self.create_network(LEFT * 3)
        right_network = self.create_network(RIGHT * 3)
        
        self.play(
            *[Create(neuron) for neuron in left_network],
            *[Create(neuron) for neuron in right_network],
            run_time=1.0
        )
        
        # Create connections
        left_connections = self.create_connections(left_network)
        right_connections = self.create_connections(right_network)
        
        self.play(
            *[Create(conn) for conn in left_connections],
            *[Create(conn) for conn in right_connections],
            run_time=0.5
        )
        
        self.wait(0.3)
        
        # Animation: Training with dropout
        dropout_text = Text("Randomly zeroing neurons", font_size=20, color=RED)
        dropout_text.next_to(training_label, DOWN, buff=0.3)
        self.play(FadeIn(dropout_text))
        
        # Animate dropout on left side (multiple rounds)
        for round_num in range(3):
            # Random dropout pattern
            left_dots = self.get_dropout_dots(left_network, 0.4)
            self.play(
                *[dot.animate.set_color(RED).set_opacity(0.3) for dot in left_dots],
                run_time=0.4
            )
            
            # Show "X" marks on dropped neurons
            crosses = [Cross(dot).scale(0.3) for dot in left_dots]
            self.play(*[Create(cross) for cross in crosses], run_time=0.2)
            
            self.wait(0.2)
            
            # Restore for next round
            if round_num < 2:
                self.play(
                    *[dot.animate.set_color(WHITE).set_opacity(1) for dot in left_dots],
                    *[FadeOut(cross) for cross in crosses],
                    run_time=0.3
                )
            else:
                # Last round - keep them visible
                self.play(FadeOut(dropout_text))
        
        # Show inference side (all active)
        inference_text = Text("All neurons active", font_size=20, color=GREEN)
        inference_text.next_to(inference_label, DOWN, buff=0.3)
        self.play(FadeIn(inference_text))
        
        # Pulse all right-side neurons to show they're all active
        self.play(
            *[dot.animate.scale(1.3).set_color(GREEN) for dot in right_network],
            run_time=0.3
        )
        self.play(
            *[dot.animate.scale(0.77).set_color(WHITE) for dot in right_network],
            run_time=0.3
        )
        
        # Show scaling explanation
        scale_text = Text("Scaling: multiply by (1 - dropout_rate)", font_size=22, color=BLUE)
        scale_text.to_edge(DOWN, buff=0.8)
        self.play(Write(scale_text))
        
        # Visual representation of scaling
        scaling_arrow = Arrow(LEFT * 4, RIGHT * 4, color=BLUE)
        scaling_arrow.next_to(scale_text, UP, buff=0.3)
        
        scale_label = Text("Output × 0.6", font_size=18, color=BLUE)
        scale_label.next_to(scaling_arrow, UP, buff=0.2)
        
        self.play(GrowArrow(scaling_arrow), FadeIn(scale_label))
        
        self.wait(1.0)
        
        # Final fade out
        self.play(
            FadeOut(title),
            FadeOut(training_label),
            FadeOut(inference_label),
            FadeOut(inference_text),
            FadeOut(scale_text),
            FadeOut(scaling_arrow),
            FadeOut(scale_label),
            *[FadeOut(neuron) for neuron in left_network],
            *[FadeOut(neuron) for neuron in right_network],
            *[FadeOut(conn) for conn in left_connections],
            *[FadeOut(conn) for conn in right_connections],
            *[FadeOut(cross) for cross in crosses],
            run_time=0.5
        )
        
        self.wait(0.5)
    
    def create_network(self, center_offset):
        """Create a simple 3-layer neural network."""
        neurons = []
        layers = [3, 5, 4, 2]  # Input, Hidden1, Hidden2, Output
        
        for layer_idx, layer_size in enumerate(layers):
            x_pos = (layer_idx - 1.5) * 1.2
            for neuron_idx in range(layer_size):
                y_offset = (neuron_idx - layer_size / 2 + 0.5) * 0.6
                dot = Dot(
                    point=center_offset + np.array([x_pos, y_offset, 0]),
                    radius=0.1,
                    color=WHITE
                )
                neurons.append(dot)
        
        return neurons
    
    def create_connections(self, neurons):
        """Create connections between neurons."""
        connections = []
        layers_structure = [3, 5, 4, 2]
        
        # Calculate indices
        idx = 0
        layer_indices = []
        for size in layers_structure:
            layer_indices.append(list(range(idx, idx + size)))
            idx += size
        
        # Create connections between adjacent layers
        for layer_idx in range(len(layer_indices) - 1):
            for i in layer_indices[layer_idx]:
                for j in layer_indices[layer_idx + 1]:
                    line = Line(
                        neurons[i].get_center(),
                        neurons[j].get_center(),
                        stroke_width=1,
                        color=GRAY,
                        stroke_opacity=0.4
                    )
                    connections.append(line)
        
        return connections
    
    def get_dropout_dots(self, neurons, dropout_rate):
        """Randomly select neurons to dropout."""
        # Group neurons by layer (skip input and output layers)
        layers_structure = [3, 5, 4, 2]
        hidden_start = layers_structure[0]
        hidden_end = hidden_start + layers_structure[1] + layers_structure[2]
        
        # Get hidden layer neurons
        hidden_neurons = neurons[hidden_start:hidden_end]
        
        # Randomly select neurons to dropout
        num_to_drop = max(1, int(len(hidden_neurons) * dropout_rate))
        return random.sample(hidden_neurons, num_to_drop)
