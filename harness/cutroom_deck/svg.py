"""SVG primitives. Default colors come from the active theme (theme.active())."""
from .fmt import esc
from .theme import active


def svg(w, h, body, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def text(x, y, s, size=14, fill=None, anchor="start", weight=400, family=None, extra=""):
    """SVG text. family=None uses the text font; "display" the title font; "mono" the code font. s is escaped."""
    t = active()
    fam = {None: t.font_text, "display": t.font_display, "mono": t.font_mono}.get(family, family)
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill or t.n700}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')


def line(x1, y1, x2, y2, stroke=None, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke or active().n200}" '
            f'stroke-width="{width}"{d} stroke-linecap="round"/>')


def rect(x, y, w, h, fill=None, rx=0, stroke="", stroke_width=1):
    s = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(0, w):.1f}" height="{max(0, h):.1f}" rx="{rx}" fill="{fill or active().primary}"{s}/>'


def circle(cx, cy, r, fill=None, stroke="", stroke_width=2):
    s = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill or active().primary}"{s}/>'


def path(d, stroke=None, width=2, fill="none", dash=""):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke or active().primary}" stroke-width="{width}"{ds} '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def mix(a, b, t):
    """Interpolate two hex colors: t=0 gives a, t=1 gives b."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    t = max(0.0, min(1.0, t))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def ordinal(i, n):
    """Theme scale color for item i of n (0 = lightest)."""
    sc = active().scale
    if n <= 1:
        return sc[-1]
    return mix(sc[1], sc[-1], i / (n - 1))


def readable(color):
    """White or dark text, whichever reads on the given background."""
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#FFFFFF" if lum < 0.6 else active().n900
