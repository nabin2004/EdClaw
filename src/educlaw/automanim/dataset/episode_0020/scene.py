"""Manim animation: Mini-batch size effect on gradient noise visualization."""
from manim import *
import numpy as np


class AutoScene(Scene):
    def construct(self):
        # ------------------------------
        # SETUP: 3D Loss Surface
        # ------------------------------
        self.camera.background_color = "#1a1a2e"
        
        # Create axes
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[0, 4, 1],
            x_length=6,
            y_length=6,
            z_length=4,
            axis_config={"color": WHITE},
        )
        
        # Shift axes slightly for better view
        axes.shift(LEFT * 0.5 + DOWN * 0.5)
        
        # Define bowl-shaped loss surface
        def loss_func(u, v):
            return (u ** 2 / 2 + v ** 2 / 2 + 0.5 * np.sin(3 * u) * np.cos(3 * v) * 0.3)
        
        # Create surface
        surface = Surface(
            lambda u, v: axes.c2p(u, v, loss_func(u, v)),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(30, 30),
            fill_color=BLUE_D,
            fill_opacity=0.5,
            stroke_color=BLUE_B,
            stroke_width=0.5,
        )
        
        # Title
        title = Text("Batch Size Effect on Gradient Noise", font_size=28, color=WHITE)
        title.to_edge(UP, buff=0.3)
        
        # Labels
        x_label = Text("Weight 1", font_size=16, color=GRAY_A).next_to(axes, DOWN, buff=0.1).shift(RIGHT * 2)
        y_label = Text("Weight 2", font_size=16, color=GRAY_A).next_to(axes, RIGHT, buff=0.1).shift(UP * 0.5)
        loss_label = Text("Loss", font_size=16, color=GRAY_A).next_to(axes, UP, buff=0.1).shift(RIGHT * 0.5)
        
        # Start camera position
        self.set_camera_orientation(phi=75 * DEGREES, theta=-30 * DEGREES)
        
        # ------------------------------
        # INTRO: Show surface
        # ------------------------------
        self.play(Write(title), run_time=1)
        self.wait(0.3)
        
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(axes), run_time=1)
        self.play(Create(surface), run_time=1.5)
        
        # Add labels
        self.add_fixed_in_frame_mobjects(x_label, y_label, loss_label)
        self.play(FadeIn(x_label, y_label, loss_label), run_time=0.5)
        self.wait(0.5)
        
        # ------------------------------
        # Simulate optimization paths
        # ------------------------------
        
        # Gradient function (noisy)
        def gradient(u, v, batch_size):
            # True gradient
            du = u + 0.5 * 3 * np.cos(3 * u) * np.cos(3 * v) * 0.3
            dv = v - 0.5 * np.sin(3 * u) * np.sin(3 * v) * 3 * 0.3
            
            # Add noise based on batch size
            noise_scale = 1.0 / np.sqrt(batch_size)
            noise_u = np.random.normal(0, noise_scale)
            noise_v = np.random.normal(0, noise_scale)
            
            return du + noise_u, dv + noise_v
        
        # Paths starting point
        start_point = np.array([2.5, 2.0])
        
        # Generate paths for different batch sizes
        np.random.seed(42)
        
        paths = {}
        colors = {1: RED, 32: GREEN, "full": GOLD}
        labels = {1: "Batch=1", 32: "Batch=32", "full": "Batch=Full"}
        
        for batch_size in [1, 32, "full"]:
            bs = 1000 if batch_size == "full" else batch_size
            lr = 0.25
            u, v = start_point[0], start_point[1]
            
            path_points = []
            for step in range(40):
                path_points.append(axes.c2p(u, v, loss_func(u, v)))
                du, dv = gradient(u, v, bs)
                u -= lr * du
                v -= lr * dv
                # Check bounds
                u = np.clip(u, -3, 3)
                v = np.clip(v, -3, 3)
            
            paths[batch_size] = path_points
        
        # Create path VMobjects
        path_objs = {}
        for batch_size in [1, 32, "full"]:
            path = paths[batch_size]
            vmobj = VMobject()
            vmobj.set_points_as_corners(path)
            vmobj.set_color(colors[batch_size])
            vmobj.set_stroke(width=3)
            path_objs[batch_size] = vmobj
        
        # Legends
        legend_vgroup = VGroup()
        for bs in [1, 32, "full"]:
            dot = Dot(color=colors[bs], radius=0.1)
            txt = Text(labels[bs], font_size=14, color=colors[bs])
            leg = VGroup(dot, txt).arrange(RIGHT, buff=0.2)
            legend_vgroup.add(leg)
        legend_vgroup.arrange(DOWN, buff=0.2)
        legend_vgroup.to_corner(UR, buff=0.5)
        self.add_fixed_in_frame_mobjects(legend_vgroup)
        
        # ------------------------------
        # ANIMATE: Batch Size 1 (noisy)
        # ------------------------------
        bs1_text = Text("Batch Size 1: High Variance", font_size=18, color=RED)
        bs1_text.to_edge(UP, buff=0.8)
        self.add_fixed_in_frame_mobjects(bs1_text)
        
        self.play(FadeIn(bs1_text), run_time=0.5)
        self.play(Create(path_objs[1]), run_time=2)
        
        # Show legend
        self.play(FadeIn(legend_vgroup[0]), run_time=0.3)
        self.wait(0.5)
        self.play(FadeOut(bs1_text), run_time=0.3)
        
        # ------------------------------
        # ANIMATE: Batch Size 32 (moderate)
        # ------------------------------
        bs32_text = Text("Batch Size 32: Moderate Variance", font_size=18, color=GREEN)
        bs32_text.to_edge(UP, buff=0.8)
        self.add_fixed_in_frame_mobjects(bs32_text)
        
        self.play(FadeIn(bs32_text), run_time=0.5)
        self.play(Create(path_objs[32]), run_time=2)
        
        self.play(FadeIn(legend_vgroup[1]), run_time=0.3)
        self.wait(0.5)
        self.play(FadeOut(bs32_text), run_time=0.3)
        
        # ------------------------------
        # ANIMATE: Full Batch (smooth)
        # ------------------------------
        full_text = Text("Full Batch: Smooth Gradient", font_size=18, color=GOLD)
        full_text.to_edge(UP, buff=0.8)
        self.add_fixed_in_frame_mobjects(full_text)
        
        self.play(FadeIn(full_text), run_time=0.5)
        
        # Also show full legend
        self.play(FadeIn(legend_vgroup[2]), run_time=0.3)
        self.play(Create(path_objs["full"]), run_time=2)
        self.wait(0.5)
        self.play(FadeOut(full_text), run_time=0.3)
        
        # ------------------------------
        # FINAL: All paths together
        # ------------------------------
        final_text = Text("Smaller batches add noise but can escape local minima", 
                          font_size=16, color=WHITE)
        final_text.to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(final_text)
        
        # Show all paths together with some camera movement
        self.move_camera(phi=70 * DEGREES, theta=-45 * DEGREES, run_time=2)
        self.play(Write(final_text), run_time=1)
        
        self.wait(2)
