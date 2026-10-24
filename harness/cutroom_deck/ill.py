"""Illustration catalog: each one explains an interpretation computed from the data (references/illustrations.md).

All return SVG or HTML ready for a slide block and read the active theme's colors. Dataviz rules: one axis per
chart, thin marks, direct labels or a legend, text in text color (not series color).
Illustrations with fictitious values carry the ui.illustrative() label in the block itself.
"""
from itertools import combinations

from . import fmt
from .svg import circle, line, mix, ordinal, path, readable, rect, svg, text
from .theme import active
from .ui import illustrative, legend


# --- timeline ------------------------------------------------------------------------------------

def timeline(labels, milestones=(), span=None, w=1136, h=190):
    """Milestones on an axis with evenly spaced labels.

    labels: tick texts (e.g. months). milestones: [(position, text in the circle, filled)], position in tick
    units (0 = first; fractions allowed). span: (start, end, label) drawn above the axis.
    """
    t = active()
    x0, x1, y = 80, w - 96, h * 0.63
    n = max(1, len(labels) - 1)
    X = lambda p: x0 + (x1 - x0) * p / n  # noqa: E731
    out = [line(x0 - 40, y, x1 + 40, y, t.n300, 2)]
    for i, r in enumerate(labels):
        out.append(line(X(i), y - 8, X(i), y + 8, t.n300, 2))
        out.append(text(X(i), y + 32, r, 14, t.n500, "middle", 600, "display"))
    if span:
        a, b, lab = span
        out.append(path(f"M{X(a):.1f},{y - 42} L{X(a):.1f},{y - 54} L{X(b):.1f},{y - 54} L{X(b):.1f},{y - 42}", t.primary, 2))
        out.append(text((X(a) + X(b)) / 2, y - 66, lab, 16, t.primary, "middle", 600, "display"))
    for p, lab, filled in milestones:
        out.append(circle(X(p), y, 16, t.primary if filled else t.background, "" if filled else t.primary, 2.5))
        out.append(text(X(p), y + 6, lab, 16, t.on_primary if filled else t.primary, "middle", 600, "display"))
    return f'<div class="center">{svg(w, h, "".join(out))}</div>'


# --- ranking queue -------------------------------------------------------------------------------

def queue_auc(positives, n=20):
    """AUC of a queue: share of (positive, negative) pairs where the positive comes first. 0 = front."""
    negatives = n - len(positives)
    if not positives or not negatives:
        return float("nan")
    pairs = sum(sum(1 for j in range(i + 1, n) if j not in positives) for i in positives)
    return pairs / (len(positives) * negatives)


def _best_queue(auc, n, k):
    best, key = None, None
    for comb in combinations(range(n), k):
        s = set(comb)
        err = abs(queue_auc(s, n) - auc)
        spread = -min(b - a for a, b in zip(comb, comb[1:])) if k > 1 else 0
        c = (round(err, 6), spread, comb)
        if key is None or c < key:
            best, key = s, c
    return best


def positions_for_auc(auc, n=20, k=5):
    """Positions of the positives in a queue of n whose AUC, at 2 decimals, is the measured AUC.

    A queue's AUC moves in steps of 1/(k·(n−k)); if k cannot reach the value, tries k±1 and k±2 and returns the
    first queue whose label (fmt.dec) matches. Otherwise the closest one. Ties prefer the most spread out (easier
    to read). Deterministic.
    """
    target = fmt.dec(auc)
    close = []
    for kk in (k, k - 1, k + 1, k - 2, k + 2):
        if 2 <= kk <= n - 2:
            s = _best_queue(auc, n, kk)
            if fmt.dec(queue_auc(s, n)) == target:
                return s
            close.append((abs(queue_auc(s, n) - auc), kk, s))
    return min(close, key=lambda x: (x[0], x[1]))[2]


def queue(positives, n=20, step=34):
    """n items in a row, highest to lowest score; positives filled, the rest hollow."""
    t = active()
    out = []
    for i in range(n):
        cx = 16 + i * step
        out.append(circle(cx, 16, 13, t.primary) if i in positives else circle(cx, 16, 12, t.background, t.n300, 2))
    return svg(32 + (n - 1) * step, 32, "".join(out))


