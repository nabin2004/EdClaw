from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title - shorter
        title = Text("Learning Rate Effect", font_size=40)
        self.play(Write(title), run_time=0.6)
        self.wait(0.2)
        self.play(FadeOut(title), run_time=0.3)
        
        # Create axes and parabolic loss function
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-1, 8, 1],
            axis_config={"color": WHITE, "include_numbers": False},
            x_length=6,
            y_length=4,
        )
        axes.to_edge(DOWN, buff=1)
        
        # Loss function: y = 0.5 * x^2
        loss_curve = axes.plot(lambda x: 0.5 * x**2, color=BLUE, stroke_width=3)
        loss_label = Text("Loss", font_size=20, color=BLUE).next_to(loss_curve, UR, buff=0.3)
        
        self.play(Create(axes), Create(loss_curve), Write(loss_label), run_time=0.8)
        
        # Minimum point marker
        min_dot = Dot(axes.c2p(0, 0), color=YELLOW, radius=0.1)
        min_label = Text("Min", font_size=16, color=YELLOW).next_to(min_dot, DOWN, buff=0.2)
        self.play(FadeIn(min_dot), Write(min_label), run_time=0.4)
        
        # ===== Section 1: Too High Learning Rate (overshoots) =====
        high_lr_title = Text("Too HIGH → Diverges", font_size=22, color=RED)
        high_lr_title.to_edge(UP)
        
        self.play(FadeIn(high_lr_title), run_time=0.3)
        
        # Start point for high LR
        high_point = Dot(axes.c2p(2.5, 3.125), color=RED, radius=0.12)
        high_label = Text("Start", font_size=16, color=RED).next_to(high_point, UR, buff=0.1)
        
        self.play(FadeIn(high_point), Write(high_label), run_time=0.3)
        
        # Simulate gradient descent with high LR (overshoots)
        positions_high = [2.5]
        lr_high = 1.8
        for _ in range(5):
            x = positions_high[-1]
            grad = x
            x_new = x - lr_high * grad
            positions_high.append(x_new)
        
        # Animate the point moving
        high_tracker = ValueTracker(2.5)
        high_moving_dot = Dot(axes.c2p(2.5, 3.125), color=RED, radius=0.12)
        
        def update_high_dot(mob):
            x = high_tracker.get_value()
            mob.move_to(axes.c2p(x, 0.5*x**2))
        
        high_moving_dot.add_updater(update_high_dot)
        self.add(high_moving_dot)
        
        # Create path as we go
        path_points = [axes.c2p(positions_high[0], 0.5*positions_high[0]**2)]
        path_high = VMobject(color=RED, stroke_width=4)
        path_high.set_points_as_corners(path_points)
        self.add(path_high)
        
        for i, x in enumerate(positions_high[1:], 1):
            new_point = axes.c2p(x, 0.5*x**2)
            path_points.append(new_point)
            path_high.set_points_as_corners(path_points)
            self.play(high_tracker.animate.set_value(x), run_time=0.35)
        
        high_moving_dot.remove_updater(update_high_dot)
        
        # Show overshoot text
        overshoot_text = Text("OVERSHOOTS!", font_size=18, color=RED).next_to(axes, RIGHT, buff=0.3)
        self.play(Write(overshoot_text), run_time=0.4)
        self.wait(0.15)
        
        # Cleanup
        self.play(
            FadeOut(high_point, high_label, high_moving_dot, overshoot_text, high_lr_title),
            run_time=0.3
        )
        path_high.fade(darkness=0.7)
        
        # ===== Section 2: Too Low Learning Rate (crawls) =====
        low_lr_title = Text("Too LOW → Crawls", font_size=22, color=ORANGE)
        low_lr_title.to_edge(UP)
        
        self.play(FadeIn(low_lr_title), run_time=0.3)
        
        # Start point for low LR
        low_point = Dot(axes.c2p(2.5, 3.125), color=ORANGE, radius=0.12)
        low_label = Text("Start", font_size=16, color=ORANGE).next_to(low_point, UR, buff=0.1)
        
        self.play(FadeIn(low_point), Write(low_label), run_time=0.3)
        
        # Simulate slow progress
        positions_low = [2.5, 2.3, 2.12, 1.95, 1.8]
        lr_low = 0.08
        
        # Animate slow steps
        low_tracker = ValueTracker(2.5)
        low_moving_dot = Dot(axes.c2p(2.5, 3.125), color=ORANGE, radius=0.12)
        
        def update_low_dot(mob):
            x = low_tracker.get_value()
            mob.move_to(axes.c2p(x, 0.5*x**2))
        
        low_moving_dot.add_updater(update_low_dot)
        self.add(low_moving_dot)
        
        # Draw path
        path_low_points = [axes.c2p(positions_low[0], 0.5*positions_low[0]**2)]
        path_low = VMobject(color=ORANGE, stroke_width=4)
        path_low.set_points_as_corners(path_low_points)
        self.add(path_low)
        
        for x in positions_low[1:]:
            path_low_points.append(axes.c2p(x, 0.5*x**2))
            path_low.set_points_as_corners(path_low_points)
            self.play(low_tracker.animate.set_value(x), run_time=0.5)
        
        low_moving_dot.remove_updater(update_low_dot)
        
        # Show slow crawl indicator
        crawl_text = Text("TOO SLOW...", font_size=18, color=ORANGE).next_to(axes, RIGHT, buff=0.3)
        dotted_path = DashedLine(
            axes.c2p(1.8, 0.5*1.8**2),
            axes.c2p(0.5, 0.5*0.5**2),
            color=ORANGE,
            dash_length=0.1
        )
        
        self.play(Write(crawl_text), FadeIn(dotted_path), run_time=0.4)
        self.wait(0.15)
        
        # Cleanup
        self.play(
            FadeOut(low_point, low_label, low_moving_dot, crawl_text, dotted_path, low_lr_title),
            run_time=0.3
        )
        path_low.fade(darkness=0.7)
        
        # ===== Section 3: Just Right Learning Rate (converges) =====
        good_lr_title = Text("Just RIGHT → Converges", font_size=22, color=GREEN)
        good_lr_title.to_edge(UP)
        
        self.play(FadeIn(good_lr_title), run_time=0.3)
        
        # Start point for good LR
        good_point = Dot(axes.c2p(2.5, 3.125), color=GREEN, radius=0.12)
        good_label = Text("Start", font_size=16, color=GREEN).next_to(good_point, UR, buff=0.1)
        
        self.play(FadeIn(good_point), Write(good_label), run_time=0.3)
        
        # Simulate smooth convergence
        positions_good = [2.5, 1.5, 0.9, 0.54, 0.32, 0.2, 0.12, 0.07]
        
        # Animate smooth convergence
        good_tracker = ValueTracker(2.5)
        good_moving_dot = Dot(axes.c2p(2.5, 3.125), color=GREEN, radius=0.12)
        
        def update_good_dot(mob):
            x = good_tracker.get_value()
            mob.move_to(axes.c2p(x, 0.5*x**2))
        
        good_moving_dot.add_updater(update_good_dot)
        self.add(good_moving_dot)
        
        # Draw smooth path
        path_good_points = [axes.c2p(positions_good[0], 0.5*positions_good[0]**2)]
        path_good = VMobject(color=GREEN, stroke_width=4)
        path_good.set_points_as_corners(path_good_points)
        self.add(path_good)
        
        for x in positions_good[1:]:
            path_good_points.append(axes.c2p(x, 0.5*x**2))
            path_good.set_points_as_corners(path_good_points)
            self.play(good_tracker.animate.set_value(x), run_time=0.3)
        
        # Reach the minimum
        converge_text = Text("PERFECT!", font_size=20, color=GREEN).next_to(axes, RIGHT, buff=0.3)
        
        self.play(
            good_moving_dot.animate.scale(1.5).set_color(YELLOW),
            Write(converge_text),
            run_time=0.5
        )
        
        good_moving_dot.remove_updater(update_good_dot)
        self.wait(0.3)
        
        # Cleanup
        self.play(
            FadeOut(good_point, good_label, good_moving_dot, converge_text, min_label),
            run_time=0.3
        )
        
        # ===== Final summary =====
        summary_title = Text("Summary", font_size=28, color=WHITE)
        summary_title.to_edge(UP)
        
        self.play(FadeIn(summary_title), run_time=0.3)
        
        # Show all three comparison
        comparison = VGroup(
            Text("• High LR → Diverges", font_size=20, color=RED),
            Text("• Low LR → Slow", font_size=20, color=ORANGE),
            Text("• Right LR → Converges", font_size=20, color=GREEN),
        ).arrange(DOWN, buff=0.4)
        comparison.next_to(axes, RIGHT, buff=0.2)
        
        for item in comparison:
            self.play(Write(item), run_time=0.3)
        
        self.wait(0.5)
        
        # Fade out everything
        self.play(
            FadeOut(axes, loss_curve, loss_label, min_dot, summary_title, comparison,
                   path_high, path_low, path_good),
            run_time=0.6
        )
        
        # Final message
        final_text = Text("Optimize Your Learning!", font_size=40, color=BLUE)
        self.play(Write(final_text), run_time=0.6)
        self.wait(0.3)
        self.play(FadeOut(final_text), run_time=0.4)
