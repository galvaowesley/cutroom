"""The derivative is the slope of the tangent: a 38 s cutroom-math example (ManimGX + local narration).

f(x) = x³/3 − x. A secant through x = 1.5 and x + h turns into the tangent as h shrinks; then the tangent rides the
curve and its slope traces f′(x) = x² − 1 on the same axes. Every number on screen is computed here.
Render: manimgx render scene.py Derivative -o ../out/derivative.mp4
"""
import json
import subprocess
from pathlib import Path

import manimgx as m
from cutroom_voice import manimgx_voice

# The active brand (cutroom: Hot Signal). `cutroom brand show --json` gives colors, fonts and logo paths.
B = json.loads(subprocess.run(["cutroom", "brand", "show", "--json"], capture_output=True, text=True, check=True).stdout)
C, F = B["colors"], B["fonts"]
BG, INK, CURVE, CUE, SOFT, MUTED = C["deep"], C["on_deep"], C["primary"], C["accent"], C["accent_soft"], "#B9AEC9"
DISPLAY, TEXT = F["display"], F["text"]
LOGO = Path(B["paths"]["logos"]["on_deep"])
m.config.background_color = BG

X0, H0, H_END = 1.5, 1.2, 0.001


def f(x: float) -> float:
    return x**3 / 3 - x


def df(x: float) -> float:
    return x**2 - 1


def secant_slope(x: float, h: float) -> float:
    return (f(x + h) - f(x)) / h


assert abs(df(X0) - 1.25) < 1e-12 and abs(secant_slope(X0, H0) - 3.53) < 0.005  # the numbers the script cites