def queue_scenarios(scenarios, n=20, axis=("highest score", "lowest score"), legends=("positive", "negative"),
                    illustrative_=True, label=None, auc_label="AUC"):
    """A queue in several scenarios (e.g. random, current, perfect): what ranking is and what AUC measures.

    scenarios: [(name, positives, label or None)]; None shows "AUC x.xx" computed from the queue itself.
    label: text of the notice under the illustration (default: fictitious positions); illustrative_=False drops it.
    """
    t = active()
    width = 32 + (n - 1) * 34
    aw = min(480, width - 80)
    arrow = svg(aw, 16, path(f"M4,8 L{aw - 8},8 M{aw - 20},2 L{aw - 8},8 L{aw - 20},14", t.n500, 1.5))
    rows = "".join(
        f'<div class="queue"><div class="queue-l"><b>{name}</b><span>{lab or auc_label + " " + fmt.dec(queue_auc(pos, n))}</span></div>{queue(pos, n)}</div>'
        for name, pos, lab in scenarios)
    leg = legend([(legends[0], t.primary, "circle"), (legends[1], t.n300, "hollow")])
    notice = label or f"Illustration with {n} items and fictitious positions, chosen to reproduce each scenario's AUC."
    seal = illustrative(notice) if illustrative_ else ""
    return (f'<div class="queues"><div class="queue-axis"><span>{axis[0]}</span>{arrow}<span>{axis[1]}</span></div>'
            f'{rows}{leg}{seal}</div>')


# --- scale ---------------------------------------------------------------------------------------

def scale(value, lo, hi, criterion=None, refs=(), ends=("", ""), w=320, f=fmt.dec):
    """Where a value sits between the minimum and the ideal.

    criterion: (value, label), dashed above the bar. refs: [(value, label)] as hollow circles labeled below.
    ends: labels of lo and hi (e.g. ("0.5 = random", "1.0 = perfect")).
    """
    t = active()
    S = lambda v: 12 + (w - 24) * (min(max(v, lo), hi) - lo) / (hi - lo)  # noqa: E731

    def anchor(x):  # labels near an edge align to it, so they are not cut
        return ("start", max(x - 8, 0)) if x < w * 0.25 else (("end", min(x + 8, w)) if x > w * 0.75 else ("middle", x))
    out = [rect(12, 52, w - 24, 12, t.n200, 6), rect(12, 52, S(value) - 12, 12, t.primary, 6)]
    if criterion:
        cv, cr = criterion
        out.append(line(S(cv), 40, S(cv), 76, t.n700, 2, "4 3"))
        a, x = anchor(S(cv))
        out.append(text(x, 32, cr, 13, t.n700, a, 600, "display"))
    for i, (rv, rr) in enumerate(refs):
        out.append(circle(S(rv), 58, 7, t.background, t.n500, 2.5))
        a, x = anchor(S(rv))
        out.append(text(x, 96 + 16 * i, rr, 13, t.n500, a))
    base = 124 + 16 * max(0, len(refs) - 1)
    out.append(text(12, base, ends[0], 13, t.n500))
    out.append(text(w - 12, base, ends[1], 13, t.n500, "end"))
    return svg(w, base + 8, "".join(out))


# --- 10 x 10 grid --------------------------------------------------------------------------------

