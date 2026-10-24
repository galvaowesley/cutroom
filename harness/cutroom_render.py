#!/usr/bin/env python3
"""Static graphics for cutroom: brand-ready HTML templates rendered to PNG, JPG, WebP or PDF in Chrome.

Commands (also `cutroom render ...`):
  presets                                   the named sizes
  new <kind> <folder> [--brand NAME] [--name file]
                                            scaffold an editable template in the brand: social, quote, thumbnail,
                                            poster, infographic, certificate. Copies the brand's tokens, fonts and
                                            logos next to it, so it renders offline and travels as a folder
  <page.html|URL> -o out.png [--size og|story|1080x1350,...] [--scale 2] [--wait 1.5] [--full-page]
                                            render; several sizes at once give out-<size>.png. The page gets
                                            ?w=W&h=H, and templates adapt their layout to the aspect ratio.
                                            .pdf prints with the page's @page size (posters, certificates)

The size can be a preset name or WxH in px. JPG and WebP need ffmpeg (PNG is converted).
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutroom_brand  # noqa: E402

PRESETS = {
    "instagram-post": (1080, 1080, "Instagram/Threads square post"),
    "instagram-portrait": (1080, 1350, "Instagram 4:5 post, highest feed reach"),
    "story": (1080, 1920, "Stories, Reels, TikTok, Shorts covers (9:16)"),
    "og": (1200, 630, "Open Graph link preview (sites, Slack, LinkedIn links)"),
    "x-post": (1600, 900, "X/Twitter in-feed image (16:9)"),
    "linkedin-post": (1200, 1200, "LinkedIn square post"),
    "linkedin-banner": (1584, 396, "LinkedIn profile or page banner"),
    "youtube-thumb": (1280, 720, "YouTube thumbnail"),
    "youtube-banner": (2560, 1440, "YouTube channel art (safe area in the center 1546x423)"),
    "slide": (1920, 1080, "Full HD slide or video frame"),
    "github-social": (1280, 640, "GitHub repository social preview"),
    "a4": (794, 1123, "A4 portrait at 96 dpi (PDF uses @page A4)"),
    "a3": (1123, 1587, "A3 portrait at 96 dpi"),
    "letter": (816, 1056, "US Letter portrait at 96 dpi"),
    "certificate": (1123, 794, "A4 landscape"),
}
KINDS = ["social", "quote", "thumbnail", "poster", "infographic", "certificate"]


def size_of(s):
    if s in PRESETS:
        return PRESETS[s][0], PRESETS[s][1]
    try:
        w, h = s.lower().split("x")
        return int(w), int(h)
    except ValueError:
        raise SystemExit(f"unknown size {s!r}: use a preset (`cutroom render presets`) or WxH")


def render(page, output, sizes=("og",), scale=1.0, wait=1.5, full_page=False):
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    url = page if "://" in page else Path(page.split("?")[0]).resolve().as_uri() + ("?" + page.split("?", 1)[1] if "?" in page else "")
    done = []
    for s in sizes:
        w, h = size_of(s)
        target = out if len(sizes) == 1 else out.with_name(f"{out.stem}-{s}{out.suffix}")
        q = ("&" if "?" in url else "?") + f"w={w}&h={h}"
        hh = h
        if target.suffix.lower() == ".pdf":
            cutroom_brand.chrome_run(["--no-pdf-header-footer", f"--virtual-time-budget={int(wait * 1000)}",
                                      f"--print-to-pdf={target}", url + q], timeout=180)
        else:
            png = target if target.suffix.lower() == ".png" else Path(tempfile.mkdtemp()) / "x.png"
            hh = h
            if full_page:  # measure the page height first
                dom = cutroom_brand.chrome_run(["--dump-dom", f"--window-size={w},{h}", f"--virtual-time-budget={int(wait * 1000)}",
                                                url + q + "&measure=1"])
                import re
                m = re.search(r'data-height="(\d+)"', dom)
                hh = int(m.group(1)) if m else h
            cutroom_brand.chrome_run([f"--screenshot={png}", f"--window-size={w},{hh}", f"--force-device-scale-factor={scale}",
                                      f"--virtual-time-budget={int(wait * 1000)}", url + q], timeout=180)
            if png != target:
                if not shutil.which("ffmpeg"):
                    raise SystemExit("ffmpeg is needed for JPG/WebP: install it, or write .png")
                extra = ["-q:v", "2"] if target.suffix.lower() in (".jpg", ".jpeg") else ["-quality", "90"]
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(png), *extra, str(target)], check=True)
        done.append(target)
        print(f"{target}  ({w}x{hh if target.suffix.lower() != '.pdf' else h}{f' @{scale:g}x' if scale != 1 else ''})")
    return done


# --- templates -----------------------------------------------------------------------------------

BASE_CSS = """
@import url("brand/tokens.css");
@import url("brand/fonts.css");
* { box-sizing: border-box; margin: 0; }
html, body { width: 100%; height: 100%; }
body { font-family: var(--font-text); color: var(--text); background: var(--background);
  -webkit-print-color-adjust: exact; print-color-adjust: exact; container-type: size; overflow: hidden; }
