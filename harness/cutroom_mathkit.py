"""Building blocks for cutroom-math scenes (ManimGX): the dynamic, vertical, no-occlusion style.

`import cutroom_mathkit as kit` inside a scene (the `manimgx` shortcut already has the harness on PYTHONPATH).
Everything here is alpha-driven or a plain function: nothing relies on a FadeIn inside a Succession, which
ManimGX can start early. `examples/math-gradient-descent/src/scene.py` is the worked example.

Captions and labels
    caption(markup, ...)          word objects laid out top-left; *starred* words are highlighted
    cap_swap(old, new)            old caption out, new one in word by word (one animation)
    topic_label(name) / topic_anim(label)
                                  a topic enters, is read for two seconds and leaves: nothing stays pinned
    show_parts(parts, dur)        reveal pieces of an equation (and their labels) one after another

Time and sound
    hop_rate(steps)               rate function that eases in and out of every discrete step
    EventLog                      logs the scene time of every sentence and beat (-> work/events.json),
                                  so sound cues are generated from the scene, not placed by hand

3D without occlusion (see skills/cutroom-math/references/style-and-nuances.md, section 6)
    glide(cam, follow, ...)       the camera frame glides onto a moving point and keeps tracking it
    orbit(cam, dur, theta, phi, zoom)
                                  swing round the figure and close in: every part seen from a clear side
    top_fade(bg)                  strips that fade the mesh out toward the top edge, under the text
    iso_view(...)                 the isometric-from-above camera settings (weak perspective)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import manimgx as m

# ------------------------------------------------------------------------------------------ captions
LEFT = -3.55            # left margin of the text column, in a 8-unit-wide (9:16) frame
WORDS_PER_S = 4.2       # reveal speed of the captions: a little faster than the voice


def caption(markup: str, font: str, color: str, key_color: str, size: int = 36, top: float = 5.6,
            line_height: float = 0.72, max_x: float = 3.75, left: float = LEFT) -> m.VGroup:
    """Word objects of a caption, laid out top-left, wrapped to `max_x`; *starred* words are bold in `key_color`."""
    words, x, line = [], left, 0
    for token in markup.split(" "):
        key = token.startswith("*")
        w = m.Text(token.replace("*", ""), font=font, weight=m.BOLD if key else m.NORMAL, font_size=size,
                   color=key_color if key else color)
        if x + w.width > max_x and x > left:
            x, line = left, line + 1
        w.move_to([x + w.width / 2, top - line_height * line, 0])
        x += w.width + 0.17
        words.append(w)
    return m.VGroup(*words)


def cap_swap(old: m.VGroup | None, new: m.VGroup, words_per_s: float = WORDS_PER_S) -> m.Animation:
    """The old caption fades up and out, then the new one reveals word by word. One alpha-driven animation: the
    captions stay in the scene at opacity 0 (add them with `add_fixed_in_frame_mobjects` and `set_opacity(0)`)."""
    n = len(new)
    t_out = 0.12 if old is not None else 0.0
    t_rev = max(0.7, n / words_per_s)
    total = t_out + t_rev
    base = [w.get_center().copy() for w in new]
    base_old = [w.get_center().copy() for w in old] if old is not None else []
    fade = min(0.28, 0.4 * t_rev)

    def fn(mob, a):
        t = a * total
        if old is not None:
            v = max(0.0, 1.0 - t / t_out)
            for w, b in zip(old, base_old):
                w.set_opacity(v)
                w.move_to(b + 0.18 * m.UP * (1 - v))
        for i, (w, b) in enumerate(zip(new, base)):
            start = t_out + i * (t_rev - fade) / max(1, n - 1)
            v = 1.0 if a >= 1 else min(1.0, max(0.0, (t - start) / fade))
            w.set_opacity(v)
            w.move_to(b + 0.14 * m.UP * (1 - v))

    return m.UpdateFromAlphaFunc(m.VGroup(*([old] if old is not None else []), new), fn, run_time=total, rate_func=m.linear)


def topic_label(name: str, font: str, color: str, y: float = 6.55, size: int = 28, left: float = LEFT) -> m.Text:
    """A transparent label, parked top-left. Add it with `add_fixed_in_frame_mobjects`, opacity 0."""
    lab = m.Text(name, font=font, font_size=size, color=color)
    lab.move_to([left + lab.width / 2, y, 0])
    return lab


def topic_anim(label: m.Text, total: float = 2.0) -> m.Animation:
    """The topic fades in, is read for a moment and leaves."""
    def fn(mob, a):
        s = a * total
        mob.set_opacity(min(1.0, s / 0.3, max(0.0, (total - s) / 0.35)))

    return m.UpdateFromAlphaFunc(label, fn, run_time=total, rate_func=m.linear)


def show_parts(parts: list, dur: float) -> m.Animation:
    """Reveal parts of an equation (and the labels under them) one after another, as their words are spoken."""
    n = len(parts)

    def fn(mob, a):
        for k, p in enumerate(parts):
            p.set_opacity(1.0 if a >= 1 else min(1.0, max(0.0, (a * dur - k * dur * 0.7 / n) / 0.25)))

    return m.UpdateFromAlphaFunc(m.VGroup(*parts), fn, run_time=dur, rate_func=m.linear)


# ------------------------------------------------------------------------------------------ steps and events
def hop_rate(steps: int):
    """A rate function that eases in and out of each of `steps` discrete steps (one tick per landing)."""
    def rate(t: float) -> float:
        s = t * steps
        k = np.floor(min(s, steps - 1e-9))
        return (k + m.smooth(s - k)) / steps

    return rate


class EventLog:
    """Logs the scene time of every beat. `stamp` is an invisible animation that records the time at which its span
    starts (put it in a say span); `dump` writes work/events.json for the cue generator."""

    def __init__(self, scene, path: Path | str):
        self.scene, self.path, self.events = scene, Path(path), []

    def ev(self, name: str, **kw) -> None:
        t = round(float(self.scene.time), 3)
        self.events.append({"t": t, "name": name, **kw})
        print(f"[t={t:6.2f}] {name} {kw or ''}")

    def stamp(self, name: str, **kw) -> m.Animation:
        mk = m.Dot(radius=0.001, fill_opacity=0, stroke_opacity=0)
        fired = {"v": False}

        def fn(mob, alpha):
            if not fired["v"]:
                fired["v"] = True
                self.ev(name, **kw)

        return m.UpdateFromAlphaFunc(mk, fn, run_time=0.05)

    def dump(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.events, indent=1))


# ------------------------------------------------------------------------------------------ 3D without occlusion
def iso_view(phi: float = 52.0, theta: float = -45.0, zoom: float = 0.62, focal_distance: float = 45.0) -> dict:
    """Isometric-from-above settings: a long focal distance gives weak perspective. Use with `orbit`/`move_camera`."""
    return dict(phi=phi * m.DEGREES, theta=theta * m.DEGREES, zoom=zoom, focal_distance=focal_distance)


def glide(cam, follow, dur: float, zoff: float = 2.4, aim=None, w_aim: float = 0.0, ease_frac: float = 0.5) -> m.Animation:
    """The camera frame glides onto the point returned by `follow()` (a callable giving a 3D point, e.g. the
    ball's center) and keeps tracking it. `aim` (a point) pulls the view toward where the point is going by
    `w_aim`. `zoff` raises the look-at point, which puts the subject lower on a vertical screen (room for text)."""
    box = {}

    def fn(frame, a):
        if "c0" not in box:
            box["c0"] = frame.get_center().copy()
        ease = m.smooth(min(1.0, a / ease_frac))
        p = np.asarray(follow(), dtype=float)
        if aim is not None:
            p = (1 - w_aim) * p + w_aim * np.asarray(aim, dtype=float)
        frame.move_to((1 - ease) * box["c0"] + ease * (p + np.array([0.0, 0.0, zoff])))

    return m.UpdateFromAlphaFunc(cam.frame, fn, run_time=dur, rate_func=m.linear)


def orbit(cam, dur: float, theta: float | None = None, phi: float | None = None, zoom: float | None = None,
          focal_distance: float | None = None) -> m.Animation:
    """Turn the figure: the camera swings round it and zooms (angles in degrees), so every part is seen from a side
    where nothing hides it. One move per beat: orbit 60 to 100 degrees over a 3D section, close in x1.5 for arrows."""
    a = []
    for tracker, value, scale in ((cam.theta_tracker, theta, m.DEGREES), (cam.phi_tracker, phi, m.DEGREES),
                                  (cam.zoom_tracker, zoom, 1.0), (cam.focal_distance_tracker, focal_distance, 1.0)):
        if value is not None:
            a.append(tracker.animate(run_time=dur, rate_func=m.smooth).set_value(value * scale))
    return m.AnimationGroup(*a)


def top_fade(bg: str, strips: int = 13, height: float = 0.42, pitch: float = 0.4, top: float = 7.1, width: float = 8.4):
    """Fade the mesh out toward the top edge, under the text. Returns (mask, to): add `mask` with
    `add_fixed_in_frame_mobjects` BEFORE the captions (so the text draws above it), then play `to(level, dur)`."""
    rects = [m.Rectangle(width=width, height=height, stroke_width=0, fill_color=bg, fill_opacity=0.0)
             .move_to([0, top - height / 2 - pitch * k, 0]) for k in range(strips)]
    mask = m.VGroup(*rects)

    def to(level: float, dur: float) -> m.Animation:
        def fn(mob, a):
            for k, r in enumerate(rects):
                r.set_fill(opacity=max(0.0, 1.0 - k / (strips - 2)) * level * (1.0 if a >= 1 else a))

        return m.UpdateFromAlphaFunc(mask, fn, run_time=dur, rate_func=m.linear)

    return mask, to
