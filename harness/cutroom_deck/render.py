"""Deck: builds the slides (cover, content slides, closing) into a self-contained 1280 x 720 HTML.

Fonts and logos are embedded as data: URIs (the HTML works on its own, also when published as a page). The same
HTML produces the PDF (Chrome, @page 1280 x 720), the previews (?slide=N) and the layout check (?check=1).
"""
import base64
import mimetypes
from pathlib import Path

from . import fmt
from .fmt import esc
from .theme import active, use

W, H = 1280, 720
MARGINS = (52, 72, 44)  # top, sides, bottom
_decks = []


def _data_uri(path):
    p = str(path)
    mime = mimetypes.guess_type(p)[0] or ("font/ttf" if p.endswith(".ttf") else "font/otf" if p.endswith(".otf")
                                          else "application/octet-stream")
    if p.endswith(".svg"):
        mime = "image/svg+xml"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def _lang_default():
    try:
        import cutroom_brand
        return cutroom_brand.load_config().get("language") or "en"
    except Exception:
        return "en"


class Deck:
    """One presentation. Create one per deck.py; `deck build` finds the instance by itself."""

    def __init__(self, title, footer, slug, theme=None, lang=None):
        self.title, self.footer, self.slug = title, footer, slug
        self.lang = lang or _lang_default()
        fmt.set_locale(self.lang)
        self.theme = use(theme or active())
        self.slides = []
        _decks.append(self)

    # --- slides ----------------------------------------------------------------------------------

    def _n(self):
        return len(self.slides) + 1

    def _footer(self, n):
        return f'<footer class="ft"><span>{self.footer}</span><span>{n}</span></footer>'

    def _logo(self, rel, cls=""):
        if not rel or not self.theme.file(rel).exists():
            return ""
        return f'<img class="{cls}" src="{_data_uri(self.theme.file(rel))}" alt="logo">'

    def cover(self, eyebrow, title, subtitle="", meta=""):
        """Cover on primary, with the on-primary logo and (if the brand says so) a soft glow in one corner."""
        sub = f'<p class="cover-sub">{subtitle}</p>' if subtitle else ""
        met = f'<p class="cover-meta">{meta}</p>' if meta else ""
        self.slides.append(
            f'<section class="slide cover" data-n="{self._n()}">{self._logo(self.theme.logo_cover, "logo")}<div class="cover-txt">'
            f'<p class="eyebrow light">{eyebrow}</p><h1>{title}</h1>{sub}{met}</div></section>')

    def slide(self, eyebrow, title, *blocks, source="", cls=""):
        """Content slide: eyebrow, title with the message (one factual sentence with the number, up to 2 lines),
        body, and the source note (where the number comes from and the period)."""
        n = self._n()
        note = f'<p class="source">{source}</p>' if source else ""
        self.slides.append(
            f'<section class="slide {cls}" data-n="{n}"><header class="hd"><p class="eyebrow">{eyebrow}</p>'
            f'<h2>{title}</h2></header><div class="bd">{"".join(blocks)}{note}</div>{self._footer(n)}</section>')

    def closing(self, title="", lines=(), signature=""):
        """Last slide: optional final message, contacts or links, and the on-light logo."""
        n = self._n()
        tit = f"<h2>{title}</h2>" if title else ""
        ls = "".join(f"<p>{l}</p>" for l in lines)
        self.slides.append(
            f'<section class="slide closing" data-n="{n}"><div class="closing-txt">{tit}{ls}</div>'
            f'<div class="closing-brand">{self._logo(self.theme.logo_closing)}<span>{signature}</span></div>'
            f'{self._footer(n)}</section>')

    # --- document --------------------------------------------------------------------------------

    def css(self):
        t = self.theme
        faces = "".join(
            f"@font-face {{ font-family: '{fam}'; src: url('{_data_uri(t.file(f))}'); font-weight: {w}; font-style: {st}; font-display: block; }}\n"
            for fam, f, w, st in t.font_files if t.file(f).exists())
        glow = (f"radial-gradient(circle, color-mix(in srgb, {t.accent} 45%, transparent) 0%, transparent 70%)"
                if t.cover_glow else "none")
        return faces + CSS.format(t=t, W=W, H=H, m=MARGINS, glow=glow, r=t.radius)

    def html(self):
        check_js = (Path(__file__).with_name("check.js")).read_text(encoding="utf-8")
        return (f'<!doctype html><html lang="{self.lang}"><head><meta charset="utf-8"><title>{esc(self.title)}</title>'
                f'<meta name="viewport" content="width={W}"><style>{self.css()}</style></head><body>'
                f'{"".join(self.slides)}<script>{MODES_JS}</script><script>{check_js}</script></body></html>')