.frame { position: absolute; inset: 0; container-type: size; }
.display { font-family: var(--font-display); }
.eyebrow { font: 600 max(14px, 2.2cqmin)/1 var(--font-display); letter-spacing: .1em; text-transform: uppercase; }
.logo { height: max(26px, 5cqmin); width: auto; display: block; }
"""

ADAPT_JS = """
<script>
// Templates read ?w=&h= (the render size) and tag the body with its shape: wide, square or tall.
(function () {
  var q = new URLSearchParams(location.search), w = +q.get('w') || innerWidth, h = +q.get('h') || innerHeight, r = w / h;
  document.body.dataset.shape = r > 1.25 ? 'wide' : (r < 0.8 ? 'tall' : 'square');
  if (q.get('measure')) {
    var f = document.querySelector('.frame'), b = f ? f.getBoundingClientRect().bottom : document.body.scrollHeight;
    document.body.setAttribute('data-height', Math.ceil(b));
  }
})();
</script>
"""

TEMPLATES = {
    "social": """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Social card</title><style>
{base}
body {{ background: var(--primary); color: var(--on-primary); }}
.frame {{ padding: 7cqmin; display: grid; grid-template-rows: auto 1fr auto; }}
.frame::after {{ content: ""; position: absolute; right: -30cqmin; bottom: -36cqmin; width: 95cqmin; height: 95cqmin; border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 45%, transparent) 0%, transparent 70%); }}
.eyebrow {{ opacity: .8; position: relative; z-index: 1; }}
main {{ align-self: center; position: relative; z-index: 1; display: grid; gap: 3cqmin; max-width: 92cqw; }}
h1 {{ font: 600 9cqmin/1.04 var(--font-display); letter-spacing: -.025em; text-wrap: balance; }}
.stat {{ font: 300 16cqmin/1 var(--font-display); letter-spacing: -.03em; }}
.stat small {{ display: block; font: 400 3.2cqmin/1.35 var(--font-text); letter-spacing: 0; opacity: .88; margin-top: 1.5cqmin; max-width: 70cqw; }}
p.lead {{ font: 300 4cqmin/1.3 var(--font-display); opacity: .92; max-width: 80cqw; }}
footer {{ display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; font-size: max(14px, 2.4cqmin); opacity: .9; }}
body[data-shape="wide"] main {{ grid-template-columns: 1.3fr 1fr; align-items: end; gap: 6cqw; max-width: none; }}
body[data-shape="tall"] h1 {{ font-size: 11cqmin; }}
</style></head><body><div class="frame">
<p class="eyebrow">EYEBROW · TOPIC</p>
<main><div><h1>The headline states the finding, with its number</h1><p class="lead" style="margin-top:2.5cqmin">One supporting line, quiet.</p></div>
<div class="stat">85.5%<small>what the number is, against its reference</small></div></main>
<footer><img class="logo" src="brand/logos/LOGO_ON_PRIMARY" alt=""><span>source · period</span></footer>
</div>{adapt}</body></html>""",
    "quote": """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Quote card</title><style>
{base}
body {{ background: var(--deep); color: var(--on-deep); }}
.frame {{ padding: 8cqmin; display: grid; grid-template-rows: 1fr auto; }}
blockquote {{ align-self: center; font: 600 7.2cqmin/1.18 var(--font-display); letter-spacing: -.015em; text-wrap: balance; }}
blockquote::before {{ content: "“"; display: block; color: var(--accent); font-size: 22cqmin; line-height: .7; margin-bottom: 1cqmin; }}
footer {{ display: flex; justify-content: space-between; align-items: end; gap: 4cqmin; }}
.who b {{ display: block; font: 600 3.4cqmin/1.2 var(--font-display); }}
.who span {{ font-size: 2.8cqmin; color: var(--accent-soft); }}
</style></head><body><div class="frame">
<blockquote>A sentence worth repeating, quoted exactly as it was said.</blockquote>
<footer><div class="who"><b>Name Surname</b><span>Role · context and date</span></div><img class="logo" src="brand/logos/LOGO_ON_DEEP" alt=""></footer>
</div>{adapt}</body></html>""",
    "thumbnail": """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Thumbnail</title><style>
{base}
body {{ background: var(--deep); color: var(--on-deep); }}
.frame {{ padding: 6cqmin; display: grid; grid-template-columns: 1.25fr 1fr; gap: 5cqw; align-items: center; }}
h1 {{ font: 800 12cqmin/.98 var(--font-display); letter-spacing: -.035em; text-transform: none; }}
h1 em {{ font-style: normal; color: var(--accent); }}
.visual {{ aspect-ratio: 1; border-radius: calc(var(--radius) * 2); background: var(--primary); display: grid; place-items: center;
  color: var(--on-primary); font: 300 22cqmin/1 var(--font-display); box-shadow: 0 0 0 1.2cqmin color-mix(in srgb, var(--accent) 80%, transparent); }}
