#!/usr/bin/env python3
"""Brand book: the boards that present a brand, generated from its brand.json (`cutroom brand book`).

Four boards, 1440 x 1120 each, in the brand itself:
  01 logo          primary lockup on light and dark, stacked, symbol, app icon, one-color; clear space, minimum sizes
  02 color         named palette with HEX/RGB and use, usage proportion, display and text type, hierarchy
  03 icons         the brand's icon set (icons/ in the brand, or a default line set drawn in the brand colors)
  04 applications  business card, avatar, social banner, email signature, presentation cover, document, website

  cutroom brand book [name] [-o folder] [--format html,png,pdf] [--scale 2] [--boards logo,color,icons,applications]

HTML is self-contained (fonts and logos embedded); PNG renders each board at --scale; PDF puts all boards in one
file, one board per page. Labels follow the brand's `language` (English and Portuguese built in).
Optional brand.json fields used here: palette, book, icons, contact, tagline, descriptor (`cutroom brand schema`).
"""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutroom_brand as cb  # noqa: E402

W, H = 1440, 1120
BOARDS = ["logo", "color", "icons", "applications"]
LABELS = {
    "en": {"identity": "Visual identity", "logo": "Logo", "color": "Color and type", "icons": "Icons",
           "applications": "Applications", "version": "Version", "stacked": "Stacked", "symbol": "Symbol",
           "app_icon": "App icon · avatar", "mono": "One color", "clear": "Clear space and minimum size",
           "clear_text": "Keep a margin around the logo at least the height of the symbol's smallest element. On screen, "
                         "the symbol is never smaller than 16 px; the horizontal logo, never narrower than 96 px.",
           "area": "Clear space", "proportion": "Suggested usage proportion", "titles": "Titles", "text": "Text",
           "hierarchy": "Hierarchy", "h1": "Heading H1", "h2": "Subheading H2",
           "body": "Body copy in {text} Regular, 16 px with 1.6 line height.", "caption": "Caption in uppercase",
           "pairing": "{display} to stand out, {text} to read.", "grid": "24 x 24 grid · 1.75 px stroke",
           "daily": "The brand, day to day.", "avatar": "Social avatar", "cover_title": "Presentation title",
           "cover_sub": "Subtitle · [date]", "nav": ["Work", "About", "Contact"], "cta": "Get in touch",
           "rgb": "RGB"},
    "pt": {"identity": "Identidade visual", "logo": "Logo", "color": "Cor e tipografia", "icons": "Ícones",
           "applications": "Aplicações", "version": "Versão", "stacked": "Empilhado", "symbol": "Símbolo",
           "app_icon": "Ícone de app · avatar", "mono": "Monocromático", "clear": "Espaço livre e tamanho mínimo",
           "clear_text": "Mantenha ao redor do logo uma margem igual, no mínimo, à altura do menor elemento do símbolo. "
                         "Em tela, o símbolo não fica menor que 16 px; o logotipo horizontal, menor que 96 px de largura.",
           "area": "Área de respeito", "proportion": "Proporção de uso sugerida", "titles": "Títulos", "text": "Texto",
           "hierarchy": "Hierarquia", "h1": "Título H1", "h2": "Subtítulo H2",
           "body": "Corpo de texto em {text} Regular, 16 px com entrelinha de 1,6.", "caption": "Legenda em caixa alta",
           "pairing": "{display} para destacar, {text} para ler.", "grid": "Grade 24 × 24 · traço 1,75 px",
           "daily": "A marca no dia a dia.", "avatar": "Avatar de redes sociais", "cover_title": "Título da apresentação",
           "cover_sub": "Subtítulo · [data]", "nav": ["Serviços", "Projetos", "Contato"], "cta": "Fale com a gente",
           "rgb": "RGB"},
}
# Default icon set (Lucide paths, ISC) for brands without icons/: drawn in text color with an accent dot.
DEFAULT_ICONS = [
    ("video", "Video", '<rect x="2" y="5" width="15" height="14" rx="2"/><path d="m17 10 5-3v10l-5-3"/>', (9.5, 12)),
    ("voice", "Voice", '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4"/>', (12, 8)),
    ("deck", "Decks", '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4M7 12l3-3 3 2 4-4"/>', (17, 7)),
    ("diagram", "Diagrams", '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M6 9v3a3 3 0 0 0 3 3h6"/>', (18, 18)),
    ("figure", "Figures", '<path d="m12 2 9 5v10l-9 5-9-5V7z"/><path d="m3 7 9 5 9-5M12 12v10"/>', (12, 12)),
    ("graphic", "Graphics", '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="m21 15-4-4L6 21"/>', (9, 9)),
    ("edit", "Editing", '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12"/>', (12, 12)),
    ("brand", "Brand", '<path d="M12 22a10 10 0 1 1 10-10c0 3-2.5 3-4 3h-2a2 2 0 0 0-1 3.7A1.6 1.6 0 0 1 12 22z"/>', (8, 9)),
    ("script", "Scripts", '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>', (16, 17)),
    ("extract", "Documents", '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M12 18v-6M9 15l3 3 3-3"/>', (12, 18)),
    ("math", "Math", '<path d="M4 20c4 0 5-16 9-16M3 12h8M15 15l5 5M20 15l-5 5"/>', (13, 4)),
    ("motion", "Motion", '<circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4z"/>', (16, 12)),
]