# ?slide=N shows only slide N (previews); ?check=1 runs check.js.
MODES_JS = """
(function () {
  var q = new URLSearchParams(location.search), n = q.get('slide');
  if (n) {
    document.querySelectorAll('section.slide').forEach(function (s) {
      if (s.getAttribute('data-n') !== n) s.style.display = 'none';
    });
    document.body.classList.add('solo');
  }
})();
"""

CSS = """
@page {{ size: {W}px {H}px; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: {t.background}; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: '{t.font_text}', sans-serif; color: {t.n900}; }}
.slide {{ width: {W}px; height: {H}px; position: relative; overflow: hidden; padding: {m[0]}px {m[1]}px {m[2]}px; display: flex;
  flex-direction: column; break-after: page; page-break-after: always; background: {t.background}; }}
.hd {{ margin-bottom: 22px; flex: none; }}
.eyebrow {{ margin: 0 0 8px; font: 600 13px/1 '{t.font_display}'; letter-spacing: .08em; text-transform: uppercase; color: {t.primary}; }}
h2 {{ margin: 0; font: 600 32px/1.18 '{t.font_display}'; letter-spacing: -.01em; color: {t.n900}; max-width: 1080px; text-wrap: balance; }}
h3 {{ margin: 0 0 10px; font: 600 16px/1.3 '{t.font_display}'; color: {t.n900}; }}
h4 {{ margin: 0 0 6px; font: 600 17px/1.3 '{t.font_display}'; color: {t.n900}; }}
.bd {{ flex: 1; display: flex; flex-direction: column; gap: 18px; min-height: 0; }}
.bd > * {{ flex-shrink: 0; }}  /* nothing shrinks to fit: what does not fit overflows and the check reports it */
.ft {{ flex: none; display: flex; justify-content: space-between; font-size: 12px; color: {t.n500}; padding-top: 10px; border-top: 1px solid {t.n200}; }}
p {{ margin: 0; }}
b {{ font-weight: 600; }}
ul {{ margin: 0; padding-left: 18px; display: grid; gap: 6px; }}
.source {{ font-size: 13px; color: {t.n500}; line-height: 1.45; margin-top: auto; }}
.note, .illustrative {{ font-size: 13px; color: {t.n500}; line-height: 1.45; }}
.illustrative {{ font-style: normal; margin-top: 4px; }}
.lead {{ font-size: 18px; line-height: 1.5; color: {t.n700}; max-width: 1080px; }}
.txt {{ font-size: 16px; line-height: 1.5; color: {t.n700}; }}
.k {{ font: 600 12px/1.2 '{t.font_display}'; letter-spacing: .08em; text-transform: uppercase; color: {t.primary}; margin-bottom: 10px; }}
.sub {{ font-size: 13px; color: {t.n500}; font-weight: 400; }}
.box {{ background: {t.tint}; border-radius: {r}px; padding: 18px 22px; font-size: 15px; line-height: 1.5; color: {t.n700}; }}
.box p + p {{ margin-top: 8px; }}
.cols {{ display: grid; }}
.stack {{ display: flex; flex-direction: column; }}
.center {{ display: flex; justify-content: center; }}
.legend {{ display: flex; gap: 22px; font-size: 14px; color: {t.n700}; margin-bottom: 6px; flex-wrap: wrap; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }}
.big {{ display: grid; gap: 6px; }}
.big-v {{ font: 300 44px/1 '{t.font_display}'; color: {t.primary}; font-variant-numeric: tabular-nums; }}
.big-t {{ font-size: 15px; color: {t.n700}; line-height: 1.45; }}
.code {{ margin: 0; background: {t.deep}; color: {t.on_deep}; border-radius: {r}px; padding: 18px 22px; font: 15px/1.5 '{t.font_mono}', monospace; white-space: pre; }}

/* Cover and closing */
.cover {{ background: {t.primary}; color: {t.on_primary}; padding: 64px 80px; justify-content: space-between; }}
.cover::after {{ content: ""; position: absolute; right: -220px; bottom: -260px; width: 760px; height: 760px; border-radius: 50%; background: {glow}; }}
.cover .logo {{ height: 46px; width: auto; align-self: flex-start; position: relative; z-index: 1; }}
.cover-txt {{ position: relative; z-index: 1; display: grid; gap: 12px; max-width: 900px; }}
.cover h1 {{ margin: 0; font: 600 60px/1.08 '{t.font_display}'; letter-spacing: -.02em; }}
.cover-sub {{ font: 300 32px/1.2 '{t.font_display}'; }}
.cover-meta {{ font-size: 18px; opacity: .85; margin-top: 18px; }}
.eyebrow.light {{ color: {t.on_primary}; opacity: .8; }}
.closing {{ justify-content: flex-start; }}
.closing-txt {{ display: grid; gap: 14px; max-width: 900px; margin-top: 120px; }}
.closing-txt p {{ font-size: 20px; line-height: 1.5; color: {t.n700}; }}
.closing-brand {{ display: flex; align-items: center; gap: 22px; font-size: 14px; color: {t.n500}; margin: auto 0 22px; }}
.closing-brand img {{ height: 40px; width: auto; }}

/* Summary */
.g-summary {{ display: grid; grid-template-columns: 1fr 1.55fr; gap: 24px; }}
.verdict {{ background: {t.deep}; color: {t.on_deep}; border-radius: {r}px; padding: 26px 28px; display: grid; gap: 12px; align-content: start; font-size: 16px; line-height: 1.5; }}
.verdict .k {{ color: {t.accent_soft}; margin: 0; }}
.verdict-v {{ font: 600 26px/1.2 '{t.font_display}'; }}
.kpis {{ display: grid; gap: 16px; }}
.kpi {{ border: 1px solid {t.n200}; border-radius: {r}px; padding: 20px; display: grid; gap: 6px; align-content: start; }}
.kpi-l {{ font: 600 12px/1.2 '{t.font_display}'; letter-spacing: .06em; text-transform: uppercase; color: {t.n500}; }}
.kpi-v {{ font: 300 52px/1 '{t.font_display}'; color: {t.primary}; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.kpi-n {{ font-size: 14px; color: {t.n700}; line-height: 1.4; }}
.highlights {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 16px; }}
.highlights li {{ background: {t.tint}; border-radius: {r}px; padding: 18px 22px; font-size: 17px; line-height: 1.45; color: {t.n700}; }}

/* Measures */
.measures {{ display: grid; gap: 20px; }}
.measure {{ border: 1px solid {t.n200}; border-radius: {r}px; padding: 20px 22px; display: flex; flex-direction: column; gap: 8px; }}
.m-l {{ font: 600 13px/1.2 '{t.font_display}'; letter-spacing: .06em; text-transform: uppercase; color: {t.n500}; }}
.m-v {{ font: 300 46px/1 '{t.font_display}'; color: {t.primary}; font-variant-numeric: tabular-nums; }}
.m-d {{ font-size: 15px; line-height: 1.45; color: {t.n900}; min-height: 66px; }}
.m-vis {{ display: flex; justify-content: center; align-items: center; min-height: 150px; }}
.m-r {{ font-size: 13px; color: {t.n500}; line-height: 1.4; margin-top: auto; }}

/* Steps and cards */
.steps {{ display: grid; gap: 20px; }}
.step {{ border: 1px solid {t.n200}; border-radius: {r}px; padding: 20px 22px; font-size: 16px; line-height: 1.5; color: {t.n700}; }}
.step-top {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }}
.num {{ display: inline-grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: {t.primary}; color: {t.on_primary}; font: 600 15px/1 '{t.font_display}'; }}
.card-grid {{ display: grid; gap: 16px; }}
.card {{ border-radius: {r}px; padding: 18px 22px; font-size: 15px; line-height: 1.5; color: {t.n700}; }}
.card.outline {{ border: 1px solid {t.n200}; }}
.card.tint {{ background: {t.tint}; }}
.card.deep {{ background: {t.deep}; color: {t.on_deep}; }}
.card.deep h4 {{ color: {t.on_deep}; }}
.card.deep .k {{ color: {t.accent_soft}; }}
.card-ic {{ margin-bottom: 8px; }}

/* Queues */
.queues {{ display: grid; gap: 10px; }}
.queue-axis {{ display: flex; align-items: center; gap: 10px; padding-left: 230px; font-size: 13px; color: {t.n500}; }}
.queue {{ display: grid; grid-template-columns: 230px 1fr; align-items: center; }}
.queue-l {{ display: grid; gap: 2px; }}
.queue-l b {{ font: 600 16px/1.2 '{t.font_display}'; color: {t.n900}; }}
.queue-l span {{ font-size: 14px; color: {t.primary}; font-weight: 600; }}

/* Small multiples, composition */
.multiples {{ display: grid; gap: 20px; }}
.comp-list {{ display: grid; gap: 2px; margin-top: 8px; font-size: 14px; color: {t.n700}; }}
.comp-list div {{ display: grid; grid-template-columns: 14px 1fr auto; gap: 8px; align-items: center; }}
.comp-list i {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
.comp-list b {{ font-variant-numeric: tabular-nums; color: {t.n900}; }}

/* Tables */
.table {{ width: 100%; border-collapse: collapse; font-size: 15px; }}
.table th {{ text-align: left; font: 600 12px/1.3 '{t.font_display}'; color: {t.n500}; padding: 6px 10px; border-bottom: 1px solid {t.n200}; }}
.table td {{ padding: 7px 10px; border-bottom: 1px solid {t.n100}; vertical-align: middle; line-height: 1.3; }}
.table .n {{ text-align: right; font-variant-numeric: tabular-nums; }}
.seg-tab td.seg {{ display: flex; align-items: center; gap: 10px; font-variant-numeric: tabular-nums; }}

/* Use and verdict */
.uses {{ display: grid; gap: 16px; }}
.use {{ border-radius: {r}px; padding: 22px 24px; display: grid; gap: 8px; font-size: 17px; line-height: 1.45; color: {t.n700}; align-content: start; }}
.use > b {{ font: 600 20px/1.2 '{t.font_display}'; }}
.use.yes {{ background: {t.success_bg}; }}
.use.yes > b {{ color: {t.success}; }}
.use.no {{ background: {t.danger_bg}; }}
.use.no > b {{ color: {t.danger}; }}
.g-sl {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
.g-sl .box {{ font-size: 16px; }}
.box.strong {{ background: {t.success_bg}; }}
.box.strong .k {{ color: {t.success}; }}
.box.limit {{ background: {t.warning_bg}; }}
.box.limit .k {{ color: {t.warning}; }}
.verdict-line {{ font-size: 18px; line-height: 1.5; color: {t.n900}; border-left: 4px solid {t.primary}; padding-left: 16px; }}

/* Proposals and next steps */
.proposals {{ display: grid; gap: 12px; }}
.proposal {{ border: 1px solid {t.scale[3]}; background: {t.tint}; border-radius: {r}px; padding: 14px 18px; display: grid;
  grid-template-columns: auto 1fr; gap: 14px; align-items: center; font-size: 15px; line-height: 1.45; color: {t.n700}; }}
.proposal b {{ display: block; color: {t.n900}; font: 600 17px/1.3 '{t.font_display}'; margin-bottom: 2px; }}
.proposal span {{ display: block; }}
.proposal em {{ display: block; font-style: normal; color: {t.n500}; margin-top: 4px; font-size: 14px; }}
.recs {{ margin: 0; padding: 0; list-style: none; counter-reset: r; display: grid; gap: 14px; }}
.recs li {{ counter-increment: r; position: relative; padding: 14px 20px 14px 70px; border: 1px solid {t.n200}; border-radius: {r}px; font-size: 17px; line-height: 1.45; color: {t.n700}; }}
.recs li::before {{ content: counter(r); position: absolute; left: 20px; top: 50%; transform: translateY(-50%); width: 34px; height: 34px; border-radius: 50%; background: {t.primary}; color: {t.on_primary}; font: 600 16px/34px '{t.font_display}'; text-align: center; }}
.recs b {{ color: {t.n900}; }}

/* Previews: one slide at a time, no margin */
body.solo {{ overflow: hidden; }}
"""
