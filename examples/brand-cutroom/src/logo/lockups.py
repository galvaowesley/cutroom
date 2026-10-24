import json, sys
from pathlib import Path
from build import word, svg
from build2 import ring_half
top = ring_half(122, 128, 92, 46, 40, 180)
bot = ring_half(146, 136, 92, 46, 180, 320)
def mark(fill, dx=3, dy=-4):
    return f'<g transform="translate({dx} {dy})" fill="{fill}"><path d="{top}"/><path d="{bot}"/></g>'
def make(B, font, weight):
    B = Path(B); m = json.load(open(B / "brand.json")); c = m["colors"]
    P, D, T, OP = c["primary"], c["deep"], c["text"], c["on_primary"]
    fpath = str(B / "fonts" / font)
    d, end = word("cutroom", 150, 296, 186, -3, fpath)
    W = end + 24
    lock = lambda mf, tf: svg(W, 256, f"<title>cutroom</title>{mark(mf)}<path d=\"{d}\" fill=\"{tf}\"/>")
    (B / "logos/symbol.svg").write_text(svg(256, 256, f"<title>cutroom</title>{mark(P)}"))
    (B / "logos/symbol-light.svg").write_text(svg(256, 256, f"<title>cutroom</title>{mark(OP)}"))
    (B / "logos/wordmark.svg").write_text(lock(P, T))
    (B / "logos/wordmark-light.svg").write_text(lock(OP, OP))
    (B / "logos/mono.svg").write_text(lock(T, T))
    OD = c.get("on_deep", OP)
    if OD != OP:  # bright primary: deep backgrounds get their own light version
        (B / "logos/wordmark-deep.svg").write_text(lock(P, OD))
        (B / "logos/symbol-deep.svg").write_text(svg(256, 256, f"<title>cutroom</title>{mark(P)}"))
    d2, end2 = word("cutroom", 120, 0, 0, -2.4, fpath)
    w = max(end2, 256)
    (B / "logos/stacked.svg").write_text(svg(w, 416, f'<title>cutroom</title><g transform="translate({(w-256)/2} 0)">{mark(P)}</g>'
        f'<g transform="translate({(w-end2)/2} 398)"><path d="{d2}" fill="{T}"/></g>'))
    (B / "logos/app-icon.svg").write_text(svg(256, 256, f'<title>cutroom</title><rect width="256" height="256" rx="56" fill="{P}"/>'
        f'<g transform="translate(128 128) scale(.74) translate(-128 -128)">{mark(OP)}</g>'))
for name, font in (("electric", "InterTight-600.ttf"), ("hot", "BricolageGrotesque-700.ttf"), ("ultra", "SpaceGrotesk-700.ttf")):
    make(f"{sys.argv[1]}/brands/cutroom-{name}", font, None)
print("logos ok")