def esc(s):
    return html.escape(str(s if s is not None else ""))


def labels(m):
    return LABELS.get(m.get("language", "en").split("-")[0].lower(), LABELS["en"])


def img(m, slot, height, fallback="", style=""):
    rel = m.get("logos", {}).get(slot)
    if rel and (Path(m["dir"]) / rel).exists():
        return f'<img src="{cb.data_uri(Path(m["dir"]) / rel)}" style="height:{height}px;width:auto;display:block;{style}" alt="{esc(slot)}">'
    return fallback


def symbol_or_wordmark(m, dark, height, on="deep"):
    """Symbol for the background (falls back to the wordmark), as <img>. dark: deep (or primary with on="primary")."""
    slot = f"symbol_on_{on}" if dark else "symbol_on_light"
    alt = f"on_{on}" if dark else "on_light"
    return img(m, slot, height) or img(m, alt, height * 0.5)


def palette(m):
    c = m["colors"]
    if m.get("palette"):
        return [dict(p, hex=c.get(p["token"], p.get("hex"))) for p in m["palette"]]
    return [{"token": "deep", "name": "Deep", "use": "Titles on dark, verdicts, video backgrounds", "share": 0.35},
            {"token": "primary", "name": "Primary", "use": "Brand color, actions, big numbers", "share": 0.2},
            {"token": "accent", "name": "Accent", "use": "The one highlight per frame", "share": 0.08},
            {"token": "surface", "name": "Surface", "use": "Backgrounds and cards", "share": 0.3},
            {"token": "text_muted", "name": "Muted", "use": "Supporting text and captions", "share": 0.07}]


def rgb_text(hx):
    r, g, b = (round(x * 255) for x in cb.rgb(hx))
    return f"{r} · {g} · {b}"


def font_faces(m):
    d = Path(m["dir"])
    return "".join(
        f"@font-face {{ font-family: '{f['family']}'; src: url('{cb.data_uri(d / f['file'])}'); font-weight: {f.get('weight', '400')}; "
        f"font-style: {f.get('style', 'normal')}; }}\n" for f in m.get("fonts", {}).get("files", []) if (d / f["file"]).exists())


