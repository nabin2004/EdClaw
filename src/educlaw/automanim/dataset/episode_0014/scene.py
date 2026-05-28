"""
Manim animation showing attention scores being computed between query and key vectors,
resulting in a weighted sum of values.
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Set up the scene with dark background
        self.camera.background_color = "#1a1a2e"
        
        # Title
        title = Text("Attention Mechanism", font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.5)
        
        subtitle = Text("Query-Key-Value Computation", font_size=20, color="#a0a0a0")
        subtitle.next_to(title, DOWN, buff=0.2)
        
        self.play(FadeIn(title), FadeIn(subtitle))
        self.wait(0.5)
        
        # Define dimensions
        dim = 4
        
        # Create Query vector
        q_values = [0.5, 0.8, 0.3, 0.6]
        q_matrix = Matrix([[f"{v:.1f}"] for v in q_values], v_buff=0.4)
        q_matrix.set_color("#ff6b6b")
        q_label = Text("Query", font_size=18, color="#ff6b6b")
        q_label.next_to(q_matrix, LEFT)
        q_group = VGroup(q_label, q_matrix)
        q_group.to_edge(LEFT, buff=1.5)
        
        # Create Key vectors (3 keys for demonstration)
        k_values = [
            [0.7, 0.2, 0.5, 0.4],
            [0.3, 0.9, 0.1, 0.8],
            [0.6, 0.4, 0.7, 0.3]
        ]
        k_matrices = []
        k_labels = []
        for i, kv in enumerate(k_values):
            k_matrix = Matrix([[f"{v:.1f}"] for v in kv], v_buff=0.4)
            k_matrix.set_color("#4ecdc4")
            k_label = Text(f"Key {i+1}", font_size=18, color="#4ecdc4")
            k_label.next_to(k_matrix, LEFT)
            k_group = VGroup(k_label, k_matrix)
            k_matrices.append(k_matrix)
            k_labels.append(k_label)
        
        # Stack Key vectors vertically
        keys_group = VGroup(*[VGroup(l, m) for l, m in zip(k_labels, k_matrices)])
        keys_group.arrange(DOWN, buff=0.4)
        keys_group.to_edge(RIGHT, buff=2)
        
        # Create Value vectors
        v_values = [
            [0.2, 0.5],
            [0.7, 0.3],
            [0.4, 0.8]
        ]
        v_matrices = []
        v_labels = []
        for i, vv in enumerate(v_values):
            v_matrix = Matrix([[f"{v:.1f}"] for v in vv], v_buff=0.4)
            v_matrix.set_color("#ffe66d")
            v_label = Text(f"Value {i+1}", font_size=18, color="#ffe66d")
            v_label.next_to(v_matrix, LEFT)
            v_group = VGroup(v_label, v_matrix)
            v_matrices.append(v_matrix)
            v_labels.append(v_label)
        
        # Position Value vectors below Keys
        values_group = VGroup(*[VGroup(l, m) for l, m in zip(v_labels, v_matrices)])
        values_group.arrange(DOWN, buff=0.4)
        values_group.next_to(keys_group, DOWN, buff=0.8)
        
        # Animate Query and Keys appearing
        self.play(
            FadeIn(q_group),
            FadeIn(keys_group),
            run_time=1.5
        )
        self.wait(0.3)
        
        # Step 1: Compute dot products (attention scores)
        dot_label = Text("Step 1: Dot Products", font_size=24, color=WHITE)
        dot_label.to_edge(DOWN, buff=1.2)
        self.play(FadeIn(dot_label))
        
        arrows = []
        score_texts = []
        score_vals = [1.19, 1.40, 1.02]  # Pre-computed dot products
        
        for i, (k_mat, k_label) in enumerate(zip(k_matrices, k_labels)):
            # Draw arrow from Query to Key
            arrow = Arrow(
                q_matrix.get_right() + RIGHT * 0.3,
                k_mat.get_left() + LEFT * 0.3,
                buff=0.1,
                color="#ff9f43",
                stroke_width=2
            )
            arrows.append(arrow)
            
            # Show dot product equation
            q_dot_k = MathTex(r"q", r"\cdot", f"k_{{{i+1}}}", font_size=20)
            q_dot_k[0].set_color("#ff6b6b")
            q_dot_k[2].set_color("#4ecdc4")
            q_dot_k.next_to(arrow, UP, buff=0.1)
            q_dot_k.set_color("#ff9f43")
            
            # Animate arrow and equation
            self.play(
                GrowArrow(arrow),
                FadeIn(q_dot_k),
                run_time=0.5
            )
            
            # Show the numeric score
            score_val = round(score_vals[i], 2)
            score_text = MathTex(f"= {score_val}", font_size=20, color="#ff9f43")
            score_text.next_to(q_dot_k, RIGHT)
            score_texts.append(score_text)
            
            self.play(FadeIn(score_text), run_time=0.3)
        
        self.wait(0.3)
        
        # Step 2: Softmax normalization
        self.play(FadeOut(dot_label))
        softmax_label = Text("Step 2: Softmax Normalization", font_size=24, color=WHITE)
        softmax_label.to_edge(DOWN, buff=1.2)
        self.play(FadeIn(softmax_label))
        
        # Create attention weight boxes
        weight_boxes = VGroup()
        weight_texts = []
        weight_vals = [0.31, 0.40, 0.29]  # Softmax of scores (approx)
        
        for i, (score, val) in enumerate(zip(score_texts, weight_vals)):
            # Box around attention score
            box = Rectangle(height=0.6, width=1.2, fill_opacity=0.3, fill_color="#9b59b6", color="#9b59b6")
            box.move_to(score.get_center())
            
            # Transform to attention weight
            attn_text = MathTex(f"\\alpha_{{{i+1}}}", f"= {val:.2f}", font_size=20)
            attn_text[0].set_color("#9b59b6")
            attn_text[1].set_color(WHITE)
            attn_text.move_to(box.get_center())
            
            weight_boxes.add(VGroup(box, attn_text))
            weight_texts.append(attn_text)
            
            self.play(
                TransformFromCopy(score_texts[i], VGroup(box, attn_text)),
                run_time=0.5
            )
        
        self.wait(0.3)
        
        # Step 3: Weighted sum of Values
        self.play(FadeOut(softmax_label))
        weight_label = Text("Step 3: Weighted Sum of Values", font_size=24, color=WHITE)
        weight_label.to_edge(DOWN, buff=1.2)
        
        # Show Values appearing
        self.play(
            FadeIn(weight_label),
            FadeIn(values_group),
            run_time=1
        )
        
        # Draw connections from attention weights to values
        value_arrows = []
        scaled_values = []
        
        for i, (weight, v_mat) in enumerate(zip(weight_texts, v_matrices)):
            # Arrow from weight to value
            start = weight_boxes[i].get_bottom()
            end = v_mat.get_top() + UP * 0.2
            arrow = Arrow(start, end, buff=0.1, color="#9b59b6", stroke_width=2)
            value_arrows.append(arrow)
            
            # Show scaling
            scale_text = MathTex(r"\times v_" + f"{{{i+1}}}", font_size=16, color="#ffe66d")
            scale_text.next_to(arrow, RIGHT, buff=0.05)
            scaled_values.append(scale_text)
            
            self.play(
                GrowArrow(arrow),
                FadeIn(scale_text),
                run_time=0.4
            )
        
        self.wait(0.3)
        
        # Compute final output
        output_label = Text("Output", font_size=18, color="#00d2ff")
        # Calculate weighted sum: 0.31*[0.2,0.5] + 0.40*[0.7,0.3] + 0.29*[0.4,0.8]
        out_vals = [
            0.31*0.2 + 0.40*0.7 + 0.29*0.4,  # ≈ 0.426
            0.31*0.5 + 0.40*0.3 + 0.29*0.8   # ≈ 0.487
        ]
        output_matrix = Matrix([[f"{v:.2f}"] for v in out_vals], v_buff=0.4)
        output_matrix.set_color("#00d2ff")
        output_label.next_to(output_matrix, RIGHT)
        output_group = VGroup(output_matrix, output_label)
        output_group.move_to(ORIGIN).shift(DOWN * 2)
        
        # Animate output appearing
        self.play(
            FadeOut(weight_label),
            run_time=0.3
        )
        
        output_title = Text("Attention Output", font_size=24, color="#00d2ff")
        output_title.to_edge(DOWN, buff=1.2)
        
        # Collect arrows to output
        collect_arrows = []
        for i, v_mat in enumerate(v_matrices):
            arrow = Arrow(
                v_mat.get_bottom() + DOWN * 0.1,
                output_matrix.get_top(),
                buff=0.3,
                color="#00d2ff",
                stroke_width=2
            )
            collect_arrows.append(arrow)
        
        self.play(
            *[GrowArrow(arrow) for arrow in collect_arrows],
            FadeIn(output_group),
            FadeIn(output_title),
            run_time=1
        )
        
        # Add equation annotation
        equation = MathTex(
            r"\text{Attention}(Q,K,V) = \sum_i \alpha_i v_i",
            font_size=20,
            color="#a0a0a0"
        )
        equation.next_to(output_group, DOWN, buff=0.4)
        self.play(FadeIn(equation), run_time=0.5)
        
        self.wait(0.5)
        
        # Final highlight
        self.play(
            Circumscribe(output_group, color="#00d2ff", buff=0.2),
            run_time=1
        )
        
        self.wait(1)
