import math, sys
sys.argv = sys.argv
from build import word, svg, rr
def ring_half(cx, cy, R, r, a0, a1):
    """Filled ring segment between angles a0..a1 (degrees, ccw), outer R inner r."""
    P = lambda rad, a: (cx + rad * math.cos(math.radians(a)), cy - rad * math.sin(math.radians(a)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = P(R, a0), P(R, a1), P(r, a1), P(r, a0)
    return (f'M{x0:.2f} {y0:.2f}A{R} {R} 0 {large} 0 {x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}'
            f'A{r} {r} 0 {large} 1 {x3:.2f} {y3:.2f}Z')
# A v2 · Splice: three tracks of clips, one slit through all of them (the cut)
def tracks(cut_color=None):
    bars = [(36, 118, 48), (66, 118, 108), (36, 118, 168)]
    rights = [(138, 192, 48), (138, 220, 108), (138, 172, 168)]
    out = "".join(f'<path d="{rr(a, y, b - a, 40, 20)}"/>' for a, b, y in bars + rights)
    if cut_color:
        out += f'<rect x="125" y="30" width="6" height="196" rx="3" fill="{cut_color}"/>'
    return out
A2 = tracks()
# B v2 · Offset c: a heavy c whose lower half slides right, like a spliced take
B2 = (f'<path d="{ring_half(122, 128, 92, 46, 40, 180)}"/>'
      f'<path d="{ring_half(146, 136, 92, 46, 180, 320)}"/>')
open("a2-symbol.svg", "w").write(svg(256, 256, A2))
open("b2-symbol.svg", "w").write(svg(256, 256, B2))
for n, body in (("a2", A2), ("b2", B2)):
    d, end = word("cutroom", 150, 300, 186, -2)
    open(f"{n}-lockup.svg", "w").write(svg(end + 20, 256, body + f'<path d="{d}"/>'))
open("a2-color.svg", "w").write(svg(256, 256, '<g fill="#3B4CCA">' + A2 + '</g><rect x="125" y="22" width="6" height="212" rx="3" fill="#FF6B4A"/>'))
