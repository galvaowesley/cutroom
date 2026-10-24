#!/usr/bin/env python3
"""Brands and design systems for cutroom: one folder per brand, described by a brand.json manifest.

A brand folder holds:
  brand.json    manifest: colors, fonts, logos, motion, narration voice (schema in `cutroom brand schema`)
  DESIGN.md     rules for people and agents: principles, color and type usage, components, do and don't
  VOICE.md      verbal identity: tone, vocabulary, words to avoid, how to address the audience
  fonts/        font files (.ttf/.otf) and their licenses, registered on the system by `cutroom brand use`
  logos/        logo files (SVG preferred, PNG accepted)
  tokens.css    generated from brand.json (`cutroom brand build`): :root custom properties
  fonts.css     generated: @font-face rules pointing at fonts/, so HTML and video render offline

Built-in brands live in harness/brands/ (copied by install.sh). Brands you create or import live in
<cutroom home>/brands/ and survive reinstalls; a user brand with the same name wins.

Subcommands (also available as `cutroom brand ...`):
  list [--json]                      brands, with the active one marked
  show [name] [--json]               resolved manifest with absolute paths (what skills read)
  use <name>                         make it the default brand and register its fonts
  new <name> [--primary HEX] [--accent HEX] [--display FAMILY] [--text FAMILY] [--mono FAMILY]
            [--from BRAND] [--language CODE]
                                     scaffold a user brand; colors not given are derived from --primary
  add <folder> [--name NAME]         import a brand folder (validated, copied to the user brands)
  font <name> "<Family>" [--weights 300,400,600] [--role display|text|mono]
                                     download a Google Fonts family (static TTFs + OFL) into the brand
  palette <image...> [--colors 8] [--json]
                                     dominant colors of images (logos, screenshots, photos), via Chrome
  check [name]                       schema, files and WCAG contrast; exit 1 on errors
  build [name]                       regenerate tokens.css and fonts.css
  preview [name] [-o specimen.png]   render a one-page specimen sheet (HTML + PNG): logos, colors, type, components
  book [name] [-o folder] [--format html,png,pdf] [--scale 2] [--boards logo,color,icons,applications]
                                     the brand book: 01 logo, 02 color and type, 03 icons, 04 applications
  compare <name...> [-o folder] [--boards logo,color,applications] [--title "..."] [--notes "..." ...]
                                     candidate brands side by side (boards + compare.html/.png) for approval
  logo <name> <slot>=<file> ...      put logo files in the brand (slots: on_primary, on_light, symbol_on_primary,
                                     symbol_on_light, stacked, app_icon, mono)
  icon <name> <icon.svg...> [--label "..."]   add icons (24 x 24 SVG) to the brand's set
  remove <name>                      delete a user brand
  schema                             print the brand.json reference
"""
import argparse
import base64
import colorsys
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
sys.path.insert(0, str(HARNESS))
import cutroom_home  # noqa: E402

HOME = cutroom_home.home()
BUILTIN = HARNESS / "brands"
USER = HOME / "brands"
DEFAULT_BRAND = "cutroom"

COLOR_KEYS = ["primary", "deep", "accent", "accent_soft", "tint", "background", "surface", "on_primary", "text",
              "text_muted", "border", "success", "success_bg", "warning", "warning_bg", "danger", "danger_bg", "info"]
NEUTRAL_KEYS = ["100", "200", "300", "500", "700", "900"]
LOGO_KEYS = ["on_primary", "on_light", "symbol_on_primary", "symbol_on_light", "on_deep", "symbol_on_deep", "stacked",
             "app_icon", "mono"]

SCHEMA = """brand.json reference (all colors are #RRGGBB):

{
  "name": "acme",                      folder name, [a-z0-9-]
  "display_name": "Acme",
  "description": "one line: who the brand is for",
  "language": "en",                    default content language (BCP 47: en, pt-BR, es...)
  "colors": {
    "primary":     brand color; buttons, eyebrows, big numbers, cover background
    "deep":        dark companion of primary; verdict boxes, dark video backgrounds
    "accent":      highlight only (the one thing to look at); never body text
    "accent_soft": lighter accent for dark backgrounds
    "tint":        very light primary; "how to read" boxes, highlight cards
    "background":  page background (usually white or off-white)
    "surface":     secondary surface (cards on background)
    "on_primary":  text and logo color over primary
    "on_deep":     optional, text over deep (default: on_primary); set it when primary is bright and on_primary dark
    "text", "text_muted", "border",
    "success", "success_bg", "warning", "warning_bg", "danger", "danger_bg", "info",
    "scale":   [6 colors, light -> dark]  ordinal data: levels, groups, heatmaps
    "neutral": {"100","200","300","500","700","900"}  greys, light -> dark
  },
  "fonts": {
    "display": "Family",               titles and big numbers
    "text": "Family",                  body copy
    "mono": "Family",                  code (prefer a no-ligature cut, e.g. "JetBrains Mono NL")
    "files": [{"family": "Family", "weight": "400" | "300 900", "style": "normal", "file": "fonts/x.ttf"}],
    "licenses": ["fonts/OFL-Family.txt"]
  },
  "logos": {                           paths relative to the brand folder, or null
    "on_primary", "on_light",          horizontal lockup for dark/primary and light backgrounds
    "symbol_on_primary", "symbol_on_light",
    "on_deep", "symbol_on_deep"        optional: versions for deep backgrounds when they differ from on_primary
    "stacked", "app_icon", "mono"      optional: stacked lockup, rounded app icon, one-color version
  },
  "tagline": "One line the brand stands for",
  "palette": [{"token": "deep", "name": "Night", "use": "titles, dark backgrounds", "share": 0.4}, ...],
                                       named colors for the brand book (token = a key of colors), share = proportion
  "icons": [{"name": "video", "label": "Video", "note": "renders and cuts", "file": "icons/video.svg"}],
  "book": {"version": "1.0", "date": "2026-10", "eyebrow": "Visual identity",
           "headlines": {"logo": "...", "color": "...", "icons": "...", "applications": "..."}},
  "contact": {"name": "...", "role": "...", "email": "...", "site": "..."}   placeholders for applications
  "shape":  {"radius": 16},            corner radius in px for cards and boxes
  "motion": {"ease": "cubic-bezier(.2,.8,.2,1)", "duration_ms": 450},
  "cover":  {"glow": true},            soft radial of accent in a corner of covers
  "narration": {"en": "af_heart", "pt-BR": "pf_dora"}   default voice per language (profile or voice spec)
}
"""


