"""
MLP Forward Pass Animation
3-layer neural network with numerical values flowing through.
"""
from manim import *


class AutoScene(Scene):
    def construct(self):
        # Configuration
        np.random.seed(42)
        
        # Layer sizes
        input_size = 3
        hidden_size = 4
        output_size = 2
        
        # Create sample data
        inputs = np.array([1.0, 0.5, -0.3])
        W1 = np.array([[0.2, -0.5, 0.8], [0.7, 0.3, -0.2], [-0.4, 0.6, 0.1], [0.5, -0.3, 0.4]])
        b1 = np.array([0.1, -0.2, 0.3, 0.0])
        W2 = np.array([[0.3, -0.4, 0.5, 0.2], [-0.6, 0.1, 0.3, -0.5]])
        b2 = np.array([0.2, -0.1])
        
        # Forward pass calculations
        z1 = np.dot(W1, inputs) + b1
        a1 = np.maximum(z1, 0)  # ReLU
        z2 = np.dot(W2, a1) + b2
        exp_z = np.exp(z2 - np.max(z2))
        outputs = exp_z / np.sum(exp_z)  # Softmax
        
        # Title
        title = Text("MLP Forward Pass", font_size=36, color=BLUE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        self.wait(0.5)
        
        # Create layers
        layer_spacing = 4
        node_spacing = 0.8
        
        def create_layer_nodes(count, x_pos, color):
            nodes = VGroup()
            for i in range(count):
                y = (count - 1) * node_spacing / 2 - i * node_spacing
                circle = Circle(radius=0.3, fill_color=color, fill_opacity=0.3, stroke_color=color, stroke_width=2)
                circle.move_to([x_pos, y, 0])
                nodes.add(circle)
            return nodes
        
        input_layer = create_layer_nodes(input_size, -layer_spacing, GREEN)
        hidden_layer = create_layer_nodes(hidden_size, 0, YELLOW)
        output_layer = create_layer_nodes(output_size, layer_spacing, RED)
        
        # Layer labels
        input_label = Text("Input\n(x)", font_size=20, color=GREEN).next_to(input_layer, LEFT)
        hidden_label = Text("Hidden\n(h)", font_size=20, color=YELLOW).next_to(hidden_layer, UP)
        output_label = Text("Output\n(ŷ)", font_size=20, color=RED).next_to(output_layer, RIGHT)
        
        # Draw layers with labels
        self.play(
            Create(input_layer),
            Create(hidden_layer),
            Create(output_layer),
            Write(input_label),
            Write(hidden_label),
            Write(output_label),
            run_time=1.5
        )
        self.wait(0.3)
        
        # Create connections (weights)
        def create_connections(from_layer, to_layer, opacity=0.3):
            connections = VGroup()
            for from_node in from_layer:
                for to_node in to_layer:
                    line = Line(from_node.get_center(), to_node.get_center(), stroke_width=1, stroke_opacity=opacity)
                    connections.add(line)
            return connections
        
        input_hidden = create_connections(input_layer, hidden_layer)
        hidden_output = create_connections(hidden_layer, output_layer)
        
        self.play(Create(input_hidden), Create(hidden_output), run_time=1)
        self.wait(0.3)
        
        # Add input values
        input_values = VGroup()
        for i, (node, val) in enumerate(zip(input_layer, inputs)):
            val_text = MathTex(f"{val:.1f}", font_size=20, color=WHITE)
            val_text.move_to(node.get_center())
            input_values.add(val_text)
        
        self.play(Create(input_values), run_time=0.8)
        self.wait(0.3)
        
        # Animate values flowing to hidden layer
        dots_hidden = VGroup()
        hidden_calcs = []
        
        for j, hidden_node in enumerate(hidden_layer):
            # Create moving dots along paths
            for i, input_node in enumerate(input_layer):
                dot = Dot(radius=0.08, color=GREEN)
                dot.move_to(input_node.get_center())
                dots_hidden.add(dot)
                
                # Animate dot
                path = Line(input_node.get_center(), hidden_node.get_center())
                self.play(MoveAlongPath(dot, path), run_time=0.4)
            
            # Show weighted sum calculation
            calc_parts = []
            for i in range(input_size):
                calc_parts.append(f"{W1[j,i]:.1f} \\cdot {inputs[i]:.1f}")
            calc_text = MathTex(f"z_{{{j+1}}} = " + " + ".join(calc_parts) + f" + {b1[j]:.1f}", font_size=16)
            calc_text.next_to(hidden_node, DOWN*0.5)
            
            # Show ReLU activation
            relu_text = MathTex(f"a_{{{j+1}}} = \\text{{ReLU}}({z1[j]:.2f}) = {a1[j]:.2f}", font_size=16, color=YELLOW)
            relu_text.next_to(calc_text, DOWN*0.5)
            
            hidden_calcs.extend([calc_text, relu_text])
            
            # Show activation result on node
            result = MathTex(f"{a1[j]:.2f}", font_size=18, color=YELLOW)
            result.move_to(hidden_node.get_center())
            
            self.play(
                Write(calc_text),
                Write(relu_text),
                Transform(dots_hidden[j*input_size:(j+1)*input_size], 
                         VGroup(*[result.copy() for _ in range(input_size)])),
                run_time=0.8
            )
            self.add(result)
            self.remove(dots_hidden[j*input_size:(j+1)*input_size])
            self.wait(0.2)
        
        # Clean up calculations
        self.play(FadeOut(*hidden_calcs), run_time=0.5)
        self.wait(0.3)
        
        # Store activation results
        activation_results = VGroup()
        for j, (hidden_node, val) in enumerate(zip(hidden_layer, a1)):
            result = MathTex(f"{val:.2f}", font_size=18, color=YELLOW)
            result.move_to(hidden_node.get_center())
            activation_results.add(result)
        
        # Animate values flowing to output layer
        dots_output = VGroup()
        output_calcs = []
        
        for k, output_node in enumerate(output_layer):
            # Create moving dots
            for j, hidden_node in enumerate(hidden_layer):
                dot = Dot(radius=0.08, color=YELLOW)
                dot.move_to(hidden_node.get_center())
                dots_output.add(dot)
                
                path = Line(hidden_node.get_center(), output_node.get_center())
                self.play(MoveAlongPath(dot, path), run_time=0.4)
            
            # Show weighted sum
            calc_parts = []
            for j in range(hidden_size):
                calc_parts.append(f"{W2[k,j]:.1f} \\cdot {a1[j]:.2f}")
            calc_text = MathTex(f"z_{{{k+1}}} = " + " + ".join(calc_parts) + f" + {b2[k]:.1f}", font_size=16)
            calc_text.next_to(output_node, UP*0.5)
            
            output_calcs.append(calc_text)
            
            # Final output value
            result = MathTex(f"{outputs[k]:.3f}", font_size=18, color=RED)
            result.move_to(output_node.get_center())
            
            self.play(
                Write(calc_text),
                Transform(dots_output[k*hidden_size:(k+1)*hidden_size],
                         VGroup(*[result.copy() for _ in range(hidden_size)])),
                run_time=0.8
            )
            self.add(result)
            self.remove(dots_output[k*hidden_size:(k+1)*hidden_size])
            self.wait(0.2)
        
        # Add Softmax explanation
        softmax_eq = MathTex(
            r"\hat{y}_k = \frac{e^{z_k}}{\sum_j e^{z_j}}", 
            font_size=20, color=ORANGE
        )
        softmax_eq.to_edge(DOWN, buff=0.5)
        
        # Prediction result
        pred_text = Text(f"Prediction: Class {np.argmax(outputs)}", font_size=28, color=GREEN)
        pred_text.next_to(output_layer, DOWN*2)
        
        self.play(
            Write(softmax_eq),
            Write(pred_text),
            run_time=1
        )
        
        # Final flash
        self.play(
            Flash(output_layer[np.argmax(outputs)], line_length=0.4, flash_radius=0.5, color=GREEN),
            run_time=0.8
        )
        
        self.wait(1)
        
        # Fade out everything
        self.play(FadeOut(*self.mobjects), run_time=1)
        
        # Final summary text
        summary = VGroup(
            Text("Forward Pass Complete!", font_size=36, color=BLUE),
            MathTex(r"\mathbf{z}^{[l]} = W^{[l]} \mathbf{a}^{[l-1]} + \mathbf{b}^{[l]}", font_size=28),
            MathTex(r"\mathbf{a}^{[l]} = g(\mathbf{z}^{[l]})", font_size=28)
        ).arrange(DOWN, buff=0.5)
        
        self.play(Write(summary), run_time=1.5)
        self.wait(1)
