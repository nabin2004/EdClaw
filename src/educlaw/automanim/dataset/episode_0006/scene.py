"""
Vanishing Gradient Problem Visualization
Shows gradients shrinking layer by layer during backpropagation
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Vanishing Gradient Problem", font_size=36)
        subtitle = Text("Backpropagation: Gradients Shrink Layer by Layer", font_size=20)
        subtitle.next_to(title, DOWN, buff=0.3)
        
        title_group = VGroup(title, subtitle)
        title_group.to_edge(UP)
        
        self.play(Write(title))
        self.play(Write(subtitle))
        self.wait(0.5)
        
        # Neural network layers structure
        num_layers = 6
        layer_y = 1.0
        neurons_per_layer = 3
        neuron_radius = 0.15
        layer_spacing = 2.0
        
        # Create neurons for each layer
        layers = []
        for l in range(num_layers):
            neurons = VGroup()
            x_pos = (l - num_layers/2) * layer_spacing
            for n in range(neurons_per_layer):
                y_pos = (n - neurons_per_layer/2) * 0.6
                neuron = Circle(radius=neuron_radius, color=WHITE).move_to([x_pos, y_pos + layer_y, 0])
                neuron.set_fill(BLACK, opacity=1)
                neurons.add(neuron)
            layers.append(neurons)
        
        # Show forward pass
        forward_label = Text("Forward Pass", font_size=24, color=GREEN).to_edge(DOWN).shift(UP * 0.5)
        all_neurons = VGroup()
        for layer in layers:
            for n in layer:
                all_neurons.add(n)
        
        self.play(Create(all_neurons))
        self.play(Write(forward_label))
        
        # Animate forward arrows
        for i in range(num_layers - 1):
            arrows = VGroup()
            for src in layers[i]:
                for dst in layers[i + 1]:
                    arrow = Arrow(src.get_right(), dst.get_left(), buff=0.05, color=GREEN, stroke_width=1)
                    arrows.add(arrow)
            self.play(FadeIn(arrows, scale=0.5), run_time=0.2)
        
        self.wait(0.2)
        self.play(FadeOut(forward_label))
        
        # Backprop label
        backprop_label = Text("Backpropagation: Gradients Flow →", font_size=24, color=RED)
        backprop_label.to_edge(DOWN).shift(UP * 0.5)
        self.play(Write(backprop_label))
        
        # Calculate gradient magnitudes (decreasing exponentially)
        # Last layer (output) has gradient 1.0, earlier layers vanish
        gradient_magnitudes = [1.0 * (0.25 ** (num_layers - 1 - i)) for i in range(num_layers)]
        max_magnitude = max(gradient_magnitudes)
        
        # Create gradient bars below each layer
        bar_width = 0.8
        max_bar_height = 2.5
        bars = VGroup()
        bar_labels = VGroup()
        
        for i, mag in enumerate(gradient_magnitudes):
            x_pos = (i - num_layers/2) * layer_spacing
            bar_height = (mag / max_magnitude) * max_bar_height
            
            # Create bar
            bar = Rectangle(
                width=bar_width,
                height=bar_height,
                color=RED,
                fill_opacity=0.8,
                fill_color=RED
            )
            bar.move_to([x_pos, -1.5, 0])
            
            # Mag label
            label = Text(f"{mag:.4f}", font_size=16, color=YELLOW)
            label.next_to(bar, DOWN, buff=0.2)
            
            # Layer number
            layer_label = Text(f"L{i+1}", font_size=18, color=WHITE)
            layer_label.next_to(layers[i], UP, buff=0.3)
            
            bars.add(bar)
            bar_labels.add(VGroup(label, layer_label))
        
        # Animate backprop from output to input
        for i in range(num_layers - 1, -1, -1):
            # Highlight current layer
            self.play(
                layers[i].animate.set_stroke(RED, width=3),
                run_time=0.2
            )
            
            # Show gradient bar growing from bottom
            target_height = (gradient_magnitudes[i] / max_magnitude) * max_bar_height
            bars[i].scale(0.01)
            bars[i].move_to([bars[i].get_center()[0], -1.5 - max_bar_height/2, 0], aligned_edge=DOWN)
            self.play(
                bars[i].animate.scale(100 * target_height / ((gradient_magnitudes[i] / max_magnitude) * max_bar_height)).move_to([bars[i].get_center()[0], -1.5, 0]),
                Write(bar_labels[i]),
                run_time=0.3
            )
            
            # Draw backprop arrow from next layer if not last
            if i < num_layers - 1:
                back_arrows = VGroup()
                for dst in layers[i]:
                    for src in layers[i + 1]:
                        arrow = Arrow(
                            src.get_bottom() + DOWN * 0.1,
                            dst.get_bottom() + DOWN * 0.1,
                            buff=layer_spacing - 0.3,
                            color=RED,
                            stroke_width=1,
                            max_stroke_width_to_length_ratio=5
                        )
                        back_arrows.add(arrow)
                
                # Pulse effect showing gradient flow
                self.play(
                    FadeIn(back_arrows),
                    run_time=0.2
                )
                self.play(FadeOut(back_arrows), run_time=0.1)
            
            # Reset layer color
            if i > 0:
                self.play(
                    layers[i].animate.set_stroke(WHITE, width=1),
                    run_time=0.1
                )
        
        # Fade out backprop label before the comparison
        self.play(FadeOut(backprop_label), run_time=0.2)
        
        # Highlight the vanishing problem
        vanish_text = Text("Gradients Vanish!", font_size=28, color=YELLOW)
        vanish_text.move_to([-(num_layers/2 - 0.5) * layer_spacing, -2.5, 0])
        vanish_text.shift(LEFT * 2)
        
        arrow_to_first = Arrow(
            vanish_text.get_right(),
            bars[0].get_left(),
            color=YELLOW,
            buff=0.2
        )
        
        # Compare first and last layer
        self.play(
            bars[0].animate.set_fill(YELLOW, opacity=1),
            bars[-1].animate.set_fill(YELLOW, opacity=1),
            run_time=0.3
        )
        
        self.play(
            Write(vanish_text),
            Create(arrow_to_first),
            run_time=0.3
        )
        
        # Add magnitude comparison text
        compare_text = Text(f"L{num_layers}: {gradient_magnitudes[-1]:.4f}  →  L1: {gradient_magnitudes[0]:.6f}", 
                           font_size=24, color=WHITE)
        compare_text.next_to(vanish_text, DOWN, buff=0.5)
        
        self.play(Write(compare_text))
        
        self.wait(0.5)
        
        # Final message - fade everything and show conclusion
        final_message = Text("Early Layers Learn Almost Nothing", font_size=32, color=RED)
        final_message.to_edge(DOWN).shift(UP * 0.3)
        
        self.play(
            FadeOut(all_neurons),
            FadeOut(bars),
            FadeOut(bar_labels),
            FadeOut(arrow_to_first),
            FadeOut(vanish_text),
            FadeOut(compare_text),
            FadeOut(title_group),
            run_time=0.3
        )
        
        self.play(Write(final_message))
        self.wait(1.0)