def css(m):
    c, f = m["colors"], m["fonts"]
    r = m["shape"]["radius"]
    return f"""{font_faces(m)}
* {{ box-sizing: border-box; }}
@page {{ size: {W}px {H}px; margin: 0; }}
html, body {{ margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ background: {c['surface']}; font-family: '{f['text']}', sans-serif; color: {c['text']}; }}
.board {{ width: {W}px; height: {H}px; padding: 72px; display: flex; flex-direction: column; gap: 32px; background: {c['surface']};
  break-after: page; page-break-after: always; overflow: hidden; position: relative; }}
.head {{ display: flex; justify-content: space-between; align-items: flex-end; }}
.eyebrow {{ font: 700 13px/1 '{f['text']}'; letter-spacing: .18em; text-transform: uppercase; color: {c['primary']}; margin-bottom: 12px; }}
h1 {{ font: 600 40px/1.1 '{f['display']}'; letter-spacing: -.02em; margin: 0; }}
.ver {{ font-size: 14px; color: {c['text_muted']}; font-weight: 500; }}
.card {{ background: {c['background']}; border: 1px solid {c['border']}; border-radius: {r + 4}px; position: relative; overflow: hidden; }}
.dark {{ background: {c['deep']}; color: {c['on_deep']}; border-color: {c['deep']}; }}
.prim {{ background: {c['primary']}; color: {c['on_primary']}; border-color: {c['primary']}; }}
.cap {{ position: absolute; left: 24px; bottom: 22px; font: 700 12px/1 '{f['text']}'; letter-spacing: .12em; text-transform: uppercase; color: {c['text_muted']}; }}
.dark .cap {{ color: {c['on_deep']}; opacity: .85; }}
.prim .cap {{ color: {c['on_primary']}; opacity: .85; }}
.center {{ display: flex; align-items: center; justify-content: center; }}
.muted {{ color: {c['text_muted']}; }}
"""


def head(m, n, key, headline):
    lb = labels(m)
    book = m.get("book", {})
    ver = f"{lb['version']} {book.get('version', '1.0')}" + (f" · {book['date']}" if book.get("date") else "")
    return (f'<div class="head"><div><div class="eyebrow">{esc(book.get("eyebrow", lb["identity"]))} · {n:02d} {esc(lb[key])}</div>'
            f'<h1>{esc(headline)}</h1></div><div class="ver">{esc(ver)}</div></div>')


def headline(m, key, default):
    return m.get("book", {}).get("headlines", {}).get(key, default)


def board_logo(m):
    lb, c = labels(m), m["colors"]
    r = m["shape"]["radius"]
    app = (img(m, "app_icon", 128) or
           f'<div style="width:128px;height:128px;border-radius:{r * 2}px;background:{c["deep"]}" class="center">{symbol_or_wordmark(m, True, 76)}</div>')
    stacked = img(m, "stacked", 120) or (f'<div style="display:grid;justify-items:center;gap:14px">{symbol_or_wordmark(m, False, 56)}'
                                         f'{img(m, "on_light", 34, style="clip-path:none")}</div>')
    mono = img(m, "on_primary", 54)  # one color: all white on primary
    sizes = "".join(f'<div style="display:grid;justify-items:center;gap:8px">{symbol_or_wordmark(m, False, s)}'
                    f'<span style="font-size:12px" class="muted">{s} px</span></div>' for s in (32, 24, 16))
    return f"""<section class="board">{head(m, 1, "logo", headline(m, "logo", m.get("tagline") or m["display_name"]))}
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px">
<div class="card center" style="grid-column:span 2;height:360px">{img(m, "on_light", 104)}</div>
<div class="card dark center" style="height:360px">{img(m, "on_deep", 72)}</div></div>
<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px">
<div class="card center" style="height:250px;padding-bottom:40px">{stacked}<span class="cap">{esc(lb["stacked"])}</span></div>
<div class="card center" style="height:250px;padding-bottom:40px">{symbol_or_wordmark(m, False, 96)}<span class="cap">{esc(lb["symbol"])}</span></div>
<div class="card center" style="height:250px;padding-bottom:40px">{app}<span class="cap">{esc(lb["app_icon"])}</span></div>
<div class="card prim center" style="height:250px;padding-bottom:40px">{mono}<span class="cap">{esc(lb["mono"])}</span></div></div>
<div class="card" style="display:grid;grid-template-columns:180px 1fr auto;gap:48px;align-items:center;padding:28px 32px">
<div style="display:grid;justify-items:center;gap:10px"><div style="border:1.5px dashed {c['primary']};padding:26px;border-radius:4px">{symbol_or_wordmark(m, False, 56)}</div>
<span style="font:700 12px/1 '{m['fonts']['text']}';letter-spacing:.12em;text-transform:uppercase" class="muted">{esc(lb["area"])}</span></div>
<div><div style="font:600 22px/1.2 '{m['fonts']['display']}';margin-bottom:8px">{esc(lb["clear"])}</div>
<div class="muted" style="font-size:15px;line-height:1.6;max-width:620px">{esc(lb["clear_text"])}</div></div>
<div style="display:flex;gap:28px;align-items:end">{sizes}</div></div></section>"""


