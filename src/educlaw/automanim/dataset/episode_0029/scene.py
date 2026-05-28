from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Label Smoothing", font_size=48, color=BLUE)
        subtitle = Text("Converting One-Hot to Soft Targets", font_size=24, color=GRAY)
        subtitle.next_to(title, DOWN, buff=0.3)
        
        self.play(Write(title), run_time=0.8)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.wait(0.5)
        self.play(FadeOut(title), FadeOut(subtitle), run_time=0.3)
        
        # Setup parameters
        num_classes = 5
        epsilon = 0.1
        true_class = 2  # 0-indexed
        
        # One-hot vector representation
        one_hot_values = [0] * num_classes
        one_hot_values[true_class] = 1.0
        
        # Smoothed vector
        smooth_values = [(1 - epsilon) * (1 if i == true_class else 0) + epsilon / num_classes 
                        for i in range(num_classes)]
        
        # Create bar charts
        bar_height = 0.6
        bar_spacing = 0.8
        bar_width = 0.5
        x_range = list(range(num_classes))
        
        # One-hot chart
        one_hot_bars = VGroup()
        one_hot_labels = VGroup()
        one_hot_title = Text("One-Hot Target", font_size=28, color=YELLOW).to_edge(UP, buff=1)
        
        for i, val in enumerate(one_hot_values):
            height = bar_height * val * 4
            bar = Rectangle(
                width=bar_width, 
                height=max(height, 0.01),
                fill_color=YELLOW if i == true_class else GRAY,
                fill_opacity=0.8,
                stroke_color=WHITE
            )
            bar.move_to([i * bar_spacing - (num_classes - 1) * bar_spacing / 2, height / 2, 0])
            one_hot_bars.add(bar)
            
            label = Text(f"{val:.1f}", font_size=20).next_to(bar, UP, buff=0.1)
            one_hot_labels.add(label)
            
            class_label = Text(str(i), font_size=16).next_to(bar, DOWN, buff=0.15)
            one_hot_labels.add(class_label)
        
        # Formula explanation
        formula = MathTex(
            r"y_{\text{smooth}} = (1 - \epsilon) \cdot y_{\text{hot}} + \frac{\epsilon}{K}",
            font_size=32
        ).to_edge(UP, buff=0.5)
        
        param_text = MathTex(r"\epsilon = 0.1,\ K = 5", font_size=24, color=GRAY).next_to(formula, DOWN, buff=0.2)
        
        # Show one-hot
        self.play(Write(one_hot_title), run_time=0.5)
        self.play(*[Create(bar) for bar in one_hot_bars], run_time=0.8)
        self.play(*[Write(label) for label in one_hot_labels], run_time=0.5)
        self.wait(0.5)
        
        # Show formula
        self.play(
            one_hot_title.animate.scale(0.8).to_edge(LEFT, buff=1),
            one_hot_bars.animate.scale(0.6).shift(DOWN + LEFT * 2.5),
            one_hot_labels.animate.scale(0.6).shift(DOWN + LEFT * 2.5),
            run_time=0.8
        )
        
        self.play(Write(formula), run_time=0.8)
        self.play(Write(param_text), run_time=0.5)
        self.wait(0.5)
        
        # Calculate steps
        steps_group = VGroup()
        
        calc1 = MathTex(r"y_{\text{smooth}} = 0.9 \cdot y_{\text{hot}} + 0.02", font_size=24, color=BLUE)
        calc1.next_to(param_text, DOWN, buff=0.3)
        steps_group.add(calc1)
        
        calc2 = MathTex(r"= 0.9 \cdot [0,0,1,0,0] + 0.02 \cdot [1,1,1,1,1]", font_size=22, color=BLUE_A)
        calc2.next_to(calc1, DOWN, buff=0.15)
        steps_group.add(calc2)
        
        calc3 = MathTex(r"= [0.02, 0.02, \mathbf{0.92}, 0.02, 0.02]", font_size=22, color=GREEN_B)
        calc3.next_to(calc2, DOWN, buff=0.15)
        steps_group.add(calc3)
        
        self.play(Write(calc1), run_time=0.6)
        self.play(Write(calc2), run_time=0.6)
        self.play(Write(calc3), run_time=0.6)
        self.wait(0.5)
        
        # Transform to smoothed distribution
        smooth_title = Text("Label-Smoothed Target", font_size=28, color=GREEN).to_edge(RIGHT, buff=1)
        smooth_bars = VGroup()
        smooth_labels = VGroup()
        
        for i, val in enumerate(smooth_values):
            height = bar_height * val * 4
            bar = Rectangle(
                width=bar_width, 
                height=max(height, 0.01),
                fill_color=GREEN if i == true_class else TEAL,
                fill_opacity=0.8,
                stroke_color=WHITE
            )
            bar.move_to([i * bar_spacing - (num_classes - 1) * bar_spacing / 2, height / 2, 0])
            smooth_bars.add(bar)
            
            label = Text(f"{val:.2f}", font_size=18).next_to(bar, UP, buff=0.1)
            smooth_labels.add(label)
            
            class_label = Text(str(i), font_size=16).next_to(bar, DOWN, buff=0.15)
            smooth_labels.add(class_label)
        
        smooth_group = VGroup(smooth_bars, smooth_labels).scale(0.6).to_edge(RIGHT, buff=1.5).shift(DOWN * 0.5)
        
        self.play(Write(smooth_title), run_time=0.5)
        self.play(
            TransformFromCopy(one_hot_bars, smooth_bars),
            TransformFromCopy(one_hot_labels, smooth_labels),
            run_time=1.5
        )
        self.wait(0.5)
        
        # Highlight difference
        arrow = DoubleArrow(
            one_hot_bars.get_right(),
            smooth_bars.get_left(),
            color=WHITE,
            buff=0.3
        )
        smooth_text = Text("Smoothed", font_size=20, color=GREEN).next_to(arrow, UP, buff=0.1)
        
        self.play(Create(arrow), Write(smooth_text), run_time=0.6)
        self.wait(0.5)
        
        # Benefits
        benefit1 = Text("✓ Reduces overconfidence", font_size=20, color=BLUE)
        benefit2 = Text("✓ Better generalization", font_size=20, color=BLUE)
        benefit3 = Text("✓ Prevents hard targets", font_size=20, color=BLUE)
        
        benefits = VGroup(benefit1, benefit2, benefit3).arrange(DOWN, buff=0.2).next_to(formula, UP, buff=0.2)
        benefits.shift(RIGHT * 2)
        
        self.play(*[Write(b) for b in benefits], run_time=0.8)
        self.wait(1)
        
        # Final emphasis
        self.play(
            smooth_title.animate.scale(1.1).set_color(GREEN_E),
            smooth_bars.animate.scale(1.1),
            smooth_labels.animate.scale(1.1),
            run_time=0.6
        )
        self.wait(1)
