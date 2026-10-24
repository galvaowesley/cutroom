"""Gradient descent, from one weight to two: a 9:16 cutroom-math explainer.

One continuous camera, no cuts. A 3D landscape is sliced into a 2D loss curve; zooming into the curve
turns it into a line (its slope is the gradient); stepping against the slope, three learning rates, and
the curve is swept back into a surface where the same rule works with two slopes.

Zones (fixed on the screen): word-by-word captions, live monospace readouts, the rule. A topic label
enters, is read, and leaves: nothing stays pinned to the top.

Render: manimgx render scene.py GradientDescent -r 1080x1920 --fps 30 -o ../work/raw.mp4
Events (for the sound cues) go to ../work/events.json; make_cues.py turns them into cues.json.
"""
import json
import subprocess
from pathlib import Path

import numpy as np

import manimgx as m
import cutroom_mathkit as kit
from cutroom_voice import manimgx_voice

B = json.loads(subprocess.run(["cutroom", "brand", "show", "--json"], capture_output=True, text=True, check=True).stdout)
C, F = B["colors"], B["fonts"]
BG, INK, DIM = C["deep"], "#F4F3EF", "#B9B4CC"
PINK, YELLOW, MUTED = C["primary"], C["accent"], "#8E929F"
CYAN = "#7FD4FF"
TEXT, MONO = F["text"], F["mono"]
LOGO = Path(B["paths"]["logos"]["on_deep"])
WORK = Path(__file__).resolve().parent.parent / "work"
m.config.background_color = BG

# ----------------------------------------------------------------------------- the math
SX, SZ = 1.15, 0.8          # world units per unit of x (and y), and per unit of loss
PX = 135                    # pixels per world unit at camera zoom 1 (1080 px / 8 units)
X0, Y0 = 2.1, 1.8           # where every run starts
LR_CRAWL, LR_GOOD, LR_BOUNCE = 0.04, 0.25, 1.5
LR_3D = 0.35


def f(x):
    return 0.5 * x**2 + 0.3 * np.cos(2.5 * x)


def df(x):
    return x - 0.75 * np.sin(2.5 * x)


def L(x, y):
    return f(x) + 0.35 * y**2


def gradL(x, y):
    return np.array([df(x), 0.7 * y])


def run_1d(lr, n, x=X0):
    out = [x]
    for _ in range(n):
        x = x - lr * df(x)
        out.append(x)
    return out


def run_3d(lr):
    p, out = np.array([X0, Y0]), []
    out.append(p.copy())
    while np.linalg.norm(gradL(*p)) >= 0.05:
        p = p - lr * gradL(*p)
        out.append(p.copy())
    return out


PATH_3D = run_3d(LR_3D)
STEPS_3D = len(PATH_3D) - 1
END_3D = PATH_3D[-1]

# facts cited in SCRIPT.md
assert STEPS_3D == 12, STEPS_3D
assert abs(df(X0) - 2.744) < 0.001
assert abs(run_1d(LR_BOUNCE, 10)[-1] - 2.05) < 0.05            # bounces between about +2.05 and -2.05
assert abs(run_1d(LR_GOOD, 8)[-1] - 0.73) < 0.02                # settles at the minimum, x = 0.73
assert abs(run_1d(LR_CRAWL, 10)[-1] - 1.24) < 0.02              # still far after 10 steps


def PW(x, y=0.0, lift=0.0):
    """A point of the landscape, in world units (x right, y away from the 2D camera, z up)."""
    return np.array([SX * x, SX * y, SZ * L(x, y) + lift])


# ----------------------------------------------------------------------------- layout and captions
LEFT = kit.LEFT
ZC = 3.9                    # the camera looks at this height: it puts the plot under the text zone
SPEECH = {"cutroom": "cut room"}


def caption(markup):
    """Word objects of a caption, laid out top-left; *starred* words are highlighted."""
    return kit.caption(markup, TEXT, DIM, YELLOW)