def board_color(m):
    lb, c, f = labels(m), m["colors"], m["fonts"]
    pal = palette(m)
    cards = "".join(
        f'<div class="card" style="height:270px;padding:24px;display:flex;flex-direction:column;justify-content:space-between;'
        f'background:{p["hex"]};border-color:{c["border"] if cb.luminance(p["hex"]) > 0.8 else p["hex"]};color:{cb.readable_on(p["hex"], dark=c["text"])}">'
        f'<div style="font:600 24px/1.05 \'{f["display"]}\';max-width:180px">{esc(p["name"])}</div>'
        f'<div><div style="font:600 17px/1.2 \'{f["display"]}\';letter-spacing:.02em">{p["hex"].upper()}</div>'
        f'<div style="font-size:13px;margin-top:6px;opacity:.9">{lb["rgb"]} {rgb_text(p["hex"])}</div>'
        f'<div style="font-size:13px;margin-top:6px;opacity:.9">{esc(p.get("use", ""))}</div></div></div>' for p in pal)
    total = sum(p.get("share", 0) for p in pal) or 1
    bar = "".join(f'<div style="flex:{p.get("share", 0) / total};background:{p["hex"]}"></div>' for p in pal if p.get("share"))
    shares = " · ".join(f'{round(100 * p["share"] / total)}% {esc(p["name"]).lower()}' for p in pal if p.get("share"))
    weights = lambda fam: " · ".join(sorted({str(x.get("weight")) for x in f.get("files", []) if x["family"] == fam}, key=lambda w: int(w.split()[0])))  # noqa: E731
    tag = m.get("tagline") or m.get("description", "")
    return f"""<section class="board">{head(m, 2, "color", headline(m, "color", m["display_name"]))}
<div style="display:grid;grid-template-columns:repeat({len(pal)},minmax(0,1fr));gap:16px">{cards}</div>
<div><div style="display:flex;height:22px;border-radius:11px;overflow:hidden;border:1px solid {c['border']}">{bar}</div>
<div class="muted" style="font-size:13px;margin-top:10px">{esc(lb["proportion"])}: {shares}</div></div>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;flex:1">
<div class="card" style="padding:28px;display:flex;flex-direction:column;justify-content:space-between;background:{c['surface']}">
<div class="eyebrow" style="color:{c['text_muted']}">{esc(lb["titles"])} · {esc(f["display"])}</div>
<div style="font:600 128px/1 '{f['display']}';letter-spacing:-.03em">Aa</div>
<div><div style="font:600 26px/1.2 '{f['display']}'">{esc(tag)}</div><div class="muted" style="font-size:13px;margin-top:8px">{esc(weights(f["display"]))}</div></div></div>
<div class="card" style="padding:28px;display:flex;flex-direction:column;justify-content:space-between;background:{c['surface']}">
<div class="eyebrow" style="color:{c['text_muted']}">{esc(lb["text"])} · {esc(f["text"])}</div>
<div style="font:500 128px/1 '{f['text']}';letter-spacing:-.02em">Aa</div>
<div><div style="font-size:17px;line-height:1.55">{esc(m.get("description", ""))}</div><div class="muted" style="font-size:13px;margin-top:8px">{esc(weights(f["text"]))}</div></div></div>
<div class="card dark" style="padding:28px;display:flex;flex-direction:column;justify-content:space-between">
<div class="eyebrow" style="color:{c['accent_soft']}">{esc(lb["hierarchy"])}</div>
<div><div style="font:600 40px/1.1 '{f['display']}';letter-spacing:-.02em">{esc(lb["h1"])}</div>
<div style="font:600 24px/1.3 '{f['display']}';margin-top:12px">{esc(lb["h2"])}</div>
<div style="font-size:16px;line-height:1.6;margin-top:14px;opacity:.92">{esc(lb["body"].format(text=f["text"]))}</div>
<div style="font:700 12px/1 '{f['text']}';letter-spacing:.14em;text-transform:uppercase;color:{c['accent_soft']};margin-top:18px">{esc(lb["caption"])}</div>
<div style="font:15px/1.5 '{f['mono']}',monospace;margin-top:18px;color:{c['accent_soft']}">{esc(f["mono"])} · code()</div></div>
<div style="font-size:13px;opacity:.8">{esc(lb["pairing"].format(display=f["display"], text=f["text"]))}</div></div></div></section>"""


