from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Adam Optimizer", font_size=48)
        self.play(Create(title), run_time=1)
        self.wait(0.5)
        self.play(title.animate.to_edge(UP), run_time=0.8)
        
        # Parameters
        beta1 = 0.9
        beta2 = 0.999
        alpha = 0.1
        eps = 1e-8
        
        # Initial values
        m_val = 0.0
        v_val = 0.0
        w_val = 2.0
        
        # Create panels for m, v, and w
        m_title = MathTex(r"\text{First Moment } m_t", font_size=32, color=BLUE)
        v_title = MathTex(r"\text{Second Moment } v_t", font_size=32, color=GREEN)
        w_title = MathTex(r"\text{Weight } w_t", font_size=32, color=RED)
        
        m_display = MathTex(f"{m_val:.4f}", font_size=40, color=BLUE)
        v_display = MathTex(f"{v_val:.4f}", font_size=40, color=GREEN)
        w_display = MathTex(f"{w_val:.4f}", font_size=40, color=RED)
        
        m_group = VGroup(m_title, m_display).arrange(DOWN, buff=0.4)
        v_group = VGroup(v_title, v_display).arrange(DOWN, buff=0.4)
        w_group = VGroup(w_title, w_display).arrange(DOWN, buff=0.4)
        
        panels = VGroup(m_group, v_group, w_group).arrange(RIGHT, buff=2.0)
        panels.shift(DOWN * 0.3)
        
        # Boxes around panels
        m_box = SurroundingRectangle(m_group, color=BLUE, buff=0.3, corner_radius=0.1)
        v_box = SurroundingRectangle(v_group, color=GREEN, buff=0.3, corner_radius=0.1)
        w_box = SurroundingRectangle(w_group, color=RED, buff=0.3, corner_radius=0.1)
        
        self.play(
            Create(m_box), Create(v_box), Create(v_box),
            run_time=1.0
        )
        self.play(
            Write(m_title), Write(v_title), Write(w_title),
            run_time=0.8
        )
        self.play(
            Write(m_display), Write(v_display), Write(w_display),
            run_time=0.8
        )
        self.wait(0.3)
        
        # Show update equations
        eq_m = MathTex(r"m_t = \beta_1 m_{t-1} + (1-\beta_1) g_t", font_size=26)
        eq_v = MathTex(r"v_t = \beta_2 v_{t-1} + (1-\beta_2) g_t^2", font_size=26)
        eq_w = MathTex(r"w_t = w_{t-1} - \alpha \frac{m_t}{\sqrt{v_t} + \epsilon}", font_size=26)
        
        eq_group = VGroup(eq_m, eq_v, eq_w).arrange(DOWN, buff=0.3).scale(0.8)
        eq_group.to_edge(DOWN, buff=0.4)
        
        self.play(Write(eq_group), run_time=1.2)
        self.wait(0.5)
        
        # Simulate 3 gradient steps
        gradients = [0.8, 0.5, 0.3]
        
        for t, g in enumerate(gradients, 1):
            # Show gradient
            grad_label = MathTex(rf"g_{{{t}}} = {g:.1f}", font_size=30, color=YELLOW)
            grad_label.next_to(panels, DOWN, buff=0.8)
            self.play(Write(grad_label), run_time=0.4)
            
            # Calculate new values
            new_m = beta1 * m_val + (1 - beta1) * g
            new_v = beta2 * v_val + (1 - beta2) * (g ** 2)
            
            # Bias correction
            m_hat = new_m / (1 - beta1 ** t)
            v_hat = new_v / (1 - beta2 ** t)
            
            new_w = w_val - alpha * m_hat / (np.sqrt(v_hat) + eps)
            
            # Create new displays
            new_m_display = MathTex(f"{new_m:.4f}", font_size=40, color=BLUE)
            new_v_display = MathTex(f"{new_v:.4f}", font_size=40, color=GREEN)
            new_w_display = MathTex(f"{new_w:.4f}", font_size=40, color=RED)
            
            new_m_display.move_to(m_display.get_center())
            new_v_display.move_to(v_display.get_center())
            new_w_display.move_to(w_display.get_center())
            
            # Animate updates
            self.play(
                Transform(m_display, new_m_display),
                Transform(v_display, new_v_display),
                Transform(w_display, new_w_display),
                run_time=1.2
            )
            
            # Remove and recreate for next iteration
            self.remove(m_display, v_display, w_display)
            m_display = new_m_display
            v_display = new_v_display
            w_display = new_w_display
            self.add(m_display, v_display, w_display)
            
            self.play(FadeOut(grad_label), run_time=0.3)
            
            m_val, v_val, w_val = new_m, new_v, new_w
            self.wait(0.2)
        
        # Final flourish
        self.play(
            Indicate(m_display),
            Indicate(v_display),
            Indicate(w_display),
            run_time=0.8
        )
        self.wait(0.5)