class GradientDescent(m.ThreeDScene):
    voice = manimgx_voice("narrator", pronounce=SPEECH)

    def construct(self):
        cam = self.camera
        log = kit.EventLog(self, WORK / "events.json")
        ev, stamp = log.ev, log.stamp

        # ------------------------------------------------------------------ trackers and state
        x0, y0 = m.ValueTracker(X0), m.ValueTracker(Y0)
        pin = m.ValueTracker(0.0)             # 0: curve in place; 1: pinned under the readouts
        lz = m.ValueTracker(0.0)              # log of the 2D zoom
        prog = m.ValueTracker(0.0)            # progress along the current run
        st = {"mode": "2d", "run": False, "dense": [], "steps": 1, "path": None, "lr": LR_GOOD}

        def zoom():
            return float(np.exp(lz.get_value()))

        def slope_s(x):
            return SZ / SX * df(x)

        def centre():
            nat = np.array([SX * x0.get_value(), 0.0, SZ * f(x0.get_value())])
            anchor = np.array([0.0, 0.0, ZC - 2.0])
            return (1 - pin.get_value()) * nat + pin.get_value() * anchor

        def point_at(s):
            p = st["path"]
            i = int(np.floor(min(s, len(p) - 1 - 1e-9)))
            return np.atleast_1d(p[i]) + (np.atleast_1d(p[i + 1]) - np.atleast_1d(p[i])) * (s - i)

        def drive(tr, axis):
            def upd(t):
                if st["run"]:
                    q = point_at(prog.get_value())
                    if axis < len(q):
                        t.set_value(float(q[axis]))
            tr.add_updater(upd)

        drive(x0, 0)
        drive(y0, 1)

        def on_run(q):
            q = np.atleast_1d(q)
            if len(q) == 1:
                return PW(q[0], 0.0, 0.05) + np.array([0, -0.04, 0])
            return PW(q[0], q[1], 0.05)

        def start_run(path, color):
            st["run"], st["path"], st["steps"] = True, path, len(path) - 1
            prog.set_value(0.0)
            dense = []
            for a, b in zip(path[:-1], path[1:]):
                a, b = np.atleast_1d(a), np.atleast_1d(b)
                dense += [on_run(a + (b - a) * (k / 16)) for k in range(16)]
            dense.append(on_run(path[-1]))
            st["dense"] = dense
            trail.set_stroke(color=color, opacity=1)

        def run_anim(duration):
            return prog.animate(run_time=duration, rate_func=kit.hop_rate(st["steps"])).set_value(st["steps"])

        # ------------------------------------------------------------------ the landscape (3D) and its slice (2D)
        surface = m.Surface(lambda u, v: PW(u, v), u_range=(-3, 3), v_range=(-2.4, 2.4), resolution=(44, 36),
                            checkerboard_colors=False, fill_color="#2B1457", fill_opacity=0.10,
                            stroke_color="#B7A8E6", stroke_width=1.2, stroke_opacity=0.75)

        U = 4.7

        def sample_x():
            z = zoom()
            xa = max(-3.0, x0.get_value() - U / (z * SX))
            xb = min(3.0, x0.get_value() + U / (z * SX))
            return np.linspace(xa, xb, 280)

        def curve_xyz(xs):
            z, c, xp = zoom(), centre(), x0.get_value()
            u = z * SX * (xs - xp)
            v = z * SZ * (f(xs) - f(xp))
            return np.stack([c[0] + u, np.full_like(u, -0.02), c[2] + v], axis=1)

        curve = m.VMobject(stroke_color=INK, stroke_width=6, fill_opacity=0)
        curve.set_points_as_corners(curve_xyz(np.linspace(-3, 3, 4)))
        curve.add_updater(lambda mob: mob.set_points_as_corners(curve_xyz(sample_x())))

        tangent = m.VMobject(stroke_color=CYAN, stroke_width=3.5, fill_opacity=0)
        tangent.set_points_as_corners([m.ORIGIN, m.RIGHT])

        def update_tangent(mob):
            c, s = centre(), slope_s(x0.get_value())
            mob.set_points_as_corners([c + np.array([-U, -0.03, -U * s]), c + np.array([U, -0.03, U * s])])

        tangent.add_updater(update_tangent)

        gap = m.VMobject(stroke_width=0, fill_color=CYAN, fill_opacity=0.0)
        gap.set_points_as_corners([m.ORIGIN, m.RIGHT, m.UP])

        def update_gap(mob):
            pts = curve_xyz(sample_x())
            c, s = centre(), slope_s(x0.get_value())
            u = pts[:, 0] - c[0]
            line = np.stack([pts[:, 0], np.full_like(u, -0.01), c[2] + s * u], axis=1)
            mob.set_points_as_corners(list(pts) + list(line[::-1]) + [pts[0]])

        gap.add_updater(update_gap)

        ball = m.Sphere(radius=0.12, checkerboard_colors=False, fill_color=YELLOW, fill_opacity=1)

        def update_ball(mob):
            if st["mode"] == "3d":
                mob.move_to(PW(x0.get_value(), y0.get_value(), 0.11))
            else:
                mob.move_to(centre() + np.array([0, -0.06, 0]))

        ball.add_updater(update_ball)

        trail = m.VMobject(stroke_color=PINK, stroke_width=5, fill_opacity=0)
        trail.set_points_as_corners([m.ORIGIN, m.RIGHT * 0.01])

        def update_trail(mob):
            d = st["dense"]
            if not d:
                return
            n = max(2, min(len(d), int(prog.get_value() / st["steps"] * (len(d) - 1)) + 2))
            mob.set_points_as_corners(list(d[: n - 1]) + [on_run(point_at(prog.get_value()))])

        trail.add_updater(update_trail)

        # the step arrow in the 2D view: a flat polygon in the x-z plane, from the point against the slope
        step_arrow = m.VMobject(stroke_width=0, fill_color=PINK, fill_opacity=0.0)
        step_arrow.set_points_as_corners([m.ORIGIN, m.RIGHT, m.UP])

        def update_step_arrow(mob):
            c = centre()
            length = SX * st["lr"] * df(x0.get_value())      # world length along x, against the slope
            tail = c + np.array([0, -0.08, 0.0])
            d = -np.sign(length) if length else 1.0
            tip = tail + np.array([d * abs(length), 0, 0])
            half, hl, hw = 0.07, min(0.38, abs(length) * 0.45 + 0.02), 0.2
            bx = tip[0] - d * hl
            mob.set_points_as_corners([
                tail + np.array([0, 0, half]), np.array([bx, tail[1], tail[2] + half]),
                np.array([bx, tail[1], tail[2] + hw]), tip,
                np.array([bx, tail[1], tail[2] - hw]), np.array([bx, tail[1], tail[2] - half]),
                tail + np.array([0, 0, -half]), tail + np.array([0, 0, half]),
            ])

        step_arrow.add_updater(update_step_arrow)

        # ------------------------------------------------------------------ fixed on screen: grid, tabs, readouts, rule
        grid = m.VGroup(*[m.Line([x, -7.1, 0], [x, 7.1, 0], stroke_width=1, color=INK, stroke_opacity=0.07) for x in np.arange(-4, 4.1, 0.5)],
                        *[m.Line([-4, y, 0], [4, y, 0], stroke_width=1, color=INK, stroke_opacity=0.07) for y in np.arange(-7, 7.1, 0.5)])

        topic_names = ("slope", "step", "learning rate", "two weights")
        topics = {name: kit.topic_label(name, MONO, INK) for name in topic_names}

        def topic(name):
            """The topic label fades in, is read for a moment and leaves."""
            return kit.topic_anim(topics[name])

        def mono(txt, color=MUTED, size=28):
            return m.Text(txt, font=MONO, font_size=size, color=color)

        def row(label, fn, places, color=INK, unit=""):
            lbl = mono(label)
            number = m.DecimalNumber(0, num_decimal_places=places, font_size=31, color=color)
            parts = [lbl, number] + ([mono(unit)] if unit else [])
            g = m.VGroup(*parts).arrange(m.RIGHT, buff=0.14)
            number.add_updater(lambda mob: mob.set_value(fn()).next_to(lbl, m.RIGHT, buff=0.14))
            if unit:
                parts[2].add_updater(lambda mob: mob.next_to(number, m.RIGHT, buff=0.12))
            return g

        def stack(*rows):
            g = m.VGroup(*rows).arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.15)
            g.move_to([LEFT + g.width / 2, 4.2 - g.height / 2, 0])
            return g

        def off_straight():
            pts = curve_xyz(sample_x())
            c, s = centre(), slope_s(x0.get_value())
            u = pts[:, 0] - c[0]
            return float(np.max(np.abs((pts[:, 2] - c[2]) - s * u)) * PX)

        def cur_step():
            return float(int(round(prog.get_value())))

        def cur_y():
            return y0.get_value() if st["mode"] == "3d" else 0.0

        rows_zoom = stack(row("zoom ×", zoom, 0), row("off straight ", off_straight, 0, YELLOW, " px"))
        rows_slope = stack(row("x ", lambda: x0.get_value(), 2), row("slope ", lambda: df(x0.get_value()), 2, CYAN))
        rows_step = stack(row("step ", cur_step, 0), row("w ", lambda: x0.get_value(), 2), row("slope ", lambda: df(x0.get_value()), 2, CYAN))
        rows_rate = stack(row("lr ", lambda: st["lr"], 2, YELLOW), row("step ", cur_step, 0), row("loss ", lambda: L(x0.get_value(), cur_y()), 3, PINK))
        rows_3d = stack(row("step ", cur_step, 0), row("loss ", lambda: L(x0.get_value(), cur_y()), 3, PINK),
                        row("|∇L| ", lambda: float(np.linalg.norm(gradL(x0.get_value(), cur_y()))), 3, CYAN))

        rule = m.MathTex(r"w_{t+1}", r"=", r"w_t", r"-", r"\mathrm{lr}\,", r"f'(w_t)", color=INK, font_size=50)
        rule[4].set_color(YELLOW)
        rule[5].set_color(CYAN)
        rule.move_to([LEFT + rule.width / 2, 2.4, 0])
        rule_labels = {}
        for idx, text, col, lvl in ((0, "new weight", INK, 0), (2, "old weight", INK, 1), (4, "learning rate", YELLOW, 0), (5, "slope", CYAN, 1)):
            lab = m.Text(text, font=MONO, font_size=22, color=col)
            lab.move_to(rule[idx].get_center() + np.array([0, -0.62 - 0.42 * lvl, 0]))
            rule_labels[idx] = lab

        show_parts = kit.show_parts

        rule_all = m.VGroup(rule, *rule_labels.values())

        rule3d = m.MathTex(r"w_{t+1} = w_t -", r"\mathrm{lr}\,", r"\nabla L(w_t)", color=INK, font_size=50)
        rule3d[1].set_color(YELLOW)
        rule3d[2].set_color(CYAN)
        rule3d.move_to([LEFT + rule3d.width / 2, 2.4, 0])

        mask, mask_to = kit.top_fade(BG)

        logo = m.SVGMobject(str(LOGO), height=0.5).move_to([0, -6.0, 0])

        # ------------------------------------------------------------------ the script, as captions
        S = {
            "a1": "How does a model *learn*?",
            "a2": "It rolls *downhill*.",
            "a3": "Start with *one weight*.",
            "b1": "Zoom into any point, and the curve turns into a *line*.",
            "b2": "Its *slope* is the gradient.",
            "c1": "Step *against* the slope.",
            "r1": "The *new* weight is the *old* weight,",
            "r2": "minus the *learning rate* times the *slope*.",
            "c2": "The flatter the curve, the *smaller* the step.",
            "d1": "Now, change the *learning rate*.",
            "d2": "Too small, and it *crawls*.",
            "d3": "Just right, and it *settles*.",
            "d4": "Too big, and it *overshoots*.",
            "e1": "Add a second weight, and the curve becomes a *surface*.",
            "e2": "Now there are *two slopes*, one per weight.",
            "e3": "Together, they are the *gradient*.",
            "e4": "Step against it: the same rule works in *any dimension*.",
            "f1": "Billions of weights. *One rule.*",
        }
        caps = {k: caption(v) for k, v in S.items()}
        chip_text = {"crawl": ("lr = 0.04 · crawls", MUTED), "good": ("lr = 0.25 · settles", YELLOW), "bounce": ("lr = 1.5 · overshoots", PINK)}
        chips = {k: m.Text(t, font=TEXT, weight=m.BOLD, font_size=46, color=c).move_to([0, -4.3, 0]) for k, (t, c) in chip_text.items()}

        for mob in [grid, rows_zoom, rows_slope, rows_step, rows_rate, rows_3d, rule3d, logo, *chips.values()]:
            self.add_fixed_in_frame_mobjects(mob)
            self.remove(mob)
        self.add_fixed_in_frame_mobjects(mask)   # above the 3D, below the text added after it
        for cap in [*caps.values(), *topics.values(), rule, *rule_labels.values()]:   # captions and topic labels stay in the scene, transparent, driven by alpha
            cap.set_opacity(0)
            self.add_fixed_in_frame_mobjects(cap)

        cur = {"cap": None}

        def say_caps(keys, anims=None):
            """One bracketed span per sentence: the caption reveals word by word next to the sentence's own animation."""
            anims = anims or {}
            spans = []
            for k in keys:
                spans.append(m.AnimationGroup(stamp("cap", key=k), kit.cap_swap(cur["cap"], caps[k]), *([anims[k]] if k in anims else [])))
                cur["cap"] = caps[k]
            self.say(" ".join(f"[{S[k].replace('*', '')}]" for k in keys), *spans)

        # ------------------------------------------------------------------ camera
        self.set_camera_orientation(phi=72 * m.DEGREES, theta=-125 * m.DEGREES, zoom=0.9)
        cam.frame.move_to(np.array([0.0, 1.5, ZC - 1.0]))

        # ================================================================== 1. hook: the landscape, then its slice
        ev("scene", which="hook")
        self.add(curve, ball)
        curve.set_stroke(opacity=0)
        ball.set_opacity(0)
        say_caps(["a1", "a2", "a3"], {
            "a1": m.AnimationGroup(m.FadeIn(surface, run_time=1.8),
                                   cam.theta_tracker.animate(run_time=4.2, rate_func=m.smooth).set_value(-62 * m.DEGREES),
                                   cam.phi_tracker.animate(run_time=4.2, rate_func=m.smooth).set_value(66 * m.DEGREES)),
            "a2": m.AnimationGroup(ball.animate(run_time=0.5).set_opacity(1), curve.animate(run_time=1.2).set_stroke(opacity=1)),
            "a3": m.AnimationGroup(m.FadeOut(surface, run_time=1.2),
                                   cam.frame.animate(run_time=1.6, rate_func=m.smooth).move_to(np.array([0.0, 0.0, ZC])),
                                   cam.phi_tracker.animate(run_time=1.6, rate_func=m.smooth).set_value(90 * m.DEGREES),
                                   cam.theta_tracker.animate(run_time=1.6, rate_func=m.smooth).set_value(-90 * m.DEGREES),
                                   cam.zoom_tracker.animate(run_time=1.6, rate_func=m.smooth).set_value(1.0),
                                   m.FadeIn(grid, run_time=1.6)),
        })

        # ================================================================== 2. zoom until it is a line; its slope
        ev("scene", which="zoom")
        self.add(tangent, gap)
        tangent.set_stroke(opacity=0)
        gap.set_fill(opacity=0)
        say_caps(["b1", "b2"], {
            "b1": m.AnimationGroup(
                topic("slope"),
                m.FadeIn(rows_zoom),
                tangent.animate(run_time=0.8).set_stroke(opacity=1),
                gap.animate(run_time=0.8).set_fill(opacity=0.24),
                pin.animate(run_time=1.4, rate_func=m.smooth).set_value(1.0),
                lz.animate(run_time=4.4, rate_func=m.linear).set_value(np.log(1600))),
            "b2": m.FadeOut(rows_zoom, run_time=0.25),
        })
        ev("zoom_end")

        # zoom back out, and slide the point along the curve: the slope changes sign
        self.play(m.FadeIn(rows_slope, run_time=0.4), lz.animate(run_time=1.0, rate_func=m.smooth).set_value(0.0),
                  pin.animate(run_time=1.0, rate_func=m.smooth).set_value(0.0),
                  gap.animate(run_time=0.6).set_fill(opacity=0.0))
        ev("slide")
        self.play(x0.animate(run_time=1.7, rate_func=m.smooth).set_value(-1.0))
        self.play(x0.animate(run_time=0.9, rate_func=m.smooth).set_value(X0), m.FadeOut(rows_slope, run_time=0.4))

        # ================================================================== 3. step against the slope
        ev("scene", which="step")
        self.add(step_arrow)
        step_arrow.set_fill(opacity=0)
        start_run(run_1d(LR_GOOD, 8), PINK)
        self.add(trail)
        trail.set_stroke(opacity=0)
        st["lr"] = LR_GOOD
        say_caps(["c1", "r1", "r2", "c2"], {
            "c1": m.AnimationGroup(topic("step"), step_arrow.animate(run_time=0.5).set_fill(opacity=0.95),
                                   trail.animate(run_time=0.4).set_stroke(opacity=1)),
            "r1": show_parts([rule[0], rule[1], rule_labels[0], rule[2], rule_labels[2]], 1.5),
            "r2": show_parts([rule[3], rule[4], rule_labels[4], rule[5], rule_labels[5]], 1.9),
            "c2": m.AnimationGroup(m.FadeIn(rows_step, run_time=0.4), run_anim(3.4)),
        })
        ev("run_end", which="good")

        # ================================================================== 4. learning rate: three runs
        ev("scene", which="rate")
        self.play(m.FadeOut(step_arrow, run_time=0.4), m.FadeOut(rows_step, run_time=0.4),
                  m.FadeOut(tangent, run_time=0.4), m.FadeOut(trail, run_time=0.4))
        st["run"] = False
        x0.set_value(X0)
        st["dense"] = []
        trail.set_points_as_corners([m.ORIGIN, m.RIGHT * 0.01])
        say_caps(["d1"], {"d1": m.AnimationGroup(topic("learning rate"), m.FadeOut(rule_all, run_time=0.3), m.FadeIn(rows_rate))})

        for i, (key, tag, lr, n, dur) in enumerate([("d2", "crawl", LR_CRAWL, 10, 2.3), ("d3", "good", LR_GOOD, 6, 1.8), ("d4", "bounce", LR_BOUNCE, 10, 2.5)]):
            if i > 0:
                self.play(m.FadeOut(chips[prev], run_time=0.25), m.FadeOut(trail, run_time=0.25))
                st["run"] = False
                x0.set_value(X0)
            st["lr"] = lr
            start_run(run_1d(lr, n), {"crawl": MUTED, "good": YELLOW, "bounce": PINK}[tag])
            self.add(trail)
            ev("run", which=tag, lr=lr, steps=n, dur=dur)
            say_caps([key], {key: m.AnimationGroup(m.FadeIn(chips[tag], shift=0.2 * m.UP), run_anim(dur))})
            ev("run_end", which=tag)
            prev = tag

        # ================================================================== 5. one more weight: the curve sweeps into a surface
        ev("scene", which="surface")
        self.play(m.FadeOut(chips["bounce"], run_time=0.3), m.FadeOut(trail, run_time=0.3), m.FadeOut(grid, run_time=0.8), m.FadeOut(rows_rate, run_time=0.3))
        st["run"], st["mode"] = False, "3d"
        x0.set_value(X0)
        y0.set_value(0.0)
        slice_x = m.VMobject(stroke_color=CYAN, stroke_width=4.5, fill_opacity=0)
        slice_y = m.VMobject(stroke_color=YELLOW, stroke_width=4.5, fill_opacity=0)
        for mob, axis in ((slice_x, 0), (slice_y, 1)):
            mob.set_points_as_corners([m.ORIGIN, m.RIGHT * 0.01])
            mob.add_updater(lambda mb, axis=axis: mb.set_points_as_corners(
                [PW(t, y0.get_value(), 0.04) for t in np.linspace(-3, 3, 120)] if axis == 0 else
                [PW(x0.get_value(), t, 0.04) for t in np.linspace(-2.4, 2.4, 120)]))

        def tangent_line(axis, color):
            line = m.VMobject(stroke_color=color, stroke_width=3.5, fill_opacity=0)
            line.set_points_as_corners([m.ORIGIN, m.RIGHT * 0.01])

            def upd(mob):
                x, y = x0.get_value(), y0.get_value()
                g = gradL(x, y)
                d = np.array([SX, 0, SZ * g[0]]) if axis == 0 else np.array([0, SX, SZ * g[1]])
                d = d / np.linalg.norm(d)
                p = PW(x, y, 0.05)
                mob.set_points_as_corners([p - 1.3 * d, p + 1.3 * d])

            line.add_updater(upd)
            return line

        tan_x, tan_y = tangent_line(0, CYAN), tangent_line(1, YELLOW)
        guides = (slice_x, slice_y, tan_x, tan_y)
        for mob in guides:
            mob.set_stroke(opacity=0)

        overview = np.array([0.0, 0.0, ZC + 1.6])
        end_pt = PW(END_3D[0], END_3D[1], 0.0)

        def glide(dur, zoff, w_end=0.0, ease_frac=0.5):
            return kit.glide(cam, ball.get_center, dur, zoff, aim=end_pt, w_aim=w_end, ease_frac=ease_frac)

        def orbit(dur, **kw):
            return kit.orbit(cam, dur, **kw)

        say_caps(["e1"], {"e1": m.AnimationGroup(
            m.FadeIn(surface, run_time=2.4),
            cam.phi_tracker.animate(run_time=3.0, rate_func=m.smooth).set_value(52 * m.DEGREES),
            cam.theta_tracker.animate(run_time=3.0, rate_func=m.smooth).set_value(-45 * m.DEGREES),
            cam.zoom_tracker.animate(run_time=3.0, rate_func=m.smooth).set_value(0.62),
            cam.focal_distance_tracker.animate(run_time=3.0, rate_func=m.smooth).set_value(45.0),
            cam.frame.animate(run_time=3.0, rate_func=m.smooth).move_to(np.array([0.0, 0.0, ZC + 1.6])),
            mask_to(1.0, 2.5),
            topic("two weights"),
            ball.animate(run_time=1.0).scale(1.5))})

        self.add(*guides)
        say_caps(["e2"], {"e2": m.AnimationGroup(
            y0.animate(run_time=1.6, rate_func=m.smooth).set_value(Y0),
            glide(2.6, 2.4), orbit(2.6, theta=-72, phi=50, zoom=0.95),
            m.Succession(m.Wait(0.8), m.AnimationGroup(*[mob.animate(run_time=0.6).set_stroke(opacity=1) for mob in guides])))})

        g0 = gradL(X0, Y0)
        up = np.array([SX * g0[0], SX * g0[1], SZ * float(g0 @ g0)])
        up = up / np.linalg.norm(up)
        p0 = PW(X0, Y0, 0.12)
        arrow = m.Arrow3D(p0, p0 + 1.8 * up, color=PINK, thickness=0.06, height=0.42, base_radius=0.14)
        normal = np.cross(np.array([SX, 0, SZ * g0[0]]), np.array([0, SX, SZ * g0[1]]))
        normal = normal / np.linalg.norm(normal)
        say_caps(["e3"], {"e3": m.AnimationGroup(m.FadeIn(arrow, run_time=0.8), m.FadeIn(rule3d, shift=0.2 * m.UP),
                                                glide(1.9, 2.2), orbit(1.9, theta=-100, phi=50, zoom=1.5))})

        st["path"], st["steps"] = PATH_3D, STEPS_3D
        say_caps(["e4"], {"e4": m.AnimationGroup(
            m.Rotate(arrow, angle=m.PI, axis=normal, about_point=p0, run_time=0.9),
            glide(3.0, 2.2), orbit(3.0, theta=-135, phi=47, zoom=1.5),
            m.Succession(m.Wait(1.2), m.AnimationGroup(*[mob.animate(run_time=0.4).set_stroke(opacity=0) for mob in guides],
                                                    m.FadeOut(arrow, run_time=0.4))))})

        # the descent on the surface
        start_run(PATH_3D, PINK)
        self.add(trail)
        ev("descent3d")
        self.play(m.FadeIn(rows_3d, run_time=0.5), m.FadeOut(rule3d, run_time=0.4), run_anim(3.3),
                  glide(3.3, 3.2, w_end=0.3, ease_frac=0.2), orbit(3.3, theta=-170, phi=46, zoom=1.15))
        ev("min3d")

        # ================================================================== 6. close
        say_caps(["f1"], {"f1": m.AnimationGroup(
            cam.theta_tracker.animate(run_time=2.4, rate_func=m.smooth).set_value(-225 * m.DEGREES),
            cam.zoom_tracker.animate(run_time=2.4, rate_func=m.smooth).set_value(0.62),
            cam.frame.animate(run_time=2.4, rate_func=m.smooth).move_to(overview),
            m.FadeOut(rows_3d, run_time=0.5))})
        self.play(m.FadeOut(cur["cap"], run_time=0.35), m.FadeIn(logo, run_time=0.6))
        ev("close")
        self.wait(0.15)
        ev("end")
        log.dump()