def icon_svg(m, body, dot, size=36):
    c = m["colors"]
    d = f'<circle cx="{dot[0]}" cy="{dot[1]}" r="2" fill="{c["accent"]}" stroke="none"/>' if dot else ""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{c["deep"]}" stroke-width="1.75" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}{d}</svg>')


def board_icons(m):
    lb, c, f = labels(m), m["colors"], m["fonts"]
    d = Path(m["dir"])
    items = []
    for ic in m.get("icons", []):
        p = d / ic["file"]
        svg = p.read_text() if p.exists() else ""
        items.append((ic.get("label", ic["name"]), ic.get("note", ""), svg))
    if not items:
        items = [(lab, "", icon_svg(m, body, dot)) for _, lab, body, dot in DEFAULT_ICONS]
    cells = "".join(
        f'<div class="card" style="padding:26px;height:{232 if len(items) > 8 else 300}px;display:flex;flex-direction:column;justify-content:space-between">'
        f'<div class="center" style="width:72px;height:72px;border-radius:{m["shape"]["radius"]}px;background:{c["tint"]}">{svg}</div>'
        f'<div><div style="font:600 19px/1.2 \'{f["display"]}\'">{esc(lab)}</div><div class="muted" style="font-size:14px;margin-top:4px">{esc(note)}</div></div></div>'
        for lab, note, svg in items[:12])
    return f"""<section class="board"><div class="head"><div><div class="eyebrow">{esc(m.get("book", {}).get("eyebrow", lb["identity"]))} · 03 {esc(lb["icons"])}</div>
<h1>{esc(headline(m, "icons", lb["icons"]))}</h1></div><div class="ver">{esc(m.get("book", {}).get("icon_grid", lb["grid"]))}</div></div>
<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px">{cells}</div></section>"""


