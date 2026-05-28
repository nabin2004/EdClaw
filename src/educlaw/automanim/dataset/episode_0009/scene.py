from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Configuration
        np.random.seed(42)
        
        # Colors
        NODE_INPUT = BLUE_C
        NODE_HIDDEN = GREEN_C
        NODE_OUTPUT = PURPLE_C
        EDGE_FF = GRAY
        EDGE_BP = RED_C
        DELTA_COLOR = YELLOW
        
        # Neural network architecture: 2-3-2
        input_pos = [LEFT * 4 + UP * 1.5, LEFT * 4 + DOWN * 1.5]
        hidden_pos = [LEFT * 1.5 + UP * 2, LEFT * 1.5, LEFT * 1.5 + DOWN * 2]
        output_pos = [RIGHT * 1 + UP * 1, RIGHT * 1 + DOWN * 1]
        
        # Create nodes
        input_nodes = VGroup(*[
            Circle(radius=0.3, color=NODE_INPUT, fill_opacity=0.3).move_to(pos)
            for pos in input_pos
        ])
        
        hidden_nodes = VGroup(*[
            Circle(radius=0.3, color=NODE_HIDDEN, fill_opacity=0.3).move_to(pos)
            for pos in hidden_pos
        ])
        
        output_nodes = VGroup(*[
            Circle(radius=0.3, color=NODE_OUTPUT, fill_opacity=0.3).move_to(pos)
            for pos in output_pos
        ])
        
        # Labels for layers
        input_label = Text("Input", font_size=24).next_to(input_nodes, LEFT)
        hidden_label = Text("Hidden", font_size=24).next_to(hidden_nodes, LEFT)
        output_label = Text("Output", font_size=24).next_to(output_nodes, RIGHT)
        
        # Create edges (forward)
        ff_edges = VGroup()
        for i_node in input_nodes:
            for h_node in hidden_nodes:
                edge = Line(i_node.get_right(), h_node.get_left(), color=EDGE_FF, stroke_width=2)
                ff_edges.add(edge)
        
        for h_node in hidden_nodes:
            for o_node in output_nodes:
                edge = Line(h_node.get_right(), o_node.get_left(), color=EDGE_FF, stroke_width=2)
                ff_edges.add(edge)
        
        # Title
        title = Text("Backpropagation: Gradient Flow", font_size=32).to_edge(UP)
        
        # Animation start
        self.play(Write(title))
        self.play(
            Create(input_nodes),
            Create(hidden_nodes),
            Create(output_nodes),
            run_time=1
        )
        self.play(
            Write(input_label),
            Write(hidden_label),
            Write(output_label),
            Create(ff_edges),
            run_time=1
        )
        self.wait(0.5)
        
        # Show forward pass briefly
        ff_arrows = VGroup()
        for edge in ff_edges:
            arrow = Arrow(edge.get_start(), edge.get_end(), buff=0.3, color=BLUE, stroke_width=2)
            ff_arrows.add(arrow)
        
        self.play(FadeIn(ff_arrows), run_time=0.5)
        self.play(FadeOut(ff_arrows), run_time=0.3)
        
        # === BACKPROPAGATION PHASE ===
        bp_title = Text("← Backward Pass (Gradients)", font_size=28, color=RED_C).to_edge(DOWN)
        self.play(Write(bp_title))
        
        # Delta values at output layer
        output_deltas = [0.15, -0.08]
        delta_output_mobjects = VGroup()
        
        for i, (node, delta) in enumerate(zip(output_nodes, output_deltas)):
            delta_text = MathTex(f"\\delta_{{{i+1}}}^{{(L)}} = {delta}", font_size=20, color=DELTA_COLOR)
            delta_text.next_to(node, RIGHT * 0.5 + UP * 0.8)
            delta_output_mobjects.add(delta_text)
        
        self.play(FadeIn(delta_output_mobjects), run_time=0.8)
        self.wait(0.3)
        
        # Gradient arrows from output to hidden
        bp_edges_output = VGroup()
        delta_hidden_vals = []
        
        for h_idx, h_node in enumerate(hidden_nodes):
            delta_sum = 0
            for o_idx, o_node in enumerate(output_nodes):
                w = np.random.uniform(0.3, 0.7)
                grad = output_deltas[o_idx] * w
                delta_sum += grad
                
                # Backward arrow
                arrow = Arrow(o_node.get_left(), h_node.get_right(), buff=0.35, 
                            color=EDGE_BP, stroke_width=3)
                bp_edges_output.add(arrow)
            delta_hidden_vals.append(round(delta_sum, 3))
        
        self.play(Create(bp_edges_output), run_time=1)
        
        # Show delta values at hidden layer
        delta_hidden_mobjects = VGroup()
        for i, (node, delta) in enumerate(zip(hidden_nodes, delta_hidden_vals)):
            delta_text = MathTex(f"\\delta_{{{i+1}}}^{{(H)}} = {delta}", font_size=20, color=DELTA_COLOR)
            delta_text.next_to(node, UP * 0.8)
            delta_hidden_mobjects.add(delta_text)
        
        self.play(FadeIn(delta_hidden_mobjects), run_time=0.8)
        self.wait(0.3)
        
        # Gradient arrows from hidden to input
        bp_edges_hidden = VGroup()
        delta_input_vals = []
        
        for i_idx, i_node in enumerate(input_nodes):
            delta_sum = 0
            for h_idx, h_node in enumerate(hidden_nodes):
                w = np.random.uniform(0.2, 0.6)
                grad = delta_hidden_vals[h_idx] * w
                delta_sum += grad
                
                arrow = Arrow(h_node.get_left(), i_node.get_right(), buff=0.35,
                            color=EDGE_BP, stroke_width=3)
                bp_edges_hidden.add(arrow)
            delta_input_vals.append(round(delta_sum, 3))
        
        self.play(Create(bp_edges_hidden), run_time=1)
        
        # Show delta values at input layer
        delta_input_mobjects = VGroup()
        for i, (node, delta) in enumerate(zip(input_nodes, delta_input_vals)):
            delta_text = MathTex(f"\\delta_{{{i+1}}}^{{(I)}} = {delta}", font_size=20, color=DELTA_COLOR)
            delta_text.next_to(node, LEFT * 0.5 + UP * 0.8)
            delta_input_mobjects.add(delta_text)
        
        self.play(FadeIn(delta_input_mobjects), run_time=0.8)
        self.wait(0.5)
        
        # Summary equation
        chain_rule = MathTex(
            "\\frac{\\partial L}{\\partial w} = ",
            "\\delta^{(l)} ",
            "\\cdot ",
            "a^{(l-1)}",
            font_size=28
        ).to_edge(DOWN * 3)
        chain_rule[1].set_color(RED_C)
        chain_rule[3].set_color(BLUE_C)
        
        self.play(
            FadeOut(bp_title),
            Write(chain_rule),
            run_time=0.8
        )
        
        # Highlight that deltas flow backward
        highlight_box = SurroundingRectangle(delta_output_mobjects, color=YELLOW, buff=0.2)
        self.play(Create(highlight_box), run_time=0.5)
        self.play(highlight_box.animate.move_to(delta_hidden_mobjects), run_time=0.5)
        self.play(highlight_box.animate.move_to(delta_input_mobjects), run_time=0.5)
        self.play(FadeOut(highlight_box), run_time=0.3)
        
        self.wait(1)
        
        # Cleanup
        self.play(
            FadeOut(title),
            FadeOut(input_nodes),
            FadeOut(hidden_nodes),
            FadeOut(output_nodes),
            FadeOut(input_label),
            FadeOut(hidden_label),
            FadeOut(output_label),
            FadeOut(ff_edges),
            FadeOut(bp_edges_output),
            FadeOut(bp_edges_hidden),
            FadeOut(delta_output_mobjects),
            FadeOut(delta_hidden_mobjects),
            FadeOut(delta_input_mobjects),
            FadeOut(chain_rule),
            run_time=1
        )
        
        self.wait(0.5)
