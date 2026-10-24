"""`deck` command (shortcut in <cutroom home>/bin, also `cutroom deck`): build, check and preview presentations.

  deck build <folder|deck.py>      run src/deck.py and write out/<slug>.pdf and out/<slug>.html (self-contained)
  deck check <folder|deck.html>    layout check in Chrome; exits 1 on problems
  deck preview <folder|deck.html>  PNGs in work/preview/ and the grid in out/<slug>-grid.png

<folder> is the piece folder (`cutroom job`): the script is src/deck.py, outputs go to out/, previews to work/.
Use --brand NAME on build to render the same deck.py in another brand.
"""
import argparse
import os
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from . import chrome  # noqa: E402
from .render import _decks  # noqa: E402
from .theme import Theme, use  # noqa: E402


def _folders(target):
    p = Path(target).resolve()
    if p.is_dir():
        return p / "src" / "deck.py", p / "out", p / "work"
    root = p.parent.parent if p.parent.name in ("src", "out") else p.parent
    return (p if p.suffix == ".py" else root / "src" / "deck.py"), root / "out", root / "work"


def _html(target):
    p = Path(target).resolve()
    if p.suffix == ".html":
        return p, p.parent.parent / "work" if p.parent.name == "out" else p.parent / "work"
    _, out, work = _folders(target)
    pages = sorted(out.glob("*.html"))
    if not pages:
        raise SystemExit(f"no HTML in {out}: run `deck build {target}` first")
    return pages[0], work


def build(a):
    script, out, _ = _folders(a.target)
    if not script.exists():
        raise SystemExit(f"{script} not found")
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(script.parent))
    cwd = os.getcwd()
    if a.brand:
        use(Theme.from_brand(a.brand))
    os.chdir(script.parent)  # relative paths in the script (data in src/ or ../work/) work
    try:
        runpy.run_path(str(script), run_name="__deck__")
    finally:
        os.chdir(cwd)
    if not _decks:
        raise SystemExit(f"{script} created no Deck(...)")
    deck = _decks[-1]
    html = out / f"{deck.slug}.html"
    pdf = out / f"{deck.slug}.pdf"
    html.write_text(deck.html(), encoding="utf-8")
    chrome.pdf(html, pdf)
    print(f"{len(deck.slides)} slides → {pdf}\nself-contained HTML → {html}")


def _titles_vs_script(html):
    """Warnings for slide titles that differ from "On screen" in src/SCRIPT.md (when it exists), slide by slide."""
    import html as html_
    import re
    script = html.parent.parent / "src" / "SCRIPT.md"
    if not script.exists():
        return []
    try:
        import cutroom_script
    except ImportError:
        return []
    r = cutroom_script.read(str(script))
    screens = {}
    for c in r.scenes:
        m = re.search(r"slide\s+(\d+)", c.window or "")
        if m and c.value("on screen"):
            screens[int(m.group(1))] = c.value("on screen")
    doc = html.read_text(encoding="utf-8")
    norm = lambda s: " ".join(html_.unescape(re.sub(r"<[^>]+>", "", s)).replace("`", "").split())  # noqa: E731
    warnings = []
    for n, body in re.findall(r'<section class="slide[^"]*" data-n="(\d+)">(.*?)</section>', doc, re.S):
        t = re.search(r"<h[12]>(.*?)</h[12]>", body, re.S)
        n = int(n)
        if t and n in screens and norm(t.group(1)) != norm(screens[n]):
            warnings.append(f"slide {n:>2} · title differs from the script:\n    deck:   {norm(t.group(1))}\n    script: {norm(screens[n])}")
    return warnings


def check(a):
    html, _ = _html(a.target)
    res = chrome.check(html)
    for w in _titles_vs_script(html):
        print(f"! {w}")
    total = 0
    for e in res["font_errors"]:
        print(f"✗ {e}")
        total += 1
    for s in res["slides"]:
        for p in s["problems"]:
            print(f"✗ slide {s['n']:>2} · {p['type']}: {p['msg']}")
            total += 1
    if total:
        print(f"\n{total} problem(s) in {html.name}. Fix deck.py, run `deck build` and `deck check` again.")
        sys.exit(1)
    print(f"✓ {len(res['slides'])} slides with no layout problem; fonts loaded: "
          f"{', '.join(sorted({f['family'] for f in res['fonts'] if f['status'] == 'loaded'}))}")


def preview(a):
    html, work = _html(a.target)
    folder = work / "preview"
    grid = html.parent / f"{html.stem}-grid.png"
    n = chrome.preview(html, folder, grid, a.scale, a.cols)
    print(f"{n} previews → {folder}/s-01.png …\ngrid → {grid}\nOpen the grid and every page before delivering.")


def main():
    ap = argparse.ArgumentParser(prog="deck", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("build", build), ("check", check), ("preview", preview)):
        s = sub.add_parser(name)
        s.add_argument("target", help="piece folder (cutroom job), src/deck.py or out/<slug>.html")
        if name == "build":
            s.add_argument("--brand", help="render in this brand instead of the one in deck.py / the active one")
        if name == "preview":
            s.add_argument("--scale", type=float, default=0.5, help="preview scale (0.5 = 640 × 360)")
            s.add_argument("--cols", type=int, default=3)
        s.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
