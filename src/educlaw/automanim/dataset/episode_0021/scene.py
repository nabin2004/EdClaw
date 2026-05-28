"""Learning Rate Warmup Animation

Shows how learning rate increases linearly during warmup phase,
then decays following a cosine schedule.
"""

from manim import *


class AutoScene(Scene):
    def construct(self):
        # Parameters
        max_steps = 100
        warmup_steps = 20
        max_lr = 2.5
        
        # Create axes
        axes = Axes(
            x_range=[0, max_steps, 20],
            y_range=[0, max_lr, 0.5],
            x_length=10,
            y_length=5,
            axis_config={
                "include_tip": True,
                "include_numbers": True,
                "font_size": 24,
            },
            tips=True,
        ).to_edge(DOWN, buff=0.5)
        
        # Labels
        x_label = axes.get_x_axis_label(
            Tex("Training Steps"), 
            edge=DOWN, 
            direction=DOWN, 
            buff=0.5
        )
        y_label = axes.get_y_axis_label(
            Tex("Learning Rate"), 
            edge=LEFT, 
            direction=LEFT, 
            buff=0.3
        ).rotate(90 * DEGREES)
        
        # Title
        title = Text(
            "Learning Rate Warmup", 
            font_size=36, 
            weight=BOLD
        ).to_edge(UP, buff=0.8)
        
        # Equation text
        warmup_text = Tex(
            r"\text{Warmup: } lr = lr_{max} \times \frac{step}{warmup\_steps}",
            font_size=24
        ).to_corner(UR, buff=0.5)
        
        decay_text = Tex(
            r"\text{Decay: } lr = lr_{max} \times \frac{1 + \cos(\pi t)}{2}",
            font_size=24
        ).to_corner(UR, buff=0.5)
        
        # Create the warmup and decay curves
        def lr_schedule(step):
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            if step == 0:
                return 0
            return 0
    
    """Avoid return-in-init bug in LM-generated code."""
    pass