def board_applications(m):
    lb, c, f = labels(m), m["colors"], m["fonts"]
    r = m["shape"]["radius"]
    ct = {"name": "Your Name", "role": "Role", "email": "hello@example.com", "phone": "[phone]", "site": "[site]"}
    ct.update(m.get("contact", {}))
    tag = m.get("tagline") or m["display_name"]
    glow = (f'<div style="position:absolute;right:-140px;bottom:-180px;width:480px;height:480px;border-radius:50%;'
            f'background:radial-gradient(circle,color-mix(in srgb,{c["accent"]} 45%,transparent) 0%,transparent 70%)"></div>'
            if m["cover"]["glow"] else "")
    nav = "".join(f"<span>{esc(x)}</span>" for x in lb["nav"])
    return f"""<section class="board">{head(m, 4, "applications", headline(m, "applications", lb["daily"]))}
<div style="display:grid;grid-template-columns:1.25fr 1.25fr 1fr;gap:24px">
<div class="card dark center" style="height:256px">{img(m, "on_deep", 56)}</div>
<div class="card" style="height:256px;padding:32px;display:flex;flex-direction:column;justify-content:space-between">
<div style="display:flex;justify-content:space-between"><div><div style="font:600 22px/1.2 '{f['display']}'">{esc(ct['name'])}</div>
<div class="muted" style="font-size:13px;margin-top:6px">{esc(ct['role'])}</div></div>{symbol_or_wordmark(m, False, 26)}</div>
<div><div style="width:36px;height:3px;background:{c['primary']};margin-bottom:16px"></div><div style="font-size:13px;line-height:1.7">{esc(ct['email'])}<br>{esc(ct['phone'])}<br>{esc(ct['site'])}</div></div></div>
<div class="card center" style="height:256px;flex-direction:column;gap:18px"><div class="center" style="width:150px;height:150px;border-radius:50%;background:{c['deep']}">{symbol_or_wordmark(m, True, 84)}</div>
<span style="font:700 12px/1 '{f['text']}';letter-spacing:.12em;text-transform:uppercase" class="muted">{esc(lb['avatar'])}</span></div></div>
<div style="display:grid;grid-template-columns:2.4fr 1fr;gap:24px">
<div class="card prim" style="height:220px;padding:36px 40px;display:flex;flex-direction:column;justify-content:space-between">{glow}
<div style="position:relative">{img(m, "on_primary", 34)}</div><div style="position:relative;font:600 34px/1.12 '{f['display']}';letter-spacing:-.02em;max-width:560px">{esc(tag)}</div>
<div style="position:absolute;right:40px;bottom:36px;width:84px;height:84px;border-radius:50%;background:{c['accent']}"></div></div>
<div class="card" style="height:220px;padding:28px;display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center">
{symbol_or_wordmark(m, False, 42)}<div style="border-left:2px solid {c['primary']};padding-left:20px"><div style="font:600 17px/1.2 '{f['display']}'">{esc(ct['name'])}</div>
<div class="muted" style="font-size:12px;margin:4px 0 10px">{esc(ct['role'])} · {esc(m['display_name'])}</div><div style="font-size:12px;line-height:1.6">{esc(ct['email'])}<br>{esc(ct['site'])}</div></div></div></div>
<div style="display:grid;grid-template-columns:1.5fr .55fr 1.65fr;gap:24px;flex:1">
<div class="card prim" style="padding:32px;display:flex;flex-direction:column;justify-content:space-between">
<div style="position:absolute;right:-90px;bottom:-110px;opacity:.16">{symbol_or_wordmark(m, True, 360, on="primary")}</div>
<div style="position:relative">{img(m, "on_primary", 26)}</div><div style="position:relative"><div style="width:48px;height:4px;background:{c['accent']};margin-bottom:16px"></div>
<div style="font:600 30px/1.15 '{f['display']}'">{esc(lb['cover_title'])}</div><div style="font-size:14px;opacity:.8;margin-top:8px">{esc(lb['cover_sub'])}</div></div></div>
<div class="card" style="padding:22px;display:flex;flex-direction:column;gap:10px">{img(m, "on_light", 16)}
<div style="height:6px;width:80%;background:{c['text']};border-radius:3px;margin-top:14px"></div>
{''.join(f'<div style="height:4px;width:{w}%;background:{c["border"]};border-radius:2px"></div>' for w in (100, 92, 96, 70, 100, 84))}
<div style="margin-top:auto;height:2px;background:{c['primary']}"></div></div>
<div class="card dark" style="display:flex;flex-direction:column"><div style="background:{c['border']};padding:8px 12px 0;display:flex">
<div style="background:{c['deep']};color:{c['on_deep']};font-size:12px;padding:7px 14px;border-radius:8px 8px 0 0;display:flex;gap:8px;align-items:center">{symbol_or_wordmark(m, True, 12)}{esc(m['display_name'])}</div></div>
<div style="padding:22px 28px;display:flex;flex-direction:column;gap:20px;flex:1"><div style="display:flex;justify-content:space-between;align-items:center">{img(m, "on_deep", 20)}
<div style="display:flex;gap:18px;font-size:13px;opacity:.85">{nav}</div></div>
<div style="font:600 30px/1.12 '{f['display']}';letter-spacing:-.02em;max-width:460px">{esc(tag)}</div>
<div><span style="display:inline-block;background:{c['accent']};color:{cb.readable_on(c['accent'], dark=c['deep'])};font:600 14px/1 '{f['display']}';padding:13px 20px;border-radius:{max(6, r // 2)}px">{esc(lb['cta'])}</span></div></div></div></div></section>"""


