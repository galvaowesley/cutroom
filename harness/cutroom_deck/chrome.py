"""PDF, previews and the layout check, all through headless Chrome (CHROME_PATH from env.sh, or found by itself)."""
import json
import re
import subprocess
from pathlib import Path

import cutroom_brand

from .render import H, W


def chrome():
    return cutroom_brand.chrome()


def _run(args, timeout=180, capture=False):
    base = [chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--run-all-compositor-stages-before-draw"]
    r = subprocess.run(base + args, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise SystemExit(f"Chrome failed ({r.returncode}): {r.stderr.strip()[-400:]}")
    return r.stdout if capture else None


def pdf(html_path, pdf_path):
    _run(["--no-pdf-header-footer", "--virtual-time-budget=10000", f"--print-to-pdf={pdf_path}", Path(html_path).as_uri()])


def count_slides(html_path):
    return len(re.findall(r'<section class="slide', Path(html_path).read_text(encoding="utf-8")))


def preview(html_path, folder, grid_path, scale=0.5, cols=3):
    """One PNG per slide (s-01.png...) in `folder` and a grid of all of them in `grid_path`."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("s-*.png"):
        f.unlink()
    n = count_slides(html_path)
    url = Path(html_path).as_uri()
    for i in range(1, n + 1):
        _run([f"--screenshot={folder / f's-{i:02d}.png'}", f"--window-size={W},{H}", f"--force-device-scale-factor={scale}",
              "--virtual-time-budget=6000", f"{url}?slide={i}"])
    w, h, gap = int(W * scale), int(H * scale), 16
    rows = -(-n // cols)
    imgs = "".join(f'<figure><img src="s-{i:02d}.png"><figcaption>{i}</figcaption></figure>' for i in range(1, n + 1))
    grid_html = folder / "grid.html"
    grid_html.write_text(
        f'<!doctype html><meta charset="utf-8"><style>body{{margin:0;padding:{gap}px;background:#E5E5EA;font:12px sans-serif;color:#3E4456}}'
        f'.g{{display:grid;grid-template-columns:repeat({cols},{w}px);gap:{gap}px}}figure{{margin:0}}'
        f'img{{display:block;width:{w}px;height:{h}px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.15)}}'
        f'figcaption{{padding-top:4px}}</style><div class="g">{imgs}</div>', encoding="utf-8")
    gw = cols * w + (cols + 1) * gap
    gh = rows * (h + 20) + (rows + 1) * gap
    _run([f"--screenshot={grid_path}", f"--window-size={gw},{gh}", "--virtual-time-budget=4000", grid_html.as_uri()])
    return n


def check(html_path):
    """Run check.js and return its result (dict with slides, fonts and font errors)."""
    dom = _run(["--dump-dom", f"--window-size={W},{H}", "--virtual-time-budget=10000", f"{Path(html_path).as_uri()}?check=1"],
               capture=True)
    m = re.search(r'<script type="application/json" id="deck-check">(.*?)</script>', dom, re.S)
    if not m:
        raise SystemExit("the check did not run: Chrome returned no result (fonts too slow to load?)")
    return json.loads(m.group(1).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