# --- io ------------------------------------------------------------------------------------------

def config_path():
    return HOME / "config.json"


def load_config():
    p = config_path()
    return json.loads(p.read_text()) if p.exists() else {}


def save_config(cfg):
    HOME.mkdir(parents=True, exist_ok=True)
    config_path().write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")


def active_name():
    return os.environ.get("CUTROOM_BRAND") or load_config().get("brand") or DEFAULT_BRAND


def brand_dirs():
    """{name: folder}, user brands overriding built-in ones."""
    found = {}
    for root in (BUILTIN, USER):
        if root.is_dir():
            for d in sorted(root.iterdir()):
                if (d / "brand.json").exists():
                    found[d.name] = d
    return found


def find(name=None):
    name = name or active_name()
    d = brand_dirs().get(name)
    if d is None:
        p = Path(name).expanduser()
        if (p / "brand.json").exists():
            return p.resolve()
        raise SystemExit(f"brand not found: {name}. Available: {', '.join(brand_dirs()) or 'none'}")
    return d


def load(name=None):
    """Manifest with `dir` (absolute) and defaults filled in."""
    d = find(name)
    m = json.loads((d / "brand.json").read_text(encoding="utf-8"))
    m["dir"] = str(d)
    m.setdefault("name", d.name)
    m.setdefault("display_name", m["name"])
    m.setdefault("language", "en")
    m.setdefault("shape", {}).setdefault("radius", 16)
    m.setdefault("motion", {}).setdefault("ease", "cubic-bezier(.2,.8,.2,1)")
    m["motion"].setdefault("duration_ms", 450)
    m.setdefault("cover", {}).setdefault("glow", True)
    m.setdefault("logos", {})
    m.setdefault("narration", {})
    c = m.setdefault("colors", {})
    if "on_primary" in c:
        c.setdefault("on_deep", c["on_primary"])
    for k in ("on_deep", "symbol_on_deep"):
        m["logos"].setdefault(k, m["logos"].get(k.replace("deep", "primary")))
    return m


def path_of(m, rel):
    return str(Path(m["dir"]) / rel) if rel else None


def resolved(m):
    """What skills read: the manifest plus absolute paths."""
    d = Path(m["dir"])
    r = dict(m)
    r["paths"] = {
        "dir": str(d),
        "design_md": str(d / "DESIGN.md"),
        "voice_md": str(d / "VOICE.md"),
        "tokens_css": str(d / "tokens.css"),
        "fonts_css": str(d / "fonts.css"),
        "fonts_dir": str(d / "fonts"),
        "logos": {k: path_of(m, v) for k, v in m.get("logos", {}).items()},
        "font_files": [path_of(m, f["file"]) for f in m.get("fonts", {}).get("files", [])],
    }
    r["builtin"] = d.parent == BUILTIN
    r["active"] = m["name"] == active_name()
    return r


# --- color ---------------------------------------------------------------------------------------

def rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hexc(c):
    return "#" + "".join(f"{round(max(0, min(1, x)) * 255):02X}" for x in c)


def mix(a, b, t):
    ca, cb = rgb(a), rgb(b)
    return hexc(tuple(x + (y - x) * t for x, y in zip(ca, cb)))


def luminance(hx):
    def ch(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb(hx))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rotate(hx, degrees, sat=None, light=None):
    h, l, s = colorsys.rgb_to_hls(*rgb(hx))
    h = (h + degrees / 360) % 1
    return hexc(colorsys.hls_to_rgb(h, light if light is not None else l, sat if sat is not None else s))


def readable_on(bg, light="#FFFFFF", dark="#14161F"):
    return light if contrast(bg, light) >= contrast(bg, dark) else dark


def derive(primary, accent=None, background="#FFFFFF"):
    """A complete color set from one brand color: a starting point that `check` and the agent refine."""
    h, l, s = colorsys.rgb_to_hls(*rgb(primary))
    if contrast(primary, "#FFFFFF") < 4.5:  # keep white text readable on the cover
        for t in [i / 20 for i in range(1, 15)]:
            cand = mix(primary, "#000000", t)
            if contrast(cand, "#FFFFFF") >= 4.5:
                primary = cand
                break
    accent = accent or rotate(primary, 160, sat=min(1, s + 0.2), light=0.6)
    ink = mix("#14161F", primary, 0.08)
    grey = lambda t: mix(mix("#FFFFFF", "#14161F", t), primary, 0.05)  # noqa: E731
    neutral = {"100": grey(0.05), "200": grey(0.11), "300": grey(0.22), "500": grey(0.5), "700": grey(0.76), "900": ink}
    tint = mix(primary, background, 0.92)
    return {
        "primary": primary, "deep": mix(primary, "#05060A", 0.62), "accent": accent,
        "accent_soft": mix(accent, "#FFFFFF", 0.45), "tint": tint, "background": background,
        "surface": mix(background, primary, 0.03), "on_primary": readable_on(primary), "text": ink,
        "text_muted": neutral["700"], "border": neutral["200"],
        "success": "#1A8F5A", "success_bg": "#E3F4EB", "warning": "#8A5A00", "warning_bg": "#FFF3D6",
        "danger": "#C2333F", "danger_bg": "#FBE5E7", "info": "#2563EB",
        "scale": [tint] + [mix(primary, background, t) for t in (0.82, 0.62, 0.42, 0.2)] + [primary],
        "neutral": neutral,
    }


# --- generated files -----------------------------------------------------------------------------

