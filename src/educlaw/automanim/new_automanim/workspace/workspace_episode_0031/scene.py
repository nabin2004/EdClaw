"""
Transformer Positional Encoding Animation
Shows how sinusoidal signals are added to token embeddings.
"""

from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Configure scene settings
        self.camera.background_color = "#1a1a2e"
        
        # ============================================
        # PART 1: Title (0-2s)
        # ============================================
        title = Text(
            "Transformer Positional Encoding",
            font_size=40,
            color="#FFFFFF"
        ).to_edge(UP, buff=0.5)
        
        self.play(FadeIn(title))
        self.wait(0.5)
        
        # ============================================
        # PART 2: Input Tokens & Embeddings (2-6s)
        # ============================================
        tokens = VGroup(
            Text("The", font_size=24, color="#4ECDC4"),
            Text("cat", font_size=24, color="#4ECDC4"),
            Text("sat", font_size=24, color="#4ECDC4"),
        ).arrange(RIGHT, buff=1.5).shift(UP * 0.3)
        
        token_labels = VGroup(
            MathTex(r"x_0", font_size=24, color="#4ECDC4"),
            MathTex(r"x_1", font_size=24, color="#4ECDC4"),
            MathTex(r"x_2", font_size=24, color="#4ECDC4"),
        )
        
        for i, (token, label) in enumerate(zip(tokens, token_labels)):
            label.next_to(token, DOWN, buff=0.3)
        
        self.play(FadeIn(tokens), run_time=0.5)
        self.play(FadeIn(token_labels), run_time=0.5)
        self.wait(0.5)
        
        # Embedding vectors
        def create_embedding(dims, color, height=2.5):
            rects = VGroup()
            rect_height = height / dims
            for i in range(dims):
                intensity = 0.3 + 0.7 * (i % 2)
                rect = Rectangle(
                    width=0.7,
                    height=rect_height - 0.02,
                    fill_opacity=0.8,
                    fill_color=color,
                    stroke_width=1,
                    stroke_color="#FFFFFF"
                )
                rects.add(rect)
            rects.arrange(DOWN, buff=0.02)
            return rects
        
        dims = 6
        embeddings = VGroup(
            create_embedding(dims, "#4ECDC4"),
            create_embedding(dims, "#4ECDC4"),
            create_embedding(dims, "#4ECDC4"),
        )
        
        for i, (emb, token) in enumerate(zip(embeddings, tokens)):
            emb.next_to(token, DOWN, buff=0.8)
        
        self.play(FadeIn(embeddings), run_time=0.8)
        self.wait(0.7)
        
        # ============================================
        # PART 3: Formula & Positional Encodings (6-12s)
        # ============================================
        formula = VGroup(
            MathTex(r"PE_{(pos,2i)} = \sin(\frac{pos}{10000^{2i/d}})", font_size=18, color="#FF6B6B"),
            MathTex(r"PE_{(pos,2i+1)} = \cos(\frac{pos}{10000^{2i/d}})", font_size=18, color="#FF6B6B"),
        ).arrange(DOWN, buff=0.15).to_edge(LEFT, buff=0.3).shift(DOWN * 2.2)
        
        self.play(Write(formula), run_time=1)
        
        # Positional encoding vectors (to the right of embeddings)
        pos_encodings = VGroup(
            create_embedding(dims, "#FFE66D"),
            create_embedding(dims, "#FFE66D"),
            create_embedding(dims, "#FFE66D"),
        )
        
        for i, (pe, emb) in enumerate(zip(pos_encodings, embeddings)):
            pe.next_to(emb, RIGHT, buff=0.6)
        
        plus_signs = VGroup(*[
            MathTex(r"+", font_size=32, color="#FFFFFF").move_to(
                (emb.get_right() + pe.get_left()) / 2
            ) for emb, pe in zip(embeddings, pos_encodings)
        ])
        
        self.play(
            FadeIn(pos_encodings),
            FadeIn(plus_signs),
            run_time=1
        )
        self.wait(1)
        
        # ============================================
        # PART 4: Sinusoidal Waves (12-16s)
        # ============================================
        axes = Axes(
            x_range=[0, 3, 1],
            y_range=[-1.2, 1.2, 0.5],
            x_length=3,
            y_length=1.2,
            axis_config={"color": "#888888", "stroke_width": 1, "include_tip": False}
        ).to_edge(RIGHT, buff=0.3).shift(DOWN * 2.2)
        
        wave_colors = ["#FFE66D", "#FF6B6B", "#4ECDC4"]
        waves = VGroup()
        for j, color in enumerate(wave_colors):
            wave = axes.plot(
                lambda x, j=j: np.sin(2 * np.pi * (0.5 + j * 0.3) * x + j * 0.5),
                x_range=[0, 3],
                color=color,
                stroke_width=2
            )
            waves.add(wave)
        
        wave_label = Text("Sinusoidal by position", font_size=14, color="#FFE66D").next_to(axes, UP, buff=0.2)
        
        self.play(FadeIn(axes), FadeIn(wave_label), run_time=0.3)
        self.play(*[Create(w) for w in waves], run_time=1)
        self.wait(0.7)
        
        # ============================================
        # PART 5: Addition & Final Result (16-22s)
        # ============================================
        final_embeddings = VGroup(
            create_embedding(dims, "#96CEB4"),
            create_embedding(dims, "#96CEB4"),
            create_embedding(dims, "#96CEB4"),
        )
        
        equal_signs = VGroup()
        for i, (pe, final) in enumerate(zip(pos_encodings, final_embeddings)):
            eq = MathTex(r"=", font_size=32, color="#FFFFFF")
            eq.next_to(pe, RIGHT, buff=0.4)
            equal_signs.add(eq)
            final.next_to(eq, RIGHT, buff=0.4)
        
        self.play(FadeIn(equal_signs), run_time=0.3)
        
        # Animate the blending
        for emb, pe, final in zip(embeddings, pos_encodings, final_embeddings):
            src_emb = emb.copy()
            src_pe = pe.copy()
            self.play(
                src_emb.animate.move_to(final.get_center()).set_opacity(0.4),
                src_pe.animate.move_to(final.get_center()).set_opacity(0.4),
                FadeIn(final),
                run_time=0.25
            )
            self.remove(src_emb, src_pe)
        
        self.wait(0.5)
        
        # ============================================
        # PART 6: Summary (22-26s)
        # ============================================
        all_others = [tokens, token_labels, embeddings, pos_encodings, 
                      plus_signs, equal_signs, final_embeddings, formula,
                      axes, waves, wave_label]
        
        summary = Text(
            "Position-aware token representations",
            font_size=28,
            color="#96CEB4"
        ).move_to(ORIGIN).shift(DOWN * 0.5)
        
        summary2 = Text(
            "Unique sinusoidal pattern per position",
            font_size=22,
            color="#FFE66D"
        ).next_to(summary, DOWN, buff=0.3)
        
        self.play(
            FadeOut(VGroup(*all_others)),
            FadeIn(summary),
            run_time=0.8
        )
        self.play(FadeIn(summary2), run_time=0.4)
        self.wait(1.8)

        self.play(FadeOut(title), FadeOut(summary), FadeOut(summary2), run_time=0.3)
