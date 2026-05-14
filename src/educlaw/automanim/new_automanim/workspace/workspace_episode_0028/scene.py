"""
ResNet Skip Connections Animation
Shows how gradients flow backward through skip connections, bypassing layers.
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("ResNet Skip Connections", font_size=36)
        subtitle = Text("Gradient Flow During Backpropagation", font_size=24, color=BLUE)
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.3)
        title_group.to_edge(UP)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(0.5)
        
        # Create main network layers on the right
        layer_colors = [BLUE, TEAL, GREEN]
        layers = []
        layer_labels = []
        
        for i in range(3):
            rect = Rectangle(height=1.2, width=1.5, fill_color=layer_colors[i], fill_opacity=0.6)
            rect.shift(RIGHT * 2 + DOWN * (i - 1) * 1.8)
            layers.append(rect)
            
            label = Text(f"Layer {i+1}", font_size=16)
            label.next_to(rect, RIGHT, buff=0.2)
            layer_labels.append(label)
        
        # Input and output
        input_box = Rectangle(height=0.8, width=1.2, fill_color=GRAY, fill_opacity=0.5)
        input_box.shift(LEFT * 3)
        input_label = Text("Input", font_size=16).next_to(input_box, LEFT, buff=0.2)
        
        output_box = Rectangle(height=0.8, width=1.2, fill_color=YELLOW, fill_opacity=0.5)
        output_box.shift(RIGHT * 4.5)
        output_label = Text("Output", font_size=16).next_to(output_box, RIGHT, buff=0.2)
        
        # Draw main network
        self.play(
            Create(input_box),
            Write(input_label)
        )
        
        for layer, label in zip(layers, layer_labels):
            self.play(Create(layer), Write(label), run_time=0.4)
        
        self.play(
            Create(output_box),
            Write(output_label)
        )
        
        # Forward connections
        forward_arrows = []
        prev = input_box
        for layer in layers:
            arrow = Arrow(prev.get_right(), layer.get_left(), buff=0.1, color=WHITE)
            forward_arrows.append(arrow)
            prev = layer
        
        final_arrow = Arrow(layers[-1].get_right(), output_box.get_left(), buff=0.1, color=WHITE)
        forward_arrows.append(final_arrow)
        
        for arrow in forward_arrows:
            self.play(Create(arrow), run_time=0.3)
        
        self.wait(0.5)
        
        # Show skip connections (the key innovation)
        skip_title = Text("Skip Connections", font_size=20, color=YELLOW)
        skip_title.to_edge(UP).shift(DOWN * 0.8)
        self.play(FadeIn(skip_title))
        
        skip_arrows = []
        skip_labels = []
        
        # Skip from input to layer 2
        skip1_start = input_box.get_right()
        skip1_end = layers[1].get_left()
        skip1 = ArcBetweenPoints(skip1_start, skip1_end, angle=-PI/3, color=YELLOW, stroke_width=3)
        skip_arrows.append(skip1)
        
        skip1_label = Text("+", font_size=24, color=YELLOW)
        skip1_label.next_to(layers[1].get_left(), RIGHT + UP * 0.3, buff=0.1)
        skip_labels.append(skip1_label)
        
        # Skip from layer 1 to output
        skip2_start = layers[0].get_right()
        skip2_end = output_box.get_left()
        skip2 = ArcBetweenPoints(skip2_start, skip2_end, angle=-PI/4, color=YELLOW, stroke_width=3)
        skip_arrows.append(skip2)
        
        self.play(
            Create(skip1),
            Create(skip2),
            run_time=0.8
        )
        self.play(FadeIn(skip1_label))
        
        self.wait(0.5)
        
        # Now show backward gradient flow
        grad_title = Text("← Gradient Flow", font_size=20, color=RED)
        grad_title.to_edge(DOWN).shift(UP * 0.5)
        self.play(FadeIn(grad_title))
        
        # Gradient arrows going backward
        gradient_arrows = []
        
        # Through layers (faded/vanished)
        for arrow in reversed(forward_arrows):
            grad_arrow = arrow.copy()
            grad_arrow.set_color(RED_E)
            grad_arrow.set_opacity(0.3)
            gradient_arrows.append(grad_arrow)
        
        self.play(*[GrowArrow(arr) for arr in gradient_arrows], run_time=1)
        
        # Strong gradients through skip connections
        skip_grad1 = skip1.copy()
        skip_grad1.set_color(RED)
        skip_grad1.set_stroke(width=6)
        
        skip_grad2 = skip2.copy()
        skip_grad2.set_color(RED)
        skip_grad2.set_stroke(width=6)
        
        # Animate gradient flowing through skips
        self.play(
            Create(skip_grad1),
            Create(skip_grad2),
            run_time=1
        )
        
        # Highlight the flow
        flow_label = Text("Direct gradient path!", font_size=18, color=RED)
        flow_label.next_to(skip_grad1, UP, buff=0.3)
        self.play(Write(flow_label))
        
        self.wait(1)
        
        # Final comparison text
        conclusion = VGroup(
            Text("Without skips: Gradients vanish through many layers", font_size=16, color=RED_E),
            Text("With skips: Gradients flow directly → No vanishing gradient!", font_size=16, color=GREEN)
        ).arrange(DOWN, buff=0.3)
        conclusion.to_edge(DOWN).shift(UP * 1.2)
        
        self.play(
            FadeOut(grad_title),
            *[FadeOut(arr) for arr in gradient_arrows],
            FadeOut(flow_label)
        )
        
        self.play(Write(conclusion))
        
        self.wait(2)