def tokens_css(m):
    c = m["colors"]
    f = m.get("fonts", {})
    scheme = "dark" if luminance(c.get("background", "#FFFFFF")) < 0.2 else "light"
    lines = ["/* Generated from brand.json by `cutroom brand build`. Edit brand.json, not this file. */",
             ":root {", f"  color-scheme: {scheme};"]
    for k in COLOR_KEYS + ["on_deep"]:
        if k in c:
            lines.append(f"  --{k.replace('_', '-')}: {c[k]};")
    for i, v in enumerate(c.get("scale", [])):
        lines.append(f"  --scale-{i}: {v};")
    for k, v in c.get("neutral", {}).items():
        lines.append(f"  --n{k}: {v};")
    for role in ("display", "text", "mono"):
        fallback = "monospace" if role == "mono" else "sans-serif"
        if f.get(role):
            lines.append(f"  --font-{role}: '{f[role]}', {fallback};")
    lines.append(f"  --radius: {m['shape']['radius']}px;")
    lines.append(f"  --ease: {m['motion']['ease']};")
    lines.append(f"  --duration: {m['motion']['duration_ms']}ms;")
    lines.append("}")
    return "\n".join(lines) + "\n"


def fonts_css(m):
    out = ["/* Generated by `cutroom brand build`: local @font-face rules, so pages and videos render offline. */"]
    for ff in m.get("fonts", {}).get("files", []):
        fmt = "opentype" if ff["file"].endswith(".otf") else "truetype"
        out.append(f"@font-face {{ font-family: '{ff['family']}'; src: url('{ff['file']}') format('{fmt}'); "
                   f"font-weight: {ff.get('weight', '400')}; font-style: {ff.get('style', 'normal')}; font-display: block; }}")
    return "\n".join(out) + "\n"


def build(m):
    d = Path(m["dir"])
    (d / "tokens.css").write_text(tokens_css(m))
    (d / "fonts.css").write_text(fonts_css(m))
    return [d / "tokens.css", d / "fonts.css"]


# --- check ---------------------------------------------------------------------------------------

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def check(m):
    errors, warnings = [], []
    d = Path(m["dir"])
    c = m.get("colors", {})
    for k in COLOR_KEYS:
        v = c.get(k)
        if v is None:
            errors.append(f"colors.{k} is missing")
        elif not HEX.match(v):
            errors.append(f"colors.{k} = {v!r} is not #RRGGBB")
    scale = c.get("scale", [])
    if len(scale) != 6 or not all(HEX.match(x or "") for x in scale):
        errors.append("colors.scale needs 6 #RRGGBB colors, light -> dark")
    elif any(luminance(a) < luminance(b) for a, b in zip(scale, scale[1:])):
        warnings.append("colors.scale is not ordered light -> dark")
    neutral = c.get("neutral", {})
    for k in NEUTRAL_KEYS:
        if not HEX.match(neutral.get(k) or ""):
            errors.append(f"colors.neutral.{k} is missing or not #RRGGBB")
    f = m.get("fonts", {})
    for role in ("display", "text", "mono"):
        if not f.get(role):
            errors.append(f"fonts.{role} is missing")
    families = {x.get("family") for x in f.get("files", [])}
    for ff in f.get("files", []):
        if not (d / ff.get("file", "")).exists():
            errors.append(f"font file not found: {ff.get('file')}")
    for role in ("display", "text", "mono"):
        if f.get(role) and f[role] not in families:
            warnings.append(f"fonts.{role} = {f[role]!r} has no file in fonts.files: it must be installed on the "
                            "system, and self-contained HTML will fall back to another font")
    if f.get("files") and not f.get("licenses"):
        warnings.append("fonts.licenses is empty: ship the font licenses (OFL.txt) next to the files")
    for lic in f.get("licenses", []):
        if not (d / lic).exists():
            errors.append(f"license file not found: {lic}")
    for k, v in m.get("logos", {}).items():
        if k not in LOGO_KEYS:
            warnings.append(f"logos.{k} is not a known slot ({', '.join(LOGO_KEYS)})")
        if v and not (d / v).exists():
            errors.append(f"logo not found: logos.{k} = {v}")
    for doc in ("DESIGN.md", "VOICE.md"):
        if not (d / doc).exists():
            warnings.append(f"{doc} is missing: agents fall back to generic rules")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", m.get("name", "")):
        errors.append("name must be lowercase letters, digits and dashes")
    if errors:
        return errors, warnings

    pairs = [  # (fg, bg, minimum, what)
        ("text", "background", 4.5, "body text on background"),
        ("text_muted", "background", 4.5, "muted text on background"),
        ("text", "surface", 4.5, "body text on surface"),
        ("on_primary", "primary", 4.5, "text on primary (covers, buttons)"),
        ("on_deep", "deep", 4.5, "text on deep"),
        ("primary", "background", 3.0, "primary as a mark or big number on background"),
        ("text", "tint", 4.5, "body text on tint"),
        ("success", "success_bg", 4.5, "success text on its background"),
        ("warning", "warning_bg", 4.5, "warning text on its background"),
        ("danger", "danger_bg", 4.5, "danger text on its background"),
        ("accent_soft", "deep", 3.0, "accent_soft on deep (highlights on dark backgrounds)"),
    ]
    for fg, bg, need, what in pairs:
        r = contrast(c[fg], c[bg])
        if r < need:
            msg = f"contrast {r:.2f}:1 for {what} ({fg} {c[fg]} on {bg} {c[bg]}), needs {need}:1"
            (errors if need >= 4.5 and fg in ("text", "on_primary", "on_deep") else warnings).append(msg)
    return errors, warnings


# --- fonts ---------------------------------------------------------------------------------------

def font_slug(family):
    return re.sub(r"[^A-Za-z0-9]", "", family)