.tag {{ position: absolute; left: 6cqmin; bottom: 5cqmin; }}
body[data-shape="tall"] .frame {{ grid-template-columns: 1fr; align-content: center; }}
</style></head><body><div class="frame">
<h1>Three words, <em>one</em> idea</h1><div class="visual">f′(x)</div>
<img class="logo tag" src="brand/logos/LOGO_ON_DEEP" alt="">
</div>{adapt}</body></html>""",
    "poster": """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Poster</title><style>
{base}
@page {{ size: A4; margin: 0; }}
.frame {{ padding: 9cqw 8cqw 7cqw; display: grid; grid-template-rows: auto auto 1fr auto; gap: 4cqh; }}
.band {{ background: var(--primary); color: var(--on-primary); margin: -9cqw -8cqw 0; padding: 9cqw 8cqw 6cqw; display: grid; gap: 3cqw; }}
.band .eyebrow {{ opacity: .8; }}
h1 {{ font: 600 9cqw/1.03 var(--font-display); letter-spacing: -.025em; text-wrap: balance; }}
.lead {{ font: 300 3.6cqw/1.35 var(--font-display); color: var(--text-muted); }}
.facts {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 3cqw; align-content: start; }}
.facts div {{ border-top: 2px solid var(--primary); padding-top: 2cqw; }}
.facts b {{ display: block; font: 300 7cqw/1 var(--font-display); color: var(--primary); }}
.facts span {{ font-size: 2.2cqw; line-height: 1.4; color: var(--text-muted); }}
footer {{ display: flex; justify-content: space-between; align-items: end; font-size: 2cqw; color: var(--text-muted);
  border-top: 1px solid var(--border); padding-top: 2cqw; }}
