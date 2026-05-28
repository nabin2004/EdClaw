from manim import *


class AutoScene(Scene):
    def construct(self):
        # Title
        title = Text("Learning Rate Effect", font_size=36)
        subtitle = Text("On Gradient Descent", font_size=24, color=GRAY)
        title_group = VGroup(title, subtitle).arrange(DOWN)
        title_group.to_edge(UP)
        
        self.play(Write(title), run_time=0.8)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.wait(0.3)
        
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
        
        self.play(Create(axes), run_time=1)
        self.play(Create(loss_curve), Write(loss_label), run_time=1)
        
        # Minimum point marker
        min_dot = Dot(axes.c2p(0, 0), color=YELLOW, radius=0.1)
        min_label = Text("Minimum", font_size=16, color=YELLOW).next_to(min_dot, DOWN, buff=0.2)
        self.play(FadeIn(min_dot), Write(min_label), run_time=0.6)
        self.wait(0.2)
        
        # Section 1: Too High Learning Rate (overshoots)
        high_lr_title = Text("Learning Rate: TOO HIGH", font_size=22, color=RED)
        high_lr_title.to_edge(UP).shift(DOWN * 0.8)
        
        self.play(
            FadeOut(title_group),
            FadeIn(high_lr_title),
            FadeOut(min_label),
            run_time=0.5
        )
        
        # Start point for high LR
        high_start = axes.c2p(2.5, 3.125)
        high_point = Dot(high_start, color=RED, radius=0.12)
        high_label = Text("Start", font_size=16, color=RED).next_to(high_point, UR, buff=0.1)
        
        self.play(FadeIn(high_point), Write(high_label), run_time=0.4)
        
        # Simulate gradient descent with high LR (overshoots)
        # Gradient of 0.5*x^2 is x, so update: x_new = x - lr * x
        # With lr = 1.8, it will oscillate and diverge
        positions_high = [2.5]
        lr_high = 1.8
        for _ in range(6):
            x = positions_high[-1]
            grad = x  # gradient of 0.5*x^2
            x_new = x - lr_high * grad
            positions_high.append(x_new)
        
        # Draw path with overshooting
        path_high = VMobject(color=RED, stroke_width=4)
        path_high.set_points_as_corners([axes.c2p(x, 0.5*x**2) for x in positions_high])
        
        self.play(Create(path_high), run_time=2)
        
        # Animate the point following the path
        high_tracker = ValueTracker(2.5)
        high_moving_dot = Dot(axes.c2p(2.5, 3.125), color=RED, radius=0.12)
        
        def update_high_dot(mob):
            x = high_tracker.get_value()
            mob.move_to(axes.c2p(x, 0.5*x**2))
        
        high_moving_dot.add_updater(update_high_dot)
        self.add(high_moving_dot)
        
        for i, x in enumerate(positions_high[1:], 1):
            self.play(high_tracker.animate.set_value(x), run_time=0.6)
        
        high_moving_dot.remove_updater(update_high_dot)
        
        # Show overshoot arrows
        overshoot_text = Text("OVERSHOOTS & DIVERGES!", font_size=18, color=RED)
        overshoot_text.next_to(axes, RIGHT, buff=0.5)
        self.play(Write(overshoot_text), run_time=0.6)
        self.wait(0.3)
        
        # Cleanup high LR section
        self.play(
            FadeOut(high_point, high_label, high_moving_dot, path_high, 
                   overshoot_text, high_lr_title),
            run_time=0.4
        )
        
        # Section 2: Too Low Learning Rate (crawls)
        low_lr_title = Text("Learning Rate: TOO LOW", font_size=22, color=ORANGE)
        low_lr_title.to_edge(UP).shift(DOWN * 0.8)
        
        self.play(FadeIn(low_lr_title), run_time=0.4)
        
        # Start point for low LR
        low_start = axes.c2p(2.5, 3.125)
        low_point = Dot(low_start, color=ORANGE, radius=0.12)
        low_label = Text("Start", font_size=16, color=ORANGE).next_to(low_point, UR, buff=0.1)
        
        self.play(FadeIn(low_point), Write(low_label), run_time=0.4)
        
        # Simulate gradient descent with low LR (crawls)
        positions_low = [2.5]
        lr_low = 0.08
        for _ in range(20):
            x = positions_low[-1]
            grad = x
            x_new = x - lr_low * grad
            positions_low.append(x_new)
        
        # Draw path - show first few steps clearly
        path_low = VMobject(color=ORANGE, stroke_width=4)
        path_low.set_points_as_corners([axes.c2p(x, 0.5*x**2) for x in positions_low[:8]])
        
        self.play(Create(path_low), run_time=1.5)
        
        # Animate slow progress
        low_tracker = ValueTracker(2.5)
        low_moving_dot = Dot(axes.c2p(2.5, 3.125), color=ORANGE, radius=0.12)
        
        def update_low_dot(mob):
            x = low_tracker.get_value()
            mob.move_to(axes.c2p(x, 0.5*x**2))
        
        low_moving_dot.add_updater(update_low_dot)
        self.add(low_moving_dot)
        
        # Show slow steps
        for i, x in enumerate(positions_low[1:6], 1):
            self.play(low_tracker.animate.set_value(x), run_time=0.8)
        
        # Show dotted continuation
        continuation = DashedVMobject(
            VMobject(color=ORANGE, stroke_width=3).set_points_as_corners(
                [axes.c2p(x, 0.5*x**2) for x in positions_low[5:12]]
            ),
            num_dashes=10
        )
        
        crawl_text = Text("SLOW CRAWL...", font_size=18, color=ORANGE)
        crawl_text.next_to(axes, RIGHT, buff=0.5)
        
        self.play(FadeIn(continuation), Write(crawl_text), run_time=0.8)
        self.wait(0.3)
        
        low_moving_dot.remove_updater(update_low_dot)
        
        # Cleanup low LR section
        self.play(
            FadeOut(low_point, low_label, low_moving_dot, path_low, 
                   continuation, crawl_text, low_lr_title),
            run_time=0.4
        )
        
        # Section 3: Just Right Learning Rate (converges)
        good_lr_title = Text("Learning Rate: JUST RIGHT", font_size=22, color=GREEN)
        good_lr_title.to_edge(UP).shift(DOWN * 0.8)
        
        self.play(FadeIn(good_lr_title), run_time=0.4)
        
        # Start point for good LR
        good_start = axes.c2p(2.5, 3.125)
        good_point = Dot(good_start, color=GREEN, radius=0.12)
        good_label = Text("Start", font_size=16, color=GREEN).next_to(good_point, UR, buff=0.1)
        
        self.play(FadeIn(good_point), Write(good_label), run_time=0.4)
        
        # Simulate gradient descent with good LR (converges smoothly)
        positions_good = [2.5]
        lr_good = 0.4
        for _ in range(12):
            x = positions_good[-1]
            grad = x
            x_new = x - lr_good * grad
            positions_good.append(x_new)
        
        # Draw smooth converging path
        path_good = VMobject(color=GREEN, stroke_width=4)
        path_good.set_points_as_corners([axes.c2p(x, 0.5*x**2) for x in positions_good])
        
        self.play(Create(path_good), run_time=1.5)
        
        # Animate smooth convergence
        good_tracker = ValueTracker(2.5)
        good_moving_dot = Dot(axes.c2p(2.5, 3.125), color=GREEN, radius=0.12)
        
        def update_good_dot(mob):
            x = good_tracker.get_value()
            mob.move_to(axes.c2p(x, 0.5*x**2))
        
        good_moving_dot.add_updater(update_good_dot)
        self.add(good_moving_dot)
        
        # Show smooth convergence steps
        for x in positions_good[1:]:
            self.play(good_tracker.animate.set_value(x), run_time=0.4)
        
        # Reach the minimum
        converge_text = Text("SMOOTH CONVERGENCE!", font_size=18, color=GREEN)
        converge_text.next_to(axes, RIGHT, buff=0.5)
        
        self.play(
            good_moving_dot.animate.scale(1.5).set_color(YELLOW),
            Write(converge_text),
            run_time=0.8
        )
        
        good_moving_dot.remove_updater(update_good_dot)
        self.wait(0.5)
        
        # Cleanup
        self.play(
            FadeOut(good_point, good_label, good_moving_dot, path_good, 
                   converge_text, min_dot),
            run_time=0.4
        )
        
        # Final summary
        self.play(
            good_lr_title.animate.become(Text("Choose Learning Rate Wisely!", 
                                              font_size=28, color=WHITE).to_edge(UP).shift(DOWN * 0.8)),
            run_time=0.4
        )
        
        # Show all three comparison
        comparison = VGroup(
            Text("Too High → Diverges", font_size=20, color=RED),
            Text("Too Low → Slow", font_size=20, color=ORANGE),
            Text("Just Right → Converges", font_size=20, color=GREEN),
        ).arrange(DOWN, buff=0.5)
        comparison.next_to(axes, RIGHT, buff=0.3)
        
        for item in comparison:
            self.play(Write(item), run_time=0.5)
        
        self.wait(1)
        
        # Fade out everything
        self.play(
            FadeOut(axes, loss_curve, loss_label, good_lr_title, comparison),
            run_time=1
        )
        
        # Final message
        final_text = Text("Optimize Your Learning!", font_size=36, color=BLUE)
        self.play(Write(final_text), run_time=1)
        self.wait(0.5)
        self.play(FadeOut(final_text), run_time=0.5)