def fetch(url, ua="Wget/1.21"):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def google_font(m, family, weights, role=None, italic=False):
    """Static TTFs per weight from the Google Fonts CSS API, plus the OFL from github.com/google/fonts."""
    d = Path(m["dir"])
    (d / "fonts").mkdir(exist_ok=True)
    spec = ";".join(sorted({str(w) for w in weights}, key=int))
    ws = spec.split(";")
    axis = ("ital,wght@" + ";".join([f"0,{w}" for w in ws] + [f"1,{w}" for w in ws])) if italic else f"wght@{spec}"
    url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}:{axis}"
    try:
        css = fetch(url).decode()
    except OSError as e:
        raise SystemExit(f"Google Fonts did not answer for {family!r} ({e}). Check the family name on fonts.google.com")
    faces = re.findall(r"@font-face\s*{([^}]*)}", css)
    if not faces:
        raise SystemExit(f"no font files for {family!r} at weights {spec}")
    files = [x for x in m.setdefault("fonts", {}).setdefault("files", []) if x.get("family") != family]
    for face in faces:
        w = re.search(r"font-weight:\s*(\d+)", face).group(1)
        st = re.search(r"font-style:\s*(\w+)", face).group(1)
        src = re.search(r"url\((https://[^)]+\.ttf)\)", face)
        if not src:
            continue
        name = f"{font_slug(family)}-{w}{'-italic' if st == 'italic' else ''}.ttf"
        (d / "fonts" / name).write_bytes(fetch(src.group(1)))
        files.append({"family": family, "weight": w, "style": st, "file": f"fonts/{name}"})
        print(f"✓ {family} {w} {st} → fonts/{name}")
    m["fonts"]["files"] = files
    lic = f"fonts/OFL-{font_slug(family)}.txt"
    for folder in ("ofl", "apache", "ufl"):
        try:
            text = fetch(f"https://raw.githubusercontent.com/google/fonts/main/{folder}/{font_slug(family).lower()}/"
                         f"{'OFL.txt' if folder == 'ofl' else 'LICENSE.txt'}")
            (d / lic).write_bytes(text)
            licenses = m["fonts"].setdefault("licenses", [])
            if lic not in licenses:
                licenses.append(lic)
            print(f"✓ license → {lic}")
            break
        except OSError:
            continue
    else:
        print(f"! license for {family} not found on github.com/google/fonts: add it to fonts/ by hand")
    if role:
        m["fonts"][role] = family


def font_install_dir():
    if cutroom_home.WINDOWS:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Windows" / "Fonts"
    if cutroom_home.MAC:
        return Path.home() / "Library/Fonts"
    return Path.home() / ".local/share/fonts/cutroom"


def _register_windows_font(target, family_hint):
    """Per-user fonts on Windows need a registry entry besides the file."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts", 0,
                             winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, f"{family_hint} (TrueType)", 0, winreg.REG_SZ, str(target))
        winreg.CloseKey(key)
    except OSError:
        pass


def install_fonts(m):
    """Register the brand fonts for the current user, so ManimGX, Chrome and ffmpeg find them by family name."""
    files = [(Path(m["dir"]) / f["file"], f) for f in m.get("fonts", {}).get("files", [])]
    files = [(p, f) for p, f in files if p.exists()]
    if not files:
        return []
    dst = font_install_dir()
    dst.mkdir(parents=True, exist_ok=True)
    keep = {f"cutroom-{m['name']}-{p.name}" for p, _ in files}
    for old in dst.glob(f"cutroom-{m['name']}-*"):  # fonts the brand no longer ships
        if old.name not in keep:
            old.unlink()
    done = []
    for p, f in files:
        target = dst / f"cutroom-{m['name']}-{p.name}"
        if not target.exists() or target.stat().st_size != p.stat().st_size:
            shutil.copy2(p, target)
            if cutroom_home.WINDOWS:
                _register_windows_font(target, f"{f['family']} {f.get('weight', '400')} cutroom-{m['name']}")
        done.append(target)
    if not cutroom_home.WINDOWS and not cutroom_home.MAC and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(dst)], capture_output=True)
    return done


def uninstall_fonts(name):
    d = font_install_dir()
    for f in d.glob(f"cutroom-{name}-*") if d.is_dir() else []:
        f.unlink()


# --- chrome --------------------------------------------------------------------------------------

def chrome_candidates():
    if cutroom_home.WINDOWS:
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        return [os.path.join(r, "Google", "Chrome", "Application", "chrome.exe") for r in roots if r] + \
               [os.path.join(r, "Microsoft", "Edge", "Application", "msedge.exe") for r in roots if r]
    return ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"]


def chrome():
    p = os.environ.get("CHROME_PATH")
    if p and os.path.exists(p):
        return p
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        if shutil.which(n):
            return shutil.which(n)
    for c in chrome_candidates():
        if os.path.exists(c):
            return c
    raise SystemExit("Chrome not found: install Google Chrome or Chromium")


def chrome_run(args, timeout=120):
    base = [chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--run-all-compositor-stages-before-draw"]
    r = subprocess.run(base + args, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise SystemExit(f"Chrome failed ({r.returncode}): {r.stderr.strip()[-400:]}")
    return r.stdout


def data_uri(path):
    p = Path(path)
    mime = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".gif": "image/gif", ".ttf": "font/ttf", ".otf": "font/otf",
            ".woff2": "font/woff2"}.get(p.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


PALETTE_JS = """
<script>
(async function () {
  const K = %d, out = [];
  for (const src of %s) {
    const img = new Image(); img.src = src; await img.decode();
    const s = Math.min(1, 160 / Math.max(img.naturalWidth || 160, img.naturalHeight || 160));
    const w = Math.max(1, Math.round((img.naturalWidth || 160) * s)), h = Math.max(1, Math.round((img.naturalHeight || 160) * s));
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d'); g.drawImage(img, 0, 0, w, h);
    const d = g.getImageData(0, 0, w, h).data, px = [];
    for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 200) px.push([d[i], d[i + 1], d[i + 2]]);
    if (!px.length) continue;
    let cs = []; for (let k = 0; k < K; k++) cs.push(px[Math.floor((k + 0.5) * px.length / K)].slice());
    let n = [];
    for (let it = 0; it < 12; it++) {
      const sum = cs.map(() => [0, 0, 0]); n = cs.map(() => 0);
      for (const p of px) {
        let b = 0, bd = 1e9;
        cs.forEach((q, k) => { const dd = (p[0]-q[0])**2 + (p[1]-q[1])**2 + (p[2]-q[2])**2; if (dd < bd) { bd = dd; b = k; } });
        n[b]++; sum[b][0] += p[0]; sum[b][1] += p[1]; sum[b][2] += p[2];
      }
      cs = cs.map((q, k) => n[k] ? sum[k].map(v => v / n[k]) : q);
    }
    cs.forEach((q, k) => { if (n[k]) out.push({ hex: '#' + q.map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase(), share: n[k] / px.length, image: src.slice(0, 0) }); });
  }
  const el = document.createElement('script'); el.type = 'application/json'; el.id = 'palette';
  el.textContent = JSON.stringify(out); document.body.appendChild(el);
})();
</script>
"""


def palette(images, k=8):
    srcs = [data_uri(i) for i in images]
    with tempfile.TemporaryDirectory() as t:
        page = Path(t) / "p.html"
        page.write_text("<!doctype html><body>" + PALETTE_JS % (k, json.dumps(srcs)) + "</body>")
        dom = chrome_run(["--dump-dom", "--virtual-time-budget=15000", page.as_uri()])
    m = re.search(r'<script type="application/json" id="palette">(.*?)</script>', dom, re.S)
    if not m:
        raise SystemExit("palette extraction did not finish (unsupported image format?)")
    colors = json.loads(html.unescape(m.group(1)))
    merged = []  # merge near-identical colors across images
    for c in sorted(colors, key=lambda x: -x["share"]):
        for mm in merged:
            if sum((a - b) ** 2 for a, b in zip(rgb(c["hex"]), rgb(mm["hex"]))) < 0.004:
                mm["share"] += c["share"]
                break
        else:
            merged.append({"hex": c["hex"], "share": c["share"]})
    total = sum(c["share"] for c in merged) or 1
    for c in merged:
        c["share"] = round(c["share"] / total, 4)
        h, l, s = colorsys.rgb_to_hls(*rgb(c["hex"]))
        c["role_hint"] = ("background" if l > 0.93 else "text" if l < 0.12 else
                          "neutral" if s < 0.12 else "brand candidate")
        c["contrast_on_white"] = round(contrast(c["hex"], "#FFFFFF"), 2)
    return sorted(merged, key=lambda x: -x["share"])


# --- preview -------------------------------------------------------------------------------------

def specimen_html(m):
    c, f, d = m["colors"], m.get("fonts", {}), Path(m["dir"])
    faces = "".join(
        f"@font-face {{ font-family: '{x['family']}'; src: url('{data_uri(d / x['file'])}'); font-weight: {x.get('weight', '400')}; "
        f"font-style: {x.get('style', 'normal')}; }}\n" for x in f.get("files", []) if (d / x["file"]).exists())
    logo = lambda k: (f'<img src="{data_uri(d / m["logos"][k])}" alt="{k}">'  # noqa: E731
                      if m["logos"].get(k) and (d / m["logos"][k]).exists() else f'<span class="nologo">no {k} logo</span>')
    e = html.escape

    def sw(k, v, fg=None):
        fg = fg or readable_on(v)
        ratio = contrast(v, c["background"])
        return (f'<div class="sw" style="background:{v};color:{fg}"><b>{e(k)}</b><span>{v}</span>'
                f'<span>{ratio:.1f}:1 on bg</span></div>')
    core = "".join(sw(k, c[k]) for k in ("primary", "deep", "accent", "accent_soft", "tint", "surface"))
    scale = "".join(f'<div style="background:{v};color:{readable_on(v)}">{i}<br>{v}</div>' for i, v in enumerate(c["scale"]))
    neutral = "".join(f'<div style="background:{v};color:{readable_on(v)}">{k}<br>{v}</div>' for k, v in c["neutral"].items())
    sem = "".join(f'<div class="sem" style="background:{c[k + "_bg"]};color:{c[k]}"><b>{k}</b> {c[k]} on {c[k + "_bg"]}'
                  f' · {contrast(c[k], c[k + "_bg"]):.1f}:1</div>' for k in ("success", "warning", "danger"))
    r = m["shape"]["radius"]
    css = f"""
{faces}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: {c['background']}; color: {c['text']}; font: 16px/1.5 '{f.get('text')}', sans-serif; }}
.wrap {{ width: 1440px; padding: 56px 64px 64px; display: grid; gap: 40px; }}
h1 {{ font: 600 44px/1.1 '{f.get('display')}'; margin: 0; letter-spacing: -.02em; }}
h2 {{ font: 600 13px/1 '{f.get('display')}'; letter-spacing: .1em; text-transform: uppercase; color: {c['primary']}; margin: 0 0 14px; }}
.sub {{ color: {c['text_muted']}; margin-top: 8px; max-width: 900px; }}
.hero {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; }}
.cover {{ background: {c['primary']}; color: {c['on_primary']}; border-radius: {r + 4}px; padding: 40px; min-height: 300px; position: relative;
  overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; }}
