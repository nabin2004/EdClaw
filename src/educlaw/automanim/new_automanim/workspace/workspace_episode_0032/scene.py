from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        self.camera.background_color = "#1a1a2e"
        
        # Title
        title = Text("Multi-Head Attention", font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.5)
        
        subtitle = Text("Split → Compute → Concatenate", font_size=22, color="#a0a0a0")
        subtitle.next_to(title, DOWN, buff=0.2)
        
        self.play(Write(title), run_time=0.8)
        self.play(Write(subtitle), run_time=0.6)
        self.wait(0.3)
        
        # Create Q, K, V matrices as rectangles
        q_rect = RoundedRectangle(height=2, width=0.8, corner_radius=0.1, fill_color=BLUE, fill_opacity=0.7, stroke_color=BLUE_B, stroke_width=2)
        k_rect = RoundedRectangle(height=2, width=0.8, corner_radius=0.1, fill_color=GREEN, fill_opacity=0.7, stroke_color=GREEN_B, stroke_width=2)
        v_rect = RoundedRectangle(height=2, width=0.8, corner_radius=0.1, fill_color=RED, fill_opacity=0.7, stroke_color=RED_B, stroke_width=2)
        
        q_rect.move_to(LEFT * 4.5)
        k_rect.move_to(LEFT * 2.5)
        v_rect.move_to(LEFT * 0.5)
        
        q_label = Text("Q", font_size=28, color=WHITE).move_to(q_rect.get_center())
        k_label = Text("K", font_size=28, color=WHITE).move_to(k_rect.get_center())
        v_label = Text("V", font_size=28, color=WHITE).move_to(v_rect.get_center())
        
        q_group = VGroup(q_rect, q_label)
        k_group = VGroup(k_rect, k_label)
        v_group = VGroup(v_rect, v_label)
        
        input_group = VGroup(q_group, k_group, v_group)
        
        self.play(
            FadeIn(q_rect, shift=DOWN*0.5),
            FadeIn(k_rect, shift=DOWN*0.5),
            FadeIn(v_rect, shift=DOWN*0.5),
            Write(q_label),
            Write(k_label),
            Write(v_label),
            run_time=0.8
        )
        self.wait(0.3)
        
        # Arrow to split
        split_arrow = Arrow(UP, DOWN, color="#f39c12", stroke_width=3)
        split_label = Text("Split into Heads", font_size=20, color="#f39c12")
        split_group = VGroup(split_arrow, split_label)
        split_group.arrange(DOWN, buff=0.2)
        split_group.move_to(DOWN * 1.5)
        
        self.play(
            GrowArrow(split_arrow),
            Write(split_label),
            run_time=0.6
        )
        self.wait(0.2)
        
        # Create 4 heads with smaller Q, K, V chunks
        num_heads = 4
        head_height = 0.4
        head_width = 0.5
        head_spacing = 0.15
        
        heads_group = VGroup()
        all_q_heads = []
        all_k_heads = []
        all_v_heads = []
        
        head_colors = ["#3498db", "#9b59b6", "#e74c3c", "#f1c40f"]
        
        for i in range(num_heads):
            y_offset = 1.5 - i * (head_height + head_spacing)
            
            # Q head
            q_head = RoundedRectangle(
                height=head_height, width=head_width, corner_radius=0.05,
                fill_color=head_colors[i], fill_opacity=0.8,
                stroke_color=WHITE, stroke_width=1
            )
            q_head.move_to(LEFT * 4 + DOWN * y_offset + LEFT * 1.2)
            
            # K head
            k_head = RoundedRectangle(
                height=head_height, width=head_width, corner_radius=0.05,
                fill_color=head_colors[i], fill_opacity=0.8,
                stroke_color=WHITE, stroke_width=1
            )
            k_head.move_to(LEFT * 4 + DOWN * y_offset + LEFT * 0.2)
            
            # V head
            v_head = RoundedRectangle(
                height=head_height, width=head_width, corner_radius=0.05,
                fill_color=head_colors[i], fill_opacity=0.8,
                stroke_color=WHITE, stroke_width=1
            )
            v_head.move_to(LEFT * 4 + DOWN * y_offset + RIGHT * 0.8)
            
            head_label = Text(f"H{i+1}", font_size=14, color=WHITE)
            head_label.next_to(q_head, LEFT, buff=0.1)
            
            head_group = VGroup(q_head, k_head, v_head, head_label)
            heads_group.add(head_group)
            all_q_heads.append(q_head)
            all_k_heads.append(k_head)
            all_v_heads.append(v_head)
        
        # Animate splitting
        self.play(
            *[TransformFromCopy(q_rect, qh) for qh in all_q_heads],
            *[TransformFromCopy(k_rect, kh) for kh in all_k_heads],
            *[TransformFromCopy(v_rect, vh) for vh in all_v_heads],
            *[Write(heads_group[i][3]) for i in range(num_heads)],
            FadeOut(q_group, k_group, v_group),
            run_time=1.2
        )
        self.wait(0.3)
        
        # Attention computation for each head
        attention_outputs = []
        for i in range(num_heads):
            head_group = heads_group[i]
            q_h, k_h, v_h = head_group[0], head_group[1], head_group[2]
            
            # Show attention flow
            attn_flow = Arrow(q_h.get_right(), k_h.get_left(), buff=0.05, color="#f39c12", stroke_width=1.5)
            attn_flow2 = Arrow(k_h.get_right(), v_h.get_left(), buff=0.05, color="#f39c12", stroke_width=1.5)
            
            self.play(
                Create(attn_flow),
                Create(attn_flow2),
                run_time=0.15
            )
            
            # Output block
            out_block = RoundedRectangle(
                height=head_height, width=head_width, corner_radius=0.05,
                fill_color=head_colors[i], fill_opacity=0.9,
                stroke_color=WHITE, stroke_width=1.5
            )
            out_block.move_to(v_h.get_center() + RIGHT * 1.2)
            out_label = Text(f"O{i+1}", font_size=14, color=WHITE)
            out_label.move_to(out_block.get_center())
            
            arrow_to_out = Arrow(v_h.get_right(), out_block.get_left(), buff=0.05, color="#2ecc71", stroke_width=1.5)
            
            self.play(
                FadeIn(out_block),
                Write(out_label),
                Create(arrow_to_out),
                run_time=0.15
            )
            
            attention_outputs.append(VGroup(out_block, out_label))
            
            self.play(
                FadeOut(attn_flow, attn_flow2, arrow_to_out),
                run_time=0.1
            )
        
        self.wait(0.3)
        
        # Concatenate arrow
        concat_arrow = Arrow(UP, DOWN, color="#e74c3c", stroke_width=3)
        concat_label = Text("Concatenate", font_size=20, color="#e74c3c")
        concat_group = VGroup(concat_arrow, concat_label)
        concat_group.arrange(DOWN, buff=0.2)
        concat_group.move_to(RIGHT * 3.5 + DOWN * 0.5)
        
        self.play(
            heads_group.animate.set_opacity(0.3),
            *[out.animate.set_opacity(0.5) for out in attention_outputs],
            GrowArrow(concat_arrow),
            Write(concat_label),
            run_time=0.7
        )
        
        # Final output - concatenated
        final_output = RoundedRectangle(
            height=2, width=0.8, corner_radius=0.1,
            fill_color="#9b59b6", fill_opacity=0.8,
            stroke_color="#8e44ad", stroke_width=2
        )
        final_output.move_to(RIGHT * 5)
        final_label = Text("Out", font_size=28, color=WHITE)
        final_label.move_to(final_output.get_center())
        
        # Arrows from outputs to final
        concat_arrows = []
        for i, out in enumerate(attention_outputs):
            arrow = Arrow(out.get_right(), final_output.get_left(), buff=0.3, color="#9b59b6", stroke_width=2)
            concat_arrows.append(arrow)
        
        self.play(
            *[GrowArrow(arr) for arr in concat_arrows],
            run_time=0.5
        )
        
        self.play(
            FadeIn(final_output),
            Write(final_label),
            run_time=0.6
        )
        
        self.wait(0.3)
        
        # Highlight each part contributing to output
        for i, out in enumerate(attention_outputs):
            self.play(
                out.animate.set_opacity(1).scale(1.1),
                run_time=0.15
            )
            self.play(
                out.animate.set_opacity(0.5).scale(1/1.1),
                run_time=0.1
            )
        
        # Final pulse on output
        self.play(
            final_output.animate.scale(1.1),
            run_time=0.2
        )
        self.play(
            final_output.animate.scale(1/1.1),
            run_time=0.2
        )
        
        self.wait(0.5)
        
        # Fade out all except title and final output with formula
        formula = MathTex(r"\\text{MultiHead}(Q,K,V) = \\text{Concat}(head_1, \\ldots, head_h)W^O", font_size=26)
        formula.set_color(WHITE)
        formula.next_to(final_output, DOWN, buff=0.8)
        
        self.play(
            FadeOut(heads_group),
            *[FadeOut(out) for out in attention_outputs],
            *[FadeOut(arr) for arr in concat_arrows],
            FadeOut(concat_arrow, concat_label, split_arrow, split_label),
            FadeOut(subtitle),
            Write(formula),
            run_time=0.8
        )
        
        # Surround final output and formula
        highlight = SurroundingRectangle(VGroup(final_output, final_label), color="#f1c40f", buff=0.2)
        
        self.play(
            Create(highlight),
            run_time=0.5
        )
        
        self.wait(0.5)
        
        self.play(
            FadeOut(highlight),
            FadeOut(title),
            FadeOut(final_output),
            FadeOut(final_label),
            FadeOut(formula),
            run_time=0.5
        )
