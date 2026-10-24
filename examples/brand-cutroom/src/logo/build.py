import math, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
FONT = sys.argv[1]
def word(text, size, x0, baseline, tracking=0, font=FONT):
    f = TTFont(font); gs = f.getGlyphSet(); cmap = f.getBestCmap(); s = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs); x = x0
    for ch in text:
        g = cmap[ord(ch)]; gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline))); x += f["hmtx"][g][0] * s + tracking
    return pen.getCommands(), x
def svg(w, h, body): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}">{body}</svg>\n'
def arc(cx, cy, r, a0, a1):
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
    (x0, y0), (x1, y1) = p(a0), p(a1); large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.2f} {y0:.2f}A{r} {r} 0 {large} 0 {x1:.2f} {y1:.2f}"
# A · Splice: two clips on a timeline, cut where the playhead passes
def rr(x, y, w, h, r): return f'M{x+r} {y}H{x+w-r}A{r} {r} 0 0 1 {x+w} {y+r}V{y+h-r}A{r} {r} 0 0 1 {x+w-r} {y+h}H{x+r}A{r} {r} 0 0 1 {x} {y+h-r}V{y+r}A{r} {r} 0 0 1 {x+r} {y}Z'
A = (f'<path d="{rr(36,88,78,40,20)}"/><path d="{rr(146,88,74,40,20)}"/>'
     f'<path d="{rr(36,140,40,40,20)}"/><path d="{rr(108,140,112,40,20)}"/>'
     f'<path d="M120 52h16v152a8 8 0 0 1-16 0z"/><path d="M110 36h36l-18 22z"/>')
# B · Offset c: the letter c split at its middle and nudged, like a spliced take
B = (f'<path d="{arc(128,128,76,38,180)}" fill="none" stroke="#000" stroke-width="44" stroke-linecap="butt"/>'
     f'<g transform="translate(16 0)"><path d="{arc(112,128,76,180,322)}" fill="none" stroke="#000" stroke-width="44" stroke-linecap="butt"/></g>')
# C · Room: crop corners that make a room, one subject inside
def corner(x, y, sx, sy): return f'<path d="M{x} {y+sy*56}V{y}H{x+sx*56}" fill="none" stroke="#000" stroke-width="24" stroke-linejoin="miter" stroke-linecap="butt"/>'
C = corner(40,40,1,1)+corner(216,40,-1,1)+corner(40,216,1,-1)+corner(216,216,-1,-1)+'<circle cx="150" cy="106" r="30"/>'
for n, body in (("a", A), ("b", B), ("c", C)):
    open(f"{n}-symbol.svg", "w").write(svg(256, 256, body))
    d, end = word("cutroom", 150, 300, 186, -2)
    open(f"{n}-lockup.svg", "w").write(svg(end + 20, 256, body + f'<path d="{d}"/>'))
print("ok")
