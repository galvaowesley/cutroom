"""Gradient Descent: Descending the Loss Landscape.

A 28 s cutroom-math explainer demonstrating the new editorial math standard:
- Zone 1: Context breadcrumb ('Optimization · gradient step') & active formula
- Zone 2: Non-convex loss bowl, tangent slope, step vector, and live monospace telemetry
- Zone 3: Synchronized editorial captions highlighting key concepts
- Strategic tactile sound design with earshot.

Render: manimgx render src/scene.py GradientDescent -o work/raw.mp4
"""
import json
import math
import subprocess
from pathlib import Path

import manimgx as m
from cutroom_voice import manimgx_voice

# Active brand: cutroom (Hot Signal on Night Plum)
B = json.loads(subprocess.run(["cutroom", "brand", "show", "--json"], capture_output=True, text=True, check=True).stdout)
C, F = B["colors"], B["fonts"]
BG, INK = C["deep"], C["on_deep"]
CURVE, CUE, SOFT, MUTED = C["primary"], C["accent"], C["accent_soft"], "#8E929F"
DISPLAY, TEXT, MONO = F["display"], F["text"], F["mono"]
LOGO = Path(B["paths"]["logos"]["on_deep"])
m.config.background_color = BG

ETA = 0.20
W_START = 2.10


def L(w: float) -> float:
    return 0.5 * w**2 + 0.3 * math.cos(2.5 * w)


def grad(w: float) -> float:
    return w - 0.75 * math.sin(2.5 * w)


# Verify numerical consistency for cited facts
assert abs(W_START - 2.10) < 1e-6
assert abs(L(W_START) - 2.359) < 0.01
assert abs(grad(W_START) - 2.744) < 0.01