RENDER = {"logo": board_logo, "color": board_color, "icons": board_icons, "applications": board_applications}


def document(m, boards):
    return (f'<!doctype html><html lang="{esc(m.get("language", "en"))}"><head><meta charset="utf-8">'
            f'<title>{esc(m["display_name"])} brand book</title><style>{css(m)}</style></head><body>'
            + "".join(RENDER[b](m) for b in boards) + "</body></html>")


def build_book(name=None, out=None, formats=("html", "png", "pdf"), scale=1.0, boards=BOARDS):
    m = cb.load(name)
    out = (Path(out) if out else Path(m["dir"]) / "book").resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = []
    full = out / f"{m['name']}-brand-book.html"
    full.write_text(document(m, boards), encoding="utf-8")
    for i, b in enumerate(boards, 1):
        page = out / f"{BOARDS.index(b) + 1:02d}-{b}.html"
        page.write_text(document(m, [b]), encoding="utf-8")
        if "png" in formats:
            png = page.with_suffix(".png")
            cb.chrome_run([f"--screenshot={png}", f"--window-size={W},{H}", f"--force-device-scale-factor={scale}",
                           "--virtual-time-budget=5000", page.as_uri()])
            results.append(png)
        if "html" in formats:
            results.append(page)
        elif "png" in formats:
            page.unlink()
    if "pdf" in formats:
        pdf = out / f"{m['name']}-brand-book.pdf"
        cb.chrome_run(["--no-pdf-header-footer", "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", full.as_uri()])
        results.append(pdf)
    if "html" in formats:
        results.append(full)
    else:
        full.unlink()
    return results


def compare(names, out, boards=("logo", "color", "applications"), title=None, notes=None, scale=1.0):
    """Proposals side by side: each brand's boards as PNG, then one page (HTML + PNG) to choose from."""
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, name in enumerate(names):
        m = cb.load(name)
        cb.build(m)
        build_book(name, out / m["name"], ("png",), scale, list(boards))
        note = (notes or [None] * len(names))[i] or m.get("description", "")
        imgs = "".join(f'<img src="{esc(m["name"])}/{BOARDS.index(b) + 1:02d}-{b}.png">' for b in boards)
        rows.append(f'<section><h2>{esc(m.get("display_name", name))} <span>· {esc(m["name"])} — {esc(note)}</span></h2>'
                    f'<div class="row" style="grid-template-columns:repeat({len(boards)},1fr)">{imgs}</div></section>')
    page = out / "compare.html"
    page.write_text(f"""<!doctype html><meta charset="utf-8"><title>{esc(title or "Brand proposals")}</title>
<style>body{{margin:0;background:#E9E9EE;font:15px/1.5 -apple-system,Helvetica,Arial,sans-serif;color:#111}}
h1{{font-size:28px;margin:32px 40px 4px}}p.s{{margin:0 40px 24px;color:#555}}section{{margin:0 40px 48px}}
h2{{font-size:20px;margin:0 0 12px}}h2 span{{font-weight:400;color:#666}}.row{{display:grid;gap:14px}}
.row img{{width:100%;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15)}}</style>
<h1>{esc(title or "Brand proposals")}</h1><p class="s">{len(names)} directions, same boards. Pick one, or mix parts of them.</p>
{''.join(rows)}""", encoding="utf-8")
    png = out / "compare.png"
    cb.chrome_run([f"--screenshot={png}", f"--window-size={max(1600, 700 * len(boards))},{240 + 700 * len(names)}",
                   "--virtual-time-budget=5000", page.as_uri()])
    return page, png


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="cutroom brand book", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--format", default="html,png,pdf")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--boards", default=",".join(BOARDS))
    a = ap.parse_args()
    for p in build_book(a.name, a.output, a.format.split(","), a.scale, a.boards.split(",")):
        print(p)