class Derivative(m.Scene):
    voice = manimgx_voice("narrator")

    def construct(self) -> None:
        title = m.Text("How steep is a curve at one point?", font=DISPLAY, weight=m.SEMIBOLD, font_size=44, color=INK)
        title.to_edge(m.UP, buff=0.55).to_edge(m.LEFT, buff=0.7)

        axes = m.Axes(x_range=[-2.8, 2.8, 1], y_range=[-3.5, 4.5, 1], x_length=7.0, y_length=5.6,
                      axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": True})
        axes.to_edge(m.LEFT, buff=0.7).shift(m.DOWN * 0.45)
        curve = axes.plot(f, x_range=[-2.62, 2.72], color=CURVE, stroke_width=6)
        f_label = m.MathTex(r"f(x)=\tfrac{x^3}{3}-x", color=CURVE, font_size=36)
        f_label.move_to(axes.c2p(0.2, 4.1), aligned_edge=m.LEFT)

        x = m.ValueTracker(X0)
        h = m.ValueTracker(H0)

        def point(t):
            return axes.c2p(t, f(t))

        dot = m.always_redraw(lambda: m.Dot(point(x.get_value()), radius=0.11, color=CUE))
        dot2 = m.always_redraw(lambda: m.Dot(point(x.get_value() + h.get_value()), radius=0.09, color=INK))

        def secant():
            """The line through both points, clipped to the axes so it never runs into the title."""
            a, s = x.get_value(), secant_slope(x.get_value(), h.get_value())
            x1, x2 = a - 1.1, a + h.get_value() + 0.55
            y_lo, y_hi = -3.4, 4.4
            if s:
                x1 = max(x1, a + (min(y_lo, y_hi) - f(a)) / s if s > 0 else a + (y_hi - f(a)) / s)
                x2 = min(x2, a + (y_hi - f(a)) / s if s > 0 else a + (y_lo - f(a)) / s)
            return m.Line(axes.c2p(x1, f(a) + s * (x1 - a)), axes.c2p(x2, f(a) + s * (x2 - a)), color=CUE, stroke_width=5)

        sec = m.always_redraw(secant)

        # Right panel: formula and live readouts.
        rise = m.MathTex(r"\text{slope}=\frac{f(x+h)-f(x)}{h}", color=INK, font_size=42)
        h_txt = m.MathTex("h=", color=MUTED, font_size=44)
        h_val = m.always_redraw(lambda: m.DecimalNumber(h.get_value(), num_decimal_places=3, color=INK, font_size=44)
                                .next_to(h_txt, m.RIGHT, buff=0.15))
        s_txt = m.MathTex(r"\text{slope}=", color=MUTED, font_size=44)
        label = [s_txt]  # what the live value sits next to: "slope =", then "f'(1.5) =", then "f'(x) ="
        value = [lambda: secant_slope(x.get_value(), h.get_value())]
        s_val = m.always_redraw(lambda: m.DecimalNumber(value[0](), num_decimal_places=2, color=CUE, font_size=56)
                                .next_to(label[0], m.RIGHT, buff=0.15))
        readouts = m.VGroup(h_txt, s_txt).arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.55)
        panel = m.VGroup(rise, readouts).arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.7)
        panel.next_to(axes, m.RIGHT, buff=0.7).shift(m.UP * 0.3)

        # 1. Hook
        self.add(title)
        self.say("[A curve] rises and falls. [How steep] is it at one single point?",
                 m.AnimationGroup(m.Create(axes), m.Create(curve), m.FadeIn(f_label), lag_ratio=0.25),
                 m.FadeIn(dot, scale=0.5))

        # 2. Secant
        self.say("Take a [second point], a small step h away. The [line through both] has a slope: rise over run.",
                 m.AnimationGroup(m.FadeIn(dot2), m.FadeIn(h_txt), m.FadeIn(h_val)),
                 m.AnimationGroup(m.Create(sec), m.Write(rise), m.FadeIn(s_txt), m.FadeIn(s_val)))

        # 3. Limit
        limit = m.MathTex(r"f'(x)=\lim_{h\to 0}\frac{f(x+h)-f(x)}{h}", color=INK, font_size=42).move_to(rise, aligned_edge=m.LEFT)
        at = m.MathTex(r"f'(1.5)=", color=MUTED, font_size=44).move_to(s_txt, aligned_edge=m.LEFT)
        label[0] = at
        self.say("Now [shrink h] toward zero. The line becomes the [tangent]. Its slope, one point two five, is the derivative.",
                 h.animate(run_time=3.2, rate_func=m.smooth).set_value(H_END),
                 m.AnimationGroup(m.TransformMatchingTex(rise, limit), m.FadeTransform(s_txt, at), m.FadeOut(dot2)))
        value[0] = lambda: df(x.get_value())

        # 4. The derivative graph: the tangent rides the curve, its slope traces f'(x)
        new_title = m.Text("Every slope, plotted: f′(x) = x² − 1", font=DISPLAY, weight=m.SEMIBOLD, font_size=44,
                           color=INK).move_to(title, aligned_edge=m.LEFT)
        deriv_label = m.MathTex(r"f'(x)=x^2-1", color=SOFT, font_size=46).move_to(limit, aligned_edge=m.LEFT)
        at_x = m.MathTex(r"f'(x)=", color=MUTED, font_size=44).move_to(at, aligned_edge=m.LEFT)
        flats = m.VGroup(*[m.DashedLine(axes.c2p(v, f(v)), axes.c2p(v, 0), color=MUTED, stroke_width=3, dash_length=0.1)
                           for v in (-1, 1)])
        zero_tag = m.Text("slope 0", font=TEXT, font_size=24, color=MUTED).next_to(axes.c2p(1, f(1)), m.DOWN, buff=0.3)
        deriv = axes.plot(df, x_range=[-2.2, 2.2], color=SOFT, stroke_width=5)
        self.say("[Slide the point] along the curve.",
                 m.AnimationGroup(m.FadeTransform(title, new_title), m.TransformMatchingTex(limit, deriv_label),
                                  m.FadeTransform(at, at_x), m.FadeOut(h_txt), m.FadeOut(h_val),
                                  x.animate(run_time=1.4).set_value(-2.2)))
        label[0] = at_x
        # created here, once the point sits at x = -2.2, so the trace starts where the sweep starts
        tracer = m.always_redraw(lambda: m.Dot(axes.c2p(x.get_value(), df(x.get_value())), radius=0.08, color=SOFT))
        trace = m.TracedPath(tracer.get_center, stroke_color=SOFT, stroke_width=5)
        self.add(tracer, trace)
        self.say("Where it is [flat], the slope is zero. All the slopes together [draw] f prime: x squared minus one.",
                 m.AnimationGroup(x.animate(run_time=5.0, rate_func=m.linear).set_value(2.2),
                                  m.Create(flats), m.FadeIn(zero_tag)),
                 m.Create(deriv, run_time=0.8))
        self.remove(trace)
        self.add(deriv)
        self.wait(0.2)

        # 5. Close
        card = m.VGroup(m.Text("The derivative is the slope", font=DISPLAY, weight=m.SEMIBOLD, font_size=30, color=INK),
                        m.Text("of the tangent,", font=DISPLAY, weight=m.SEMIBOLD, font_size=30, color=INK),
                        m.Text("at every point.", font=DISPLAY, weight=m.SEMIBOLD, font_size=30, color=CUE))
        card.arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.16)
        card.next_to(deriv_label, m.DOWN, buff=0.7, aligned_edge=m.LEFT)
        logo = m.SVGMobject(str(LOGO), height=0.42).to_corner(m.DR, buff=0.55)
        self.say("The derivative: the slope of the tangent, [at every point].",
                 m.AnimationGroup(m.FadeOut(at_x), m.FadeOut(s_val), m.FadeIn(card, shift=m.UP * 0.15), m.FadeIn(logo)))
        self.wait(1.2)