class GradientDescent(m.Scene):
    voice = manimgx_voice("narrator")

    def construct(self) -> None:
        # -------------------------------------------------------------
        # ZONE 1: Context Breadcrumb & Active Formula (Top-Left)
        # -------------------------------------------------------------
        eyebrow = m.Text("Optimization · gradient step", font=TEXT, weight=m.SEMIBOLD, font_size=22, color=MUTED)
        eyebrow.to_corner(m.UL, buff=0.55)

        formula = m.MathTex(r"w_{t+1} = w_t -", r"\eta \nabla L(w_t)", color=INK, font_size=38)
        formula[1].set_color(CURVE)
        formula.next_to(eyebrow, m.DOWN, buff=0.18, aligned_edge=m.LEFT)

        # -------------------------------------------------------------
        # ZONE 2: Tactile Mechanism + Live Telemetry (Center Stage)
        # -------------------------------------------------------------
        axes = m.Axes(
            x_range=[-2.4, 2.6, 1],
            y_range=[-0.2, 3.8, 1],
            x_length=9.0,
            y_length=3.9,
            axis_config={"color": MUTED, "stroke_width": 1.5, "include_ticks": True},
        )
        axes.move_to([0, 0.35, 0])

        loss_curve = axes.plot(L, x_range=[-2.2, 2.35], color=CURVE, stroke_width=5)
        loss_area = axes.get_area(loss_curve, x_range=[-2.2, 2.35], color=CURVE, opacity=0.12)
        curve_label = m.MathTex(r"L(w) = \tfrac{1}{2}w^2 + 0.3\cos(2.5w)", color=CURVE, font_size=26)
        curve_label.move_to(axes.c2p(1.15, 3.35))

        w = m.ValueTracker(W_START)
        step_idx = m.ValueTracker(0)

        # Focal point on loss surface
        dot = m.Dot(axes.c2p(W_START, L(W_START)), radius=0.11, color=CUE)
        dot.add_updater(lambda d: d.move_to(axes.c2p(w.get_value(), L(w.get_value()))))

        # Tangent line indicating local slope
        wv_init = W_START
        dx = 0.55
        p1 = axes.c2p(wv_init - dx, L(wv_init) - grad(wv_init) * dx)
        p2 = axes.c2p(wv_init + dx, L(wv_init) + grad(wv_init) * dx)
        tangent = m.Line(p1, p2, color=SOFT, stroke_width=3.5)

        def update_tangent(line):
            wv = w.get_value()
            slope = grad(wv)
            pt1 = axes.c2p(wv - dx, L(wv) - slope * dx)
            pt2 = axes.c2p(wv + dx, L(wv) + slope * dx)
            line.put_start_and_end_on(pt1, pt2)

        tangent.add_updater(update_tangent)

        # Negative gradient vector (step direction downhill)
        s_init = -ETA * grad(wv_init)
        arrow_start = axes.c2p(wv_init, L(wv_init))
        arrow_end = axes.c2p(wv_init + s_init, L(wv_init))
        step_arrow = m.Arrow(arrow_start, arrow_end, buff=0, color=CUE, stroke_width=4, max_tip_length_to_length_ratio=0.3)

        def update_arrow(arr):
            wv = w.get_value()
            s = -ETA * grad(wv)
            p_s = axes.c2p(wv, L(wv))
            p_e = axes.c2p(wv + (s if abs(s) > 0.02 else -0.02), L(wv))
            arr.put_start_and_end_on(p_s, p_e)

        step_arrow.add_updater(update_arrow)

        # Live Monospace Telemetry Box
        tele_box = m.RoundedRectangle(
            corner_radius=0.12, width=9.2, height=0.62,
            fill_color="#180B28", fill_opacity=0.85,
            stroke_color=MUTED, stroke_opacity=0.4, stroke_width=1.5
        )
        tele_box.next_to(axes, m.DOWN, buff=0.18)

        # Telemetry components using DecimalNumber
        t_lbl1 = m.Text("step: ", font=MONO, font_size=20, color=MUTED)
        t_step = m.Integer(0, font_size=22, color=INK)
        t_lbl2 = m.Text(" | w: ", font=MONO, font_size=20, color=MUTED)
        t_w = m.DecimalNumber(W_START, num_decimal_places=2, font_size=22, color=INK)
        t_lbl3 = m.Text(" | L(w): ", font=MONO, font_size=20, color=MUTED)
        t_loss = m.DecimalNumber(L(W_START), num_decimal_places=3, font_size=22, color=CURVE)
        t_lbl4 = m.Text(" | ∇L: ", font=MONO, font_size=20, color=MUTED)
        t_grad = m.DecimalNumber(grad(W_START), num_decimal_places=2, font_size=22, color=CUE)

        t_step.add_updater(lambda mob: mob.set_value(int(step_idx.get_value())))
        t_w.add_updater(lambda mob: mob.set_value(w.get_value()))
        t_loss.add_updater(lambda mob: mob.set_value(L(w.get_value())))
        t_grad.add_updater(lambda mob: mob.set_value(grad(w.get_value())))

        tele_group = m.VGroup(t_lbl1, t_step, t_lbl2, t_w, t_lbl3, t_loss, t_lbl4, t_grad).arrange(m.RIGHT, buff=0.12)
        tele_group.move_to(tele_box.get_center())

        # -------------------------------------------------------------
        # ZONE 3: Synchronized Editorial Captions (Bottom Zone)
        # -------------------------------------------------------------
        caption_pos = m.DOWN * 3.42

        c1 = m.Text("How does AI find the best weights out of billions?", font=TEXT, font_size=26, color=INK, t2c={"best weights": CUE})
        c1.move_to(caption_pos)
        c2 = m.Text("It slides down a loss landscape.", font=TEXT, font_size=26, color=INK, t2c={"loss landscape": CURVE})
        c2.move_to(caption_pos)
        c3 = m.Text("At any point, the tangent slope gives the gradient.", font=TEXT, font_size=26, color=INK, t2c={"tangent slope": SOFT})
        c3.move_to(caption_pos)
        c4 = m.Text("It points steepest uphill, so we step in reverse.", font=TEXT, font_size=26, color=INK, t2c={"step in reverse": CUE})
        c4.move_to(caption_pos)
        c5 = m.Text("Scaled by the learning rate eta, each gradient step descends toward the minimum.",
                    font=TEXT, font_size=24, color=INK, t2c={"learning rate eta": CURVE, "minimum": CUE})
        c5.move_to(caption_pos)
        c6 = m.Text("Where the curve flattens, the gradient vanishes to zero.", font=TEXT, font_size=26, color=INK, t2c={"vanishes to zero": CUE})
        c6.move_to(caption_pos)
        c7 = m.Text("The descent converges, locking into optimal weights.", font=TEXT, font_size=26, color=INK, t2c={"converges": CURVE, "optimal weights": CUE})
        c7.move_to(caption_pos)

        logo = m.SVGMobject(str(LOGO), height=0.40).to_corner(m.DR, buff=0.55)

        # -------------------------------------------------------------
        # CHOREOGRAPHY & PROGRESSIVE DISCLOSURE
        # -------------------------------------------------------------
        self.add(eyebrow, formula)
        self.say("How does AI find the [best weights out of billions]? It slides down a [loss landscape].",
                 m.AnimationGroup(m.FadeIn(c1), m.Create(axes), m.Create(loss_curve), m.FadeIn(loss_area), m.FadeIn(curve_label), lag_ratio=0.2),
                 m.AnimationGroup(m.FadeOut(c1), m.FadeIn(c2), m.FadeIn(dot), m.FadeIn(tele_box), m.FadeIn(tele_group)))

        self.say("At any point, the [tangent slope] gives the gradient. It points steepest uphill, so we [step in reverse].",
                 m.AnimationGroup(m.FadeOut(c2), m.FadeIn(c3), m.Create(tangent)),
                 m.AnimationGroup(m.FadeOut(c3), m.FadeIn(c4), m.FadeIn(step_arrow)))

        self.say("Scaled by the [learning rate eta], each gradient step [descends toward the minimum].",
                 m.AnimationGroup(m.FadeOut(c4), m.FadeIn(c5)),
                 m.AnimationGroup(
                     w.animate(run_time=3.6, rate_func=m.smooth).set_value(0.81),
                     step_idx.animate(run_time=3.6, rate_func=m.linear).set_value(4)
                 ))

        self.say("Where the curve flattens, the [gradient vanishes to zero]. The descent [converges], locking into optimal weights.",
                 m.AnimationGroup(m.FadeOut(c5), m.FadeIn(c6)),
                 m.AnimationGroup(m.FadeOut(c6), m.FadeIn(c7), m.FadeIn(logo)))
        self.wait(1.0)