def grid(k, total=100, cols=10, size=13, gap=5, color=None):
    """"k out of 100": rate, coverage, precision, frequency. k is rounded to an integer."""
    t = active()
    k = round(k)
    out = []
    for i in range(total):
        r, c = divmod(i, cols)
        out.append(circle(c * (size + gap) + size / 2, r * (size + gap) + size / 2, size / 2,
                          (color or t.primary) if i < k else t.n200))
    side = cols * (size + gap) - gap
    rows = -(-total // cols)
    return svg(side, rows * (size + gap) - gap, "".join(out))


# --- concentration bars --------------------------------------------------------------------------

def concentration_bars(base, segment, labels=("Average", "Segment"), f=fmt.pct, w=320, h=180):
    """Base rate x segment rate (lift = segment / base)."""
    t = active()
    top = max(base, segment) or 1
    out = []
    for i, (lab, v, color) in enumerate([(labels[0], base, t.n300), (labels[1], segment, t.primary)]):
        x = 30 + i * 140
        hh = (h - 62) * v / top
        out.append(rect(x, h - 30 - hh, 90, hh, color, 6))
        out.append(text(x + 45, h - 38 - hh, f(v), 15, t.n900, "middle", 600, "display"))
        out.append(text(x + 45, h - 8, lab, 13, t.n500, "middle"))
    return svg(w, h, "".join(out))


# --- lines ---------------------------------------------------------------------------------------

def lines(series, w, h, ydom, yticks, yfmt, refs=(), hollow=(), xfmt=str, label_last=True, mr=70):
    """Line chart with a shared categorical x. series: [(name, color, [(x, y)])].

    refs: [(y, label)] dashed. hollow: x values whose points are hollow (not comparable).
    """
    t = active()
    xs = series[0][2]
    ml, mt, mb = max(46, 14 + 7 * max(len(yfmt(tk)) for tk in yticks)), 14, 30
    n = len(xs)
    X = lambda i: ml + (w - ml - mr) * (i / max(1, n - 1))  # noqa: E731
    Y = lambda v: mt + (h - mt - mb) * (1 - (v - ydom[0]) / (ydom[1] - ydom[0]))  # noqa: E731
    out = []
    for tk in yticks:
        out.append(line(ml, Y(tk), w - mr, Y(tk), t.n200, 1))
        out.append(text(ml - 8, Y(tk) + 4, yfmt(tk), 12, t.n500, "end"))
    for i, (x, _) in enumerate(xs):
        out.append(text(X(i), h - 8, xfmt(x), 12, t.n500, "middle"))
    for v, lab in refs:
        out.append(line(ml, Y(v), w - mr, Y(v), t.n500, 1.2, "5 5"))
        out.append(text(w - mr + 8, Y(v) + 4, lab, 12, t.n500))
    ends = []
    for name, color, pts in series:
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(i):.1f},{Y(v):.1f}" for i, (_, v) in enumerate(pts))
        out.append(path(d, color, 2.5))
        for i, (x, v) in enumerate(pts):
            out.append(circle(X(i), Y(v), 5, t.background if x in hollow else color, color, 2.5))
        if label_last and name:
            ends.append([Y(pts[-1][1]) + 4, name, color])
    ends.sort()
    for i in range(1, len(ends)):  # push apart end labels that touch (16 px minimum)
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 16)
    for y, name, color in ends:
        out.append(circle(X(len(xs) - 1) + 14, y - 4, 4, color))
        out.append(text(X(len(xs) - 1) + 22, y, name, 13, t.n900, weight=600))
    return svg(w, h, "".join(out))


def small_multiples(panels, xfmt=str, w=370, h=300):
    """One measure per panel, each on its own axis, same x.

    panels: [dict(title=, points=[(x, y)], ydom=(a, b), yticks=[...], yfmt=callable, refs=[(y, label)], hollow=set())].
    """
    t = active()
    blocks = []
    for p in panels:
        g = lines([("", t.primary, p["points"])], w, h, p["ydom"], p["yticks"], p["yfmt"], p.get("refs", ()),
                  p.get("hollow", ()), xfmt, label_last=False)
        blocks.append(f"<div><h3>{p['title']}</h3>{g}</div>")
    return f'<div class="multiples" style="grid-template-columns:repeat({len(panels)}, 1fr)">{"".join(blocks)}</div>'


# --- composition and availability ----------------------------------------------------------------

def composition(parts, w=1136, h=34, f=fmt.pct, label_min=70, with_legend=False):
    """Stacked bar: how the base splits into segments. parts: [(label, share)], in order."""
    total = sum(p for _, p in parts) or 1
    out, x0, colors = [], 0.0, []
    for i, (lab, p) in enumerate(parts):
        color = ordinal(len(parts) - 1 - i, len(parts))
        colors.append(color)
        wg = w * p / total
        out.append(rect(x0, 0, max(wg - 2, 1), h, color, 6))
        if wg > label_min:
            out.append(text(x0 + 10, h / 2 + 5, f"{lab} · {f(p / total)}", 14, readable(color), weight=600, family="display"))
        x0 += wg
    bar = svg(w, h, "".join(out))
    if not with_legend:
        return bar
    items = "".join(f'<div><i style="background:{c}"></i><span>{r}</span><b>{f(p / total)}</b></div>'
                    for (r, p), c in zip(parts, colors))
    return f'{bar}<div class="comp-list">{items}</div>'


def availability(items, w=490, f=fmt.pct):
    """Coverage by source: % of the base that has each piece of information. items: [(label, coverage 0..1)]."""
    t = active()
    out = []
    width = w - 70
    for i, (lab, v) in enumerate(items):
        y = i * 38
        out.append(text(0, y + 15, lab, 15, t.n900, weight=600, family="display"))
        out.append(rect(0, y + 22, width, 14, t.n100, 5))
        out.append(rect(0, y + 22, max(3, width * v), 14, t.primary, 5))
        out.append(text(width + 10, y + 34, f(v), 14, t.n900, weight=600, family="display"))
    return svg(w, len(items) * 38, "".join(out))


