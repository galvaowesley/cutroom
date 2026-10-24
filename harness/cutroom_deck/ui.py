"""Slide layout blocks. Each function returns HTML to pass to Deck.slide(...).

Texts accept simple HTML (<b>, <br>); pass anything from external data through fmt.esc().
Default labels ("How to read", "Verdict"...) are in English; pass your own for other languages.
"""
from .theme import active

# Lucide icons (https://lucide.dev, ISC license), stroke 1.75, rounded joins.
ICONS = {
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "chart": '<path d="M6 20v-4M12 20V10M18 20V4"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "text": '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5M2 12l10 5 10-5"/>',
    "bolt": '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    "arrow": '<path d="M5 12h14M12 5l7 7-7 7"/>',
    "calendar-off": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M10 14l4 4M14 14l-4 4"/>',
    "code": '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    "play": '<circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4z"/>',
    "mic": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/>',
}


def icon(name, size=28, color=None):
    return (f'<svg class="ui-icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color or active().primary}" '
            f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">'
            f'{ICONS[name]}</svg>')


def _list(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def _body(text_or_items):
    if isinstance(text_or_items, (list, tuple)):
        return _list(text_or_items)
    return f"<p>{text_or_items}</p>"


# --- text ----------------------------------------------------------------------------------------

def lead(text):
    """Opening paragraph of the body (18 px)."""
    return f'<p class="lead">{text}</p>'


def paragraph(text, cls=""):
    return f'<p class="txt {cls}">{text}</p>'


def chart_title(text):
    """Short title above a chart: what it measures and in which unit."""
    return f'<h3>{text}</h3>'


def big(value, text):
    """Big number (display font, 300) with the sentence that explains it."""
    return f'<div class="big"><span class="big-v">{value}</span><span class="big-t">{text}</span></div>'


def legend(items):
    """items: [(label, color, shape)] with shape "square", "circle" or "hollow"."""
    t = active()
    parts = []
    for label, color, shape in items:
        style = {"square": f"background:{color}", "circle": f"background:{color};border-radius:50%",
                 "hollow": f"background:{t.background};border:2px solid {color};border-radius:50%"}[shape]
        parts.append(f'<span><i style="{style}"></i>{label}</span>')
    return f'<div class="legend">{"".join(parts)}</div>'


# --- composition ---------------------------------------------------------------------------------

def columns(*blocks, widths=None, gap=24, align="start"):
    """Blocks side by side. widths: CSS grid values (e.g. ("1fr", "440px"))."""
    cols = " ".join(widths) if widths else f"repeat({len(blocks)}, 1fr)"
    children = "".join(f"<div>{b}</div>" for b in blocks)
    return f'<div class="cols" style="grid-template-columns:{cols};gap:{gap}px;align-items:{align}">{children}</div>'


def stack(*blocks, gap=14):
    return f'<div class="stack" style="gap:{gap}px">{"".join(blocks)}</div>'


def center(block):
    return f'<div class="center">{block}</div>'


def card(body, title=None, kicker=None, variant="outline", icon_name=None):
    """variant: "outline" (border), "tint" (light primary fill), "deep" (deep fill, light text)."""
    top = ""
    if icon_name:
        top = f'<div class="card-ic">{icon(icon_name, color=active().on_deep if variant == "deep" else None)}</div>'
    k = f'<p class="k">{kicker}</p>' if kicker else ""
    h = f"<h4>{title}</h4>" if title else ""
    return f'<div class="card {variant}">{top}{k}{h}{_body(body)}</div>'


def cards(items, cols=3, variant="outline"):
    """items: [(title, text)] or [(title, text, icon)]."""
    cs = "".join(card(i[1], title=i[0], variant=variant, icon_name=i[2] if len(i) > 2 else None) for i in items)
    return f'<div class="card-grid" style="grid-template-columns:repeat({cols}, 1fr)">{cs}</div>'


def how_to_read(text_or_items, title="How to read"):
    """Box next to a chart that needs interpretation: what each mark is, what is good and what is bad."""
    return f'<div class="box"><p class="k">{title}</p>{_body(text_or_items)}</div>'


def note(text):
    """Body footnote (besides the slide's source note)."""
    return f'<p class="note">{text}</p>'


def illustrative(text="Illustration with fictitious data."):
    """Required label when an illustration uses fictitious positions or values."""
    return f'<p class="illustrative">{text}</p>'


# --- summary boxes -------------------------------------------------------------------------------

def verdict(headline, text, kicker="Verdict"):
    """Verdict box, on deep: the verdict in one line and the justification with the number."""
    return f'<div class="verdict"><p class="k">{kicker}</p><p class="verdict-v">{headline}</p><p>{text}</p></div>'


def kpi(label, value, note_):
    return (f'<div class="kpi"><span class="kpi-l">{label}</span><span class="kpi-v">{value}</span>'
            f'<span class="kpi-n">{note_}</span></div>')


def kpis(items):
    """items: [(label, value, note)], ideally three."""
    return f'<div class="kpis" style="grid-template-columns:repeat({len(items)}, 1fr)">{"".join(kpi(*i) for i in items)}</div>'


def highlights(items):
    """Up to three short sentences with the number in the middle."""
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<ul class="highlights" style="grid-template-columns:repeat({len(items)}, 1fr)">{lis}</ul>'


def summary(headline, text, kpis_, highlights_, kicker="Verdict"):
    """Standard summary slide: verdict + three numbers on top, three highlights below."""
    top = f'<div class="g-summary">{verdict(headline, text, kicker)}{kpis(kpis_)}</div>'
    return top + highlights(highlights_)


def measure(label, value, description, visual="", reading=""):
    """Card for one measure: name, big value, what it measures, an illustration and how to read it."""
    vis = f'<div class="m-vis">{visual}</div>' if visual else ""
    rd = f'<p class="m-r">{reading}</p>' if reading else ""
    return (f'<div class="measure"><p class="m-l">{label}</p><p class="m-v">{value}</p><p class="m-d">{description}</p>'
            f'{vis}{rd}</div>')


def measures(items):
    """items: [(label, value, description, visual, reading)], usually three, side by side."""
    return f'<div class="measures" style="grid-template-columns:repeat({len(items)}, 1fr)">{"".join(measure(*i) for i in items)}</div>'


def steps(items):
    """items: [(icon, title, text)], numbered in order."""
    ps = []
    for n, (ic, tit, txt) in enumerate(items, 1):
        ps.append(f'<div class="step"><div class="step-top"><span class="num">{n}</span>{icon(ic)}</div>'
                  f'<h4>{tit}</h4><p>{txt}</p></div>')
    return f'<div class="steps" style="grid-template-columns:repeat({len(items)}, 1fr)">{"".join(ps)}</div>'


def use_for(yes, no, titles=("Use for", "Don't use for")):
    """Semantic cards for appropriate use (green and red only here and in strengths_limits)."""
    return (f'<div class="uses"><div class="use yes"><b>{titles[0]}</b>{_body(yes)}</div>'
            f'<div class="use no"><b>{titles[1]}</b>{_body(no)}</div></div>')


def strengths_limits(strengths, limits, verdict_line=None, titles=("Strengths", "Limits")):
    """Verdict in two boxes; optional one-line verdict below."""
    v = f'<p class="verdict-line">{verdict_line}</p>' if verdict_line else ""
    return (f'<div class="g-sl"><div class="box strong"><p class="k">{titles[0]}</p>{_list(strengths)}</div>'
            f'<div class="box limit"><p class="k">{titles[1]}</p>{_list(limits)}</div></div>{v}')


def proposals(items, condition="Condition"):
    """items: [(title, description, adoption condition)] or with a 4th element: icon."""
    cs = []
    for i in items:
        tit, desc, cond = i[:3]
        ic = f'<div class="prop-ic">{icon(i[3])}</div>' if len(i) > 3 else ""
        cs.append(f'<div class="proposal">{ic}<div><b>{tit}</b><span>{desc}</span><em>{condition}: {cond}</em></div></div>')
    return f'<div class="proposals">{"".join(cs)}</div>'


def next_steps(items):
    """items: [(bold part, rest of the sentence)], numbered."""
    lis = "".join(f"<li><b>{b}</b> {t}</li>" for b, t in items)
    return f'<ol class="recs">{lis}</ol>'


def table(header, rows, numeric=()):
    """Plain table; numeric: indexes of right-aligned columns, with tabular figures."""
    th = "".join(f'<th class="{"n" if j in numeric else ""}">{c}</th>' for j, c in enumerate(header))
    trs = "".join("<tr>" + "".join(f'<td class="{"n" if j in numeric else ""}">{c}</td>' for j, c in enumerate(r)) + "</tr>"
                  for r in rows)
    return f'<table class="table"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def code(source, lang=""):
    """Code block on deep, in the brand's mono font (no syntax colors: the deck is for reading)."""
    from .fmt import esc
    return f'<pre class="code" data-lang="{esc(lang)}">{esc(source)}</pre>'