</style></head><body><div class="frame">
<div class="band"><p class="eyebrow">EVENT · DATE · PLACE</p><h1>Poster title that says what happens and why it matters</h1></div>
<p class="lead">A short paragraph: who it is for, what they will leave with, and how to join.</p>
<div class="facts"><div><b>3</b><span>first fact, with its unit</span></div><div><b>45 min</b><span>second fact</span></div><div><b>Free</b><span>third fact</span></div></div>
<footer><span>where to find more · link</span><img class="logo" src="brand/logos/LOGO_ON_LIGHT" alt=""></footer>
</div>{adapt}</body></html>""",
    "infographic": """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Infographic</title><style>
{base}
body {{ overflow: visible; height: auto; container-type: normal; }}
html, body {{ height: auto; }}
.frame {{ position: relative; container-type: normal; padding: 88px 84px 72px; display: grid; gap: 60px; }}
header {{ display: grid; gap: 20px; }}
header .eyebrow {{ color: var(--primary); font-size: 18px; }}
h1 {{ font: 600 86px/1.02 var(--font-display); letter-spacing: -.025em; text-wrap: balance; }}
.lead {{ font: 300 34px/1.3 var(--font-display); color: var(--text-muted); }}
.row {{ display: grid; grid-template-columns: 290px 1fr; gap: 44px; align-items: center; border-top: 1px solid var(--border); padding-top: 52px; }}
.row b {{ font: 300 104px/1 var(--font-display); color: var(--primary); letter-spacing: -.03em; }}
.row h2 {{ font: 600 36px/1.15 var(--font-display); margin-bottom: 10px; }}
.row p {{ font-size: 25px; line-height: 1.45; color: var(--text-muted); }}
.bar {{ height: 18px; border-radius: 9px; background: var(--n200); margin-top: 20px; overflow: hidden; }}
.bar i {{ display: block; height: 100%; background: var(--primary); }}
footer {{ display: flex; justify-content: space-between; align-items: center; color: var(--text-muted); font-size: 20px; border-top: 1px solid var(--border); padding-top: 32px; }}
footer .logo {{ height: 34px; }}
</style></head><body><div class="frame">
<header><p class="eyebrow">TOPIC · PERIOD</p><h1>Infographic title with the main number</h1><p class="lead">What was measured, on whom, when.</p></header>
<div class="row"><b>62%</b><div><h2>First finding</h2><p>The sentence that explains it, compared with a reference.</p><div class="bar"><i style="width:62%"></i></div></div></div>
<div class="row"><b>1 in 4</b><div><h2>Second finding</h2><p>The sentence that explains it.</p><div class="bar"><i style="width:25%"></i></div></div></div>
<div class="row"><b>3.1x</b><div><h2>Third finding</h2><p>The sentence that explains it.</p></div></div>
<footer><span>Source: … · period</span><img class="logo" src="brand/logos/LOGO_ON_LIGHT" alt=""></footer>
</div>{adapt}</body></html>""",
    "certificate": """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Certificate</title><style>
{base}
@page {{ size: A4 landscape; margin: 0; }}
.frame {{ padding: 6cqh; }}
.border {{ position: absolute; inset: 3.2cqh; border: 2px solid var(--primary); border-radius: var(--radius); }}
.inner {{ position: relative; height: 100%; display: grid; grid-template-rows: auto 1fr auto; padding: 6cqh 8cqw; text-align: center; }}
.inner .eyebrow {{ color: var(--primary); }}
.mid {{ align-self: center; display: grid; gap: 3cqh; }}
.mid p {{ font-size: 2.6cqh; color: var(--text-muted); }}
h1 {{ font: 600 9cqh/1.05 var(--font-display); letter-spacing: -.02em; }}
h2 {{ font: 300 4.4cqh/1.2 var(--font-display); color: var(--primary); }}
footer {{ display: flex; justify-content: space-between; align-items: end; font-size: 2.2cqh; color: var(--text-muted); text-align: left; }}
footer .sig {{ border-top: 1px solid var(--text); padding-top: 1cqh; min-width: 28cqw; }}
</style></head><body><div class="frame"><div class="border"></div><div class="inner">
<p class="eyebrow">CERTIFICATE OF COMPLETION</p>
<div class="mid"><p>This certifies that</p><h1>Full Name</h1><p>completed</p><h2>Course or program name · 12 hours</h2></div>
<footer><div class="sig">Signer name<br>Role</div><img class="logo" src="brand/logos/LOGO_ON_LIGHT" alt=""><div class="sig" style="text-align:right">Date<br>Place</div></footer>
</div></div>{adapt}</body></html>""",
}


def scaffold(kind, folder, brand=None, name=None):
    if kind not in TEMPLATES:
        raise SystemExit(f"unknown kind {kind!r}: {', '.join(KINDS)}")
    m = cutroom_brand.load(brand)
    cutroom_brand.build(m)
    d = Path(folder)
    b = d / "brand"
    if b.exists():
        shutil.rmtree(b)
    (b / "logos").mkdir(parents=True)
    src = Path(m["dir"])
    for f in ("tokens.css", "fonts.css"):
        shutil.copy2(src / f, b / f)
    if (src / "fonts").is_dir():
        shutil.copytree(src / "fonts", b / "fonts")
    for v in m["logos"].values():
        if v and (src / v).exists():
            shutil.copy2(src / v, b / "logos" / Path(v).name)
    html = TEMPLATES[kind].format(base=BASE_CSS, adapt=ADAPT_JS)
    html = html.replace("LOGO_ON_PRIMARY", Path(m["logos"].get("on_primary") or "none.svg").name)
    html = html.replace("LOGO_ON_DEEP", Path(m["logos"].get("on_deep") or "none.svg").name)
    html = html.replace("LOGO_ON_LIGHT", Path(m["logos"].get("on_light") or "none.svg").name)
    html = html.replace('<html lang="en">', f'<html lang="{m.get("language", "en")}">')
    page = d / f"{name or kind}.html"
    page.write_text(html, encoding="utf-8")
    return page


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["presets"]:
        for k, (w, h, what) in PRESETS.items():
            print(f"{k:<20} {w:>5} x {h:<5} {what}")
        return 0
    if argv[:1] == ["new"]:
        ap = argparse.ArgumentParser(prog="cutroom render new")
        ap.add_argument("kind", choices=KINDS)
        ap.add_argument("folder")
        ap.add_argument("--brand")
        ap.add_argument("--name")
        a = ap.parse_args(argv[1:])
        p = scaffold(a.kind, a.folder, a.brand, a.name)
        print(f"{p}\nEdit the text, then: cutroom render {p} -o out/{a.name or a.kind}.png --size <preset>")
        return 0
    ap = argparse.ArgumentParser(prog="cutroom render", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--size", default="og", help="preset or WxH; comma-separated for several")
    ap.add_argument("--scale", type=float, default=1.0, help="device scale factor (2 = retina)")
    ap.add_argument("--wait", type=float, default=1.5, help="seconds for fonts and scripts to settle")
    ap.add_argument("--full-page", action="store_true", help="grow the height to the page content (infographics)")
    a = ap.parse_args(argv)
    render(a.page, a.output, [s.strip() for s in a.size.split(",")], a.scale, a.wait, a.full_page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