# --- table with mini scale -----------------------------------------------------------------------

def mini_scale(value, lo, hi, ci_=None, criterion=None, chance=None, w=184, h=26):
    t = active()
    S = lambda v: 4 + (w - 8) * (min(max(v, lo), hi) - lo) / (hi - lo)  # noqa: E731
    out = [rect(4, h / 2 - 2, w - 8, 4, t.n200, 2)]
    if chance is not None:
        out.append(line(S(chance), 5, S(chance), h - 5, t.n500, 1))
    if criterion is not None:
        out.append(line(S(criterion), 3, S(criterion), h - 3, t.n700, 1.5, "3 2"))
    if ci_:
        out.append(line(S(ci_[0]), h / 2, S(ci_[1]), h / 2, t.primary, 3))
        out.append(line(S(ci_[0]), h / 2 - 5, S(ci_[0]), h / 2 + 5, t.primary, 1.5))
        out.append(line(S(ci_[1]), h / 2 - 5, S(ci_[1]), h / 2 + 5, t.primary, 1.5))
    out.append(circle(S(value), h / 2, 7, t.primary))
    return svg(w, h, "".join(out))


def segment_table(rows, scale_, f=fmt.pct, criterion=None, chance=None, header=("Segment", "% of base", "Result"),
                  extras=()):
    """Result by segment: one row per segment, with a mini scale, value and CI.

    rows: [dict(name=, sub=, share=, value=, ci=(lo, hi), extras=[...])]; scale_: (lo, hi).
    extras: titles of extra columns (values come in row["extras"], already formatted).
    """
    to = "to" if fmt.locale() == "en" else "a"
    th = (f'<th>{header[0]}</th><th class="n">{header[1]}</th><th>{header[2]}</th>'
          + "".join(f'<th class="n">{e}</th>' for e in extras))
    trs = []
    for r in rows:
        ci_ = r.get("ci")
        val = f(r["value"]) + (f' <span class="sub">({f(ci_[0])} {to} {f(ci_[1])})</span>' if ci_ else "")
        sub = f'<br><span class="sub">{r["sub"]}</span>' if r.get("sub") else ""
        bar = mini_scale(r["value"], *scale_, ci_=ci_, criterion=criterion, chance=chance)
        ext = "".join(f'<td class="n">{e}</td>' for e in r.get("extras", ()))
        trs.append(f'<tr><td><b>{r["name"]}</b>{sub}</td><td class="n">{fmt.pct(r["share"])}</td>'
                   f'<td class="seg">{bar}<span>{val}</span></td>{ext}</tr>')
    return f'<table class="table seg-tab"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


# --- paired bars ---------------------------------------------------------------------------------

def paired_bars(levels, labels=("% of base", "% of outcome"), w=760, h=300, f=fmt.pct, d=0):
    """Whether levels concentrate the outcome: % of base x % of outcome per level.

    levels: [(label, share of base, share of outcome, sub-label)].
    """
    t = active()
    top = max(max(b, o) for _, b, o, _ in levels) or 1
    step = (w - 40) / len(levels)
    bw = min(52, step / 2 - 8)
    out = []
    for i, (lab, vb, vo, sub) in enumerate(levels):
        cx = 20 + step * (i + 0.5)
        for j, (v, color) in enumerate([(vb, t.n300), (vo, t.primary)]):
            hh = (h - 90) * v / top
            x = cx - bw - 2 + j * (bw + 4)
            out.append(rect(x, h - 60 - hh, bw, hh, color, 6))
            out.append(text(x + bw / 2, h - 68 - hh, f(v, d), 14, t.n900, "middle", 600, "display"))
        out.append(text(cx, h - 34, lab, 14, t.n900, "middle", 600, "display"))
        if sub:
            out.append(text(cx, h - 12, sub, 13, t.n500, "middle"))
    leg = legend([(labels[0], t.n300, "square"), (labels[1], t.primary, "square")])
    return leg + svg(w, h, "".join(out))


# --- heatmap -------------------------------------------------------------------------------------