.cover::after {{ content: ""; position: absolute; right: -160px; bottom: -200px; width: 520px; height: 520px; border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, {c['accent']} {45 if m['cover']['glow'] else 0}%, transparent) 0%, transparent 70%); }}
.cover img {{ height: 40px; position: relative; z-index: 1; align-self: flex-start; }}
.cover h3 {{ font: 600 40px/1.08 '{f.get('display')}'; margin: 0; letter-spacing: -.02em; position: relative; z-index: 1; max-width: 560px; }}
.cover p {{ font: 300 22px/1.3 '{f.get('display')}'; margin: 10px 0 0; position: relative; z-index: 1; opacity: .92; }}
.logos {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.logos > div {{ border-radius: {r}px; display: grid; place-items: center; padding: 22px; min-height: 140px; }}
.logos img {{ max-height: 54px; max-width: 80%; }}
.nologo {{ font-size: 13px; opacity: .6; }}
.row {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }}
.sw {{ border-radius: {r}px; padding: 16px; min-height: 120px; display: flex; flex-direction: column; gap: 2px; font-size: 13px; border: 1px solid {c['border']}; }}
.sw b {{ font: 600 15px/1.2 '{f.get('display')}'; margin-bottom: auto; }}
.strip {{ display: grid; grid-template-columns: repeat(6, 1fr); border-radius: {r}px; overflow: hidden; font-size: 12px; }}
.strip div {{ padding: 14px; min-height: 70px; }}
.sems {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
.sem {{ border-radius: {r}px; padding: 14px 18px; font-size: 14px; }}
.type {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; align-items: start; }}
.d1 {{ font: 800 76px/1 '{f.get('display')}'; letter-spacing: -.03em; }}
.d2 {{ font: 600 34px/1.15 '{f.get('display')}'; letter-spacing: -.01em; margin-top: 12px; }}
.num {{ font: 300 64px/1 '{f.get('display')}'; color: {c['primary']}; font-variant-numeric: tabular-nums; }}
.body {{ font-size: 18px; line-height: 1.55; color: {c['text_muted']}; }}
pre {{ font: 15px/1.5 '{f.get('mono')}', monospace; background: {c['deep']}; color: {c['on_deep']}; padding: 18px 22px; border-radius: {r}px; margin: 0; }}
pre i {{ color: {c['accent_soft']}; font-style: normal; }}
.comp {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
.card {{ border: 1px solid {c['border']}; background: {c['surface']}; border-radius: {r}px; padding: 22px; display: grid; gap: 8px; }}
.card .k {{ font: 600 12px/1 '{f.get('display')}'; letter-spacing: .08em; text-transform: uppercase; color: {c['text_muted']}; }}
.card .v {{ font: 300 48px/1 '{f.get('display')}'; color: {c['primary']}; }}
.verdict {{ background: {c['deep']}; color: {c['on_deep']}; border-radius: {r}px; padding: 22px; display: grid; gap: 8px; }}
.verdict b {{ font: 600 22px/1.2 '{f.get('display')}'; }}
.verdict .k {{ color: {c['accent_soft']}; }}
.tintbox {{ background: {c['tint']}; border-radius: {r}px; padding: 22px; color: {c['text']}; }}
.btns {{ display: flex; gap: 12px; align-items: center; }}
.btn {{ font: 600 15px/1 '{f.get('display')}'; padding: 13px 20px; border-radius: 999px; }}
.btn.p {{ background: {c['primary']}; color: {c['on_primary']}; }}
.btn.s {{ border: 1.5px solid {c['primary']}; color: {c['primary']}; }}
.btn.a {{ background: {c['accent']}; color: {readable_on(c['accent'])}; }}
.foot {{ font-size: 13px; color: {c['text_muted']}; border-top: 1px solid {c['border']}; padding-top: 14px; }}
"""
    lp = logo("on_primary")
    return f"""<!doctype html><html lang="{e(m['language'])}"><head><meta charset="utf-8"><title>{e(m['display_name'])} brand</title>
<style>{css}</style></head><body><div class="wrap">
<header><h1>{e(m['display_name'])}</h1><p class="sub">{e(m.get('description', ''))}</p></header>
<section class="hero"><div class="cover">{lp}<div><h3>Every number comes from the data</h3>
<p>Cover · {e(f.get('display', ''))} 600 and 300 on primary</p></div></div>
<div class="logos"><div style="background:{c['primary']}">{lp}</div><div style="background:{c['background']};border:1px solid {c['border']}">{logo('on_light')}</div>
<div style="background:{c['deep']}">{logo('symbol_on_deep')}</div><div style="background:{c['tint']}">{logo('symbol_on_light')}</div></div></section>
<section><h2>Core colors</h2><div class="row">{core}</div></section>
<section><h2>Scale · ordinal data, light to dark</h2><div class="strip">{scale}</div></section>
<section><h2>Neutrals</h2><div class="strip">{neutral}</div></section>
<section><h2>Semantic · only for state</h2><div class="sems">{sem}</div></section>
<section class="type"><div><h2>Display · {e(f.get('display', ''))}</h2><div class="d1">Aa 0123</div>
<div class="d2">Titles say the message with the number</div><div class="num" style="margin-top:18px">85.5%</div></div>
<div><h2>Text · {e(f.get('text', ''))}</h2><p class="body">Body copy sits at 16 to 18 px with generous line height. Numbers appear in the
middle of the sentence, compared with a reference: 85.5% against 0.4% for exact matching.</p>
<h2 style="margin-top:22px">Mono · {e(f.get('mono', ''))}</h2><pre><i># no ligatures: -> stays -></i>
def derivative(f, x, h=1e-6):
    return (f(x + h) - f(x)) / h</pre></div></section>
<section><h2>Components</h2><div class="comp"><div class="card"><span class="k">Accuracy</span><span class="v">85.5%</span>
<span>top-1 match on 22,284 queries</span></div><div class="verdict"><span class="k" style="font:600 12px/1 '{f.get('display')}';letter-spacing:.08em;text-transform:uppercase">Verdict</span>
<b>Ready for search, not for audit</b><span>The right match is first in 85.5% of queries.</span></div>
<div class="tintbox"><b>How to read</b><br>Filled dots are hits; hollow dots are misses. Further left is better.</div></div>
<div class="btns" style="margin-top:18px"><span class="btn p">Primary action</span><span class="btn s">Secondary</span><span class="btn a">Accent</span></div></section>
<p class="foot">Specimen generated by <code>cutroom brand preview {e(m['name'])}</code> from brand.json · radius {r}px · ease {e(m['motion']['ease'])}</p>
</div></body></html>"""


def preview(m, out_png=None):
    d = Path(m["dir"])
    out_png = Path(out_png) if out_png else d / "specimen.png"
    out_html = out_png.with_suffix(".html")
    out_html.write_text(specimen_html(m), encoding="utf-8")
    chrome_run([f"--screenshot={out_png}", "--window-size=1440,1720", "--virtual-time-budget=5000", out_html.as_uri()])
    return out_html, out_png


# --- scaffolding ---------------------------------------------------------------------------------

DESIGN_TEMPLATE = """# {display} design system

> Rules for people and agents. `brand.json` holds the values; this file says how to use them.
> Replace every TODO with what the brand inputs say. Keep it short and concrete.

## Principles

- TODO: three principles that decide close calls (e.g. "one accent per frame", "numbers carry the weight").

## Color

- **Primary {primary}** is the constant: eyebrows, big numbers, the main series, covers.
- **Deep {deep}** gives depth: verdict boxes, dark video backgrounds.
- **Accent {accent}** marks the one thing to look at. Never body text, never a whole background.
- Backgrounds are solid. Depth comes from a soft radial of the accent in one corner, not full gradients.
- Ordinal data uses `scale` light -> dark. Semantic colors (`success`, `warning`, `danger`) only mean state.

## Type

- **{display_font}** for titles and big numbers (600 for titles, 300 for numbers).
- **{text_font}** for body copy, 16 to 18 px, line height 1.5.
- **{mono_font}** for code.

## Shape and motion

- Corner radius {radius} px on cards and boxes; pills for buttons.
- Motion uses `{ease}`: short fades and translates, no bounce.

## Logo

- `logos/on_primary` over primary or deep, `logos/on_light` over light backgrounds.
- Clear space of at least the symbol height. Never recolor, rotate, stretch or add effects.
- Only on pieces that speak for the brand (covers, closing slides, end cards).

## Do / don't

| Do | Don't |
|---|---|
| TODO | TODO |
"""

VOICE_TEMPLATE = """# {display} voice

> How the brand writes and speaks. Agents read this before any script, slide title or narration.

- **Address:** TODO (e.g. "you", second person, never "the user").
- **Tone:** TODO, three pairs of "X, but never Y" (e.g. "simple, but never naive").
- **Numbers:** in the middle of the sentence, compared with a reference.
- **Avoid:** superlatives, alarm words, corporate filler, emoji.
- **Name:** how the brand name is written (case, accents).
- **Language:** {language} by default.
"""


def write_manifest(d, m):
    clean = {k: v for k, v in m.items() if k != "dir"}
    (Path(d) / "brand.json").write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def new(name, primary=None, accent=None, display=None, text=None, mono=None, base=None, language=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise SystemExit("brand name: lowercase letters, digits and dashes")
    d = USER / name
    if d.exists():
        raise SystemExit(f"{d} already exists: edit it, or `cutroom brand remove {name}` first")
    src = load(base or DEFAULT_BRAND)
    d.mkdir(parents=True)
    m = {"name": name, "display_name": name.replace("-", " ").title(), "description": "TODO: who the brand is for",
         "language": language or src.get("language", "en")}
    if primary:
        m["colors"] = derive(primary, accent)
    else:
        m["colors"] = json.loads(json.dumps(src["colors"]))
        if accent:
            m["colors"]["accent"] = accent
    if base or not (display or text or mono):  # keep the base fonts (files copied) unless new ones are named
        (d / "fonts").mkdir()
        for x in src.get("fonts", {}).get("files", []) + [{"file": lic} for lic in src.get("fonts", {}).get("licenses", [])]:
            s = Path(src["dir"]) / x["file"]
            if s.exists():
                shutil.copy2(s, d / x["file"])
        m["fonts"] = json.loads(json.dumps(src.get("fonts", {})))
    else:
        m["fonts"] = {"display": display or "", "text": text or "", "mono": mono or "JetBrains Mono", "files": [], "licenses": []}
    for role, fam in (("display", display), ("text", text), ("mono", mono)):
        if fam:
            m["fonts"][role] = fam
    m["logos"] = {k: None for k in LOGO_KEYS}
    (d / "logos").mkdir()
    m["shape"], m["motion"], m["cover"] = src["shape"], src["motion"], src["cover"]
    m["narration"] = src.get("narration", {})
    write_manifest(d, m)
    c = m["colors"]
    (d / "DESIGN.md").write_text(DESIGN_TEMPLATE.format(
        display=m["display_name"], primary=c["primary"], deep=c["deep"], accent=c["accent"],
        display_font=m["fonts"].get("display"), text_font=m["fonts"].get("text"), mono_font=m["fonts"].get("mono"),
        radius=m["shape"]["radius"], ease=m["motion"]["ease"]))
    (d / "VOICE.md").write_text(VOICE_TEMPLATE.format(display=m["display_name"], language=m["language"]))
    return load(name)


def add(folder, name=None):
    src = Path(folder).expanduser().resolve()
    if not (src / "brand.json").exists():
        raise SystemExit(f"{src} has no brand.json (see `cutroom brand schema`)")
    m = json.loads((src / "brand.json").read_text(encoding="utf-8"))
    name = name or m.get("name") or src.name
    dst = USER / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".DS_Store", "specimen.*"))
    m["name"] = name
    write_manifest(dst, m)
    return load(name)


def use(name):
    m = load(name)
    errors, _ = check(m)
    if errors:
        raise SystemExit("cannot use a brand with errors:\n  " + "\n  ".join(errors))
    build(m)
    fonts = install_fonts(m)
    cfg = load_config()
    cfg["brand"] = m["name"]
    save_config(cfg)
    return m, fonts


# --- cli -----------------------------------------------------------------------------------------

def report(m):
    errors, warnings = check(m)
    for e in errors:
        print(f"✗ {e}")
    for w in warnings:
        print(f"! {w}")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cutroom brand", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("show"); s.add_argument("name", nargs="?"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("use"); s.add_argument("name")
    s = sub.add_parser("new"); s.add_argument("name")
    for opt in ("--primary", "--accent", "--display", "--text", "--mono", "--from", "--language"):
        s.add_argument(opt, dest=opt[2:].replace("from", "base"))
    s = sub.add_parser("add"); s.add_argument("folder"); s.add_argument("--name")
    s = sub.add_parser("font"); s.add_argument("name"); s.add_argument("family")
    s.add_argument("--weights", default="300,400,600,800"); s.add_argument("--role", choices=["display", "text", "mono"])
    s.add_argument("--italic", action="store_true")
    s = sub.add_parser("palette"); s.add_argument("images", nargs="+"); s.add_argument("--colors", type=int, default=8)
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("check"); s.add_argument("name", nargs="?")
    s = sub.add_parser("build"); s.add_argument("name", nargs="?")
    s = sub.add_parser("preview"); s.add_argument("name", nargs="?"); s.add_argument("-o", "--output")
    s = sub.add_parser("remove"); s.add_argument("name")
    sub.add_parser("schema")
    s = sub.add_parser("book"); s.add_argument("name", nargs="?"); s.add_argument("-o", "--output")
    s.add_argument("--format", default="html,png,pdf"); s.add_argument("--scale", type=float, default=1.0)
    s.add_argument("--boards", default="logo,color,icons,applications")
    s = sub.add_parser("logo"); s.add_argument("name"); s.add_argument("slots", nargs="+")
    s = sub.add_parser("compare"); s.add_argument("names", nargs="+"); s.add_argument("-o", "--output", default="brand-proposals")
    s.add_argument("--boards", default="logo,color,applications"); s.add_argument("--title"); s.add_argument("--notes", nargs="*")
    s.add_argument("--scale", type=float, default=1.0)
    s = sub.add_parser("icon"); s.add_argument("name"); s.add_argument("files", nargs="+"); s.add_argument("--label", action="append")
    a = ap.parse_args(argv)

    if a.cmd == "list":
        rows = []
        for n, d in brand_dirs().items():
            m = load(n)
            rows.append({"name": n, "display_name": m["display_name"], "description": m.get("description", ""),
                         "builtin": d.parent == BUILTIN, "active": n == active_name(), "dir": str(d)})
        if a.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for r in rows:
                print(f"{'●' if r['active'] else '·'} {r['name']:<14} {'built-in' if r['builtin'] else 'user':<9} {r['description']}")
    elif a.cmd == "show":
        r = resolved(load(a.name))
        if a.json:
            print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            c = r["colors"]
            print(f"{r['display_name']} ({r['name']}{', active' if r['active'] else ''}) · {r['paths']['dir']}")
            print(f"  colors   primary {c['primary']} · deep {c['deep']} · accent {c['accent']} · background {c['background']}")
            print(f"  fonts    display {r['fonts'].get('display')} · text {r['fonts'].get('text')} · mono {r['fonts'].get('mono')}")
            print(f"  logos    {', '.join(k for k, v in r['logos'].items() if v) or 'none'}")
            print(f"  rules    {r['paths']['design_md']}\n  voice    {r['paths']['voice_md']}\n  tokens   {r['paths']['tokens_css']}")
    elif a.cmd == "use":
        m, fonts = use(a.name)
        print(f"✓ {m['name']} is the default brand · {len(fonts)} font files registered on the system")
    elif a.cmd == "new":
        m = new(a.name, a.primary, a.accent, a.display, a.text, a.mono, a.base, a.language)
        build(m)
        print(f"✓ created {m['dir']}\n  next: fonts (`cutroom brand font {a.name} \"Family\" --role display`), logos in logos/, "
              f"DESIGN.md and VOICE.md, then `cutroom brand check {a.name}` and `cutroom brand preview {a.name}`")
    elif a.cmd == "add":
        m = add(a.folder, a.name)
        build(m)
        errors, _ = report(m)
        print(f"{'✗' if errors else '✓'} imported {m['name']} → {m['dir']}")
        return 1 if errors else 0
    elif a.cmd == "font":
        m = load(a.name)
        if Path(m["dir"]).parent == BUILTIN:
            raise SystemExit(f"{a.name} is built-in: create your own with `cutroom brand new <name> --from {a.name}`")
        google_font(m, a.family, [int(w) for w in a.weights.split(",")], a.role, a.italic)
        write_manifest(m["dir"], m)
        build(load(a.name))
    elif a.cmd == "palette":
        cols = palette(a.images, a.colors)
        if a.json:
            print(json.dumps(cols, indent=2))
        else:
            for c in cols:
                print(f"{c['hex']}  {c['share'] * 100:5.1f}%  {c['role_hint']:<16} {c['contrast_on_white']:.2f}:1 on white")
    elif a.cmd == "check":
        m = load(a.name)
        errors, warnings = report(m)
        if not errors:
            build(m)
            print(f"✓ {m['name']}: no errors, {len(warnings)} warning(s); tokens.css and fonts.css rebuilt")
        return 1 if errors else 0
    elif a.cmd == "build":
        for p in build(load(a.name)):
            print(p)
    elif a.cmd == "preview":
        m = load(a.name)
        build(m)
        h, p = preview(m, a.output)
        print(f"{h}\n{p}")
    elif a.cmd == "remove":
        d = find(a.name)
        if d.parent != USER:
            raise SystemExit(f"{a.name} is built-in and cannot be removed")
        shutil.rmtree(d)
        uninstall_fonts(a.name)
        if active_name() == a.name:
            cfg = load_config()
            cfg["brand"] = DEFAULT_BRAND
            save_config(cfg)
        print(f"✓ removed {a.name}")
    elif a.cmd == "schema":
        print(SCHEMA)
    elif a.cmd == "book":
        import cutroom_book
        bad = set(a.format.split(",")) - {"html", "png", "pdf"}
        if bad:
            raise SystemExit(f"--format accepts html, png and pdf (got {', '.join(bad)})")
        build(load(a.name))
        for p in cutroom_book.build_book(a.name, a.output, a.format.split(","), a.scale, a.boards.split(",")):
            print(p)
    elif a.cmd == "compare":
        import cutroom_book
        page, png = cutroom_book.compare(a.names, a.output, a.boards.split(","), a.title, a.notes, a.scale)
        print(f"{page}\n{png}")
    elif a.cmd == "logo":
        m = load(a.name)
        if Path(m["dir"]).parent == BUILTIN:
            raise SystemExit(f"{a.name} is built-in: create your own with `cutroom brand new <name> --from {a.name}`")
        (Path(m["dir"]) / "logos").mkdir(exist_ok=True)
        for pair in a.slots:
            slot, _, f = pair.partition("=")
            if slot not in LOGO_KEYS or not f:
                raise SystemExit(f"use slot=file with slot in {', '.join(LOGO_KEYS)}")
            src = Path(f).expanduser()
            dst = Path(m["dir"]) / "logos" / f"{slot.replace('_', '-')}{src.suffix.lower()}"
            shutil.copy2(src, dst)
            m["logos"][slot] = f"logos/{dst.name}"
            print(f"✓ {slot} → logos/{dst.name}")
        write_manifest(m["dir"], m)
    elif a.cmd == "icon":
        m = load(a.name)
        if Path(m["dir"]).parent == BUILTIN:
            raise SystemExit(f"{a.name} is built-in: create your own with `cutroom brand new <name> --from {a.name}`")
        (Path(m["dir"]) / "icons").mkdir(exist_ok=True)
        icons = m.setdefault("icons", [])
        for i, f in enumerate(a.files):
            src = Path(f).expanduser()
            shutil.copy2(src, Path(m["dir"]) / "icons" / src.name)
            label = (a.label or [])[i] if a.label and i < len(a.label) else src.stem.replace("-", " ").title()
            icons[:] = [x for x in icons if x["name"] != src.stem] + [{"name": src.stem, "label": label, "file": f"icons/{src.name}"}]
            print(f"✓ icon {src.stem}")
        write_manifest(m["dir"], m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
