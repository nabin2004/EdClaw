"""
SGD Weight Updates Animation
Shows gradient descent steps on a loss surface with arrows.
"""

from manim import *


class AutoScene(ThreeDScene):
    def construct(self):
        # Setup camera
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)
        
        # Create loss surface: z = x^2 + y^2 (bowl shape)
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[0, 18, 2],
            x_length=6,
            y_length=6,
            z_length=4,
        )
        
        # Labels
        x_label = MathTex("w_1").next_to(axes.x_axis, RIGHT)
        y_label = MathTex("w_2").next_to(axes.y_axis, UP)
        z_label = MathTex("L").next_to(axes.z_axis, UP)
        
        labels = VGroup(x_label, y_label, z_label)
        
        # Loss surface
        surface = Surface(
            lambda u, v: axes.c2p(u, v, u**2 + v**2),
            u_range=[-2.5, 2.5],
            v_range=[-2.5, 2.5],
            resolution=[30, 30],
        )
        surface.set_style(fill_opacity=0.6, stroke_width=0.5)
        surface.set_color_by_gradient(BLUE, GREEN, YELLOW)
        
        # Title - fixed in frame using add_fixed_in_frame_mobjects
        title = Text("Stochastic Gradient Descent", font_size=36)
        title.to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)
        
        # Show setup
        self.play(Create(axes), Create(labels))
        self.play(FadeIn(surface))
        self.play(Write(title))
        self.wait(0.5)
        
        # SGD steps starting from (-2, 2)
        learning_rate = 0.3
        current_pos = np.array([-2.0, 2.0])
        
        # Gradient of L = x^2 + y^2 is [2x, 2y]
        steps_data = []
        for i in range(6):
            grad = np.array([2 * current_pos[0], 2 * current_pos[1]])
            new_pos = current_pos - learning_rate * grad
            steps_data.append({
                'from': current_pos.copy(),
                'to': new_pos.copy(),
                'grad': grad.copy()
            })
            current_pos = new_pos
        
        # Animate SGD steps
        point = None
        for i, step in enumerate(steps_data):
            from_3d = axes.c2p(step['from'][0], step['from'][1], 
                               step['from'][0]**2 + step['from'][1]**2)
            to_3d = axes.c2p(step['to'][0], step['to'][1], 
                             step['to'][0]**2 + step['to'][1]**2)
            
            # Point marker
            if point is None:
                point = Sphere(radius=0.1)
                point.move_to(from_3d)
                point.set_color(RED)
                self.play(FadeIn(point))
            
            # Gradient arrow
            arrow = Arrow3D(
                start=from_3d,
                end=to_3d,
                color=RED,
                thickness=0.02
            )
            
            # Step label - fixed in frame
            step_text = Text(f"Step {i+1}", font_size=24)
            step_text.next_to(title, DOWN)
            self.add_fixed_in_frame_mobjects(step_text)
            
            # Animation
            self.play(
                Create(arrow),
                Write(step_text),
                run_time=0.8
            )
            self.play(
                point.animate.move_to(to_3d),
                run_time=0.7
            )
            self.remove_fixed_in_frame_mobjects(step_text)
            self.remove(step_text)
        
        # Final point
        final_text = Text("Converged!", font_size=28, color=GREEN)
        final_text.next_to(title, DOWN)
        self.add_fixed_in_frame_mobjects(final_text)
        self.play(Write(final_text))
        
        self.wait(1)