def heatmap(rows, cols, values, f=fmt.pct, intensity=None, label_w=86, cell_w=72, cell_h=34):
    """Heatmap table (evolution by cohort or period). values[i][j] may be None (empty).

    intensity: function value -> 0..1 (default: min to max of the matrix). Darker = more intense.
    """
    t = active()
    vals = [v for row in values for v in row if v is not None]
    lo, hi = (min(vals), max(vals)) if vals else (0, 1)
    I = intensity or (lambda v: (v - lo) / (hi - lo) if hi > lo else 0.5)  # noqa: E741
    w = label_w + cell_w * len(cols)
    h = 28 + cell_h * len(rows)
    out = [text(label_w + cell_w * j + cell_w / 2, 18, c, 12, t.n500, "middle", 600, "display") for j, c in enumerate(cols)]
    for i, r in enumerate(rows):
        y = 28 + cell_h * i
        out.append(text(0, y + cell_h / 2 + 5, r, 13, t.n900, weight=600, family="display"))
        for j, v in enumerate(values[i]):
            if v is None:
                continue
            k = I(v)
            bg = mix(t.scale[0], t.scale[-1], k)
            x = label_w + cell_w * j
            out.append(rect(x + 2, y + 2, cell_w - 4, cell_h - 4, bg, 6))
            out.append(text(x + cell_w / 2, y + cell_h / 2 + 5, f(v), 13, "#FFFFFF" if k > 0.55 else t.n900, "middle"))
    return svg(w, h, "".join(out))


# --- weights and waterfall -----------------------------------------------------------------------

def hbars(items, w, maxv=None, f=fmt.dec, label_w=250, bar_h=22, gap=14, highlight_first=True):
    """Horizontal bars with the label on the left and the value on the right. items: [(label, value)]."""
    t = active()
    maxv = maxv or max(v for _, v in items) or 1
    out = []
    for i, (lab, v) in enumerate(items):
        y = i * (bar_h + gap)
        bw = (w - label_w - 70) * v / maxv
        out.append(text(label_w - 12, y + bar_h / 2 + 5, lab, 15, t.n900, "end"))
        color = t.primary if (i == 0 or not highlight_first) else t.scale[3]
        out.append(rect(label_w, y, max(2, bw), bar_h, color, 5))
        out.append(text(label_w + max(2, bw) + 8, y + bar_h / 2 + 5, f(v), 14, t.n700))
    return svg(w, len(items) * (bar_h + gap) - gap, "".join(out))


def weights(items, f=fmt.dec, w=640, label_w=290):
    """Weight of each factor (explainability): the first highlighted, the rest on the scale."""
    return hbars(items, w, None, f, label_w)


def waterfall(steps, w=470, f=fmt.dec, illustrative_=True, scale_max=None):
    """How contributions add up to a result. steps: [(label, value, kind)] with kind "base", "delta" or "total".
    Base and total start at zero; each delta starts at the running total.
    """
    t = active()
    acc, vals = 0.0, []
    for lab, v, kind in steps:
        if kind == "delta":
            vals.append((lab, acc, acc + v, kind, v))
            acc += v
        else:
            vals.append((lab, 0.0, v, kind, v))
            acc = v
    top = scale_max or max(max(a, b) for _, a, b, _, _ in vals) * 1.1 or 1
    X = lambda v: 190 + (w - 250) * v / top  # noqa: E731
    out = []
    for i, (lab, a, b, kind, v) in enumerate(vals):
        y = 8 + i * 34
        lo, hi = sorted((a, b))
        color = t.n700 if kind == "base" else (t.primary if (kind == "total" or v > 0) else t.n500)
        out.append(text(180, y + 16, lab, 13, t.n900, "end"))
        out.append(rect(X(lo), y + 4, max(2, X(hi) - X(lo)), 18, color, 4))
        val = f(v) if kind != "delta" else (("+" if v > 0 else "−") + f(abs(v)))
        out.append(text(X(hi) + 6, y + 18, val, 12, t.n700))
    seal = illustrative("Illustrative example, fictitious values.") if illustrative_ else ""
    return svg(w, 8 + len(vals) * 34, "".join(out)) + seal


# --- event strip ---------------------------------------------------------------------------------

def event_strip(sources, days=30, w=530, cell=12):
    """How often each source changes: a strip of `days` cells per source, filled on days with an event.

    sources: [(name, set of days 0..days-1, note)].
    """
    t = active()
    out = []
    for i, (name, ds, note_) in enumerate(sources):
        y = 6 + i * 44
        out.append(text(150, y + 14, name, 14, t.n900, "end", 600, "display"))
        for d in range(days):
            out.append(rect(160 + d * cell, y + 2, cell - 3, 16, t.primary if d in ds else t.n100, 2))
        out.append(text(160, y + 34, note_, 12, t.n500))
    return svg(max(w, 160 + days * cell), 6 + len(sources) * 44, "".join(out))
