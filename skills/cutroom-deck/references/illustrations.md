# Illustration catalog (`cutroom_deck.ill` and `cutroom_deck.ui`)

Each illustration explains one interpretation; none is decoration. If the slide does not need the interpretation,
do not use the illustration. Illustrative data (fictitious positions, a conceptual waterfall) is flagged on the slide
itself, with the label the function adds or `ui.illustrative()`.

Every function returns SVG or HTML to pass to `deck.slide(...)` and reads the active theme's colors.

| Illustration | Explains | Call | Input |
|---|---|---|---|
| Timeline with milestones | when something was done, measured and checked; the steps of a process | `ill.timeline(labels, milestones=[(pos, "1", filled)], span=(i, j, label))` | tick labels; milestones in tick units |
| Queue of N items in scenarios | what ranking is and what a ranking metric (AUC) measures | `ill.queue_scenarios([(name, positives, label)], n=20, axis=(...), legends=(...), label=...)` | positions of the positives (0 = front) |
| … positions that reproduce an AUC | choose each scenario's positions from the measured AUC | `ill.positions_for_auc(auc, n=20, k=5)` → `set`; `ill.queue_auc(pos, n)` | measured AUC (the 2-decimal label matches) |
| Scale with markers | where a value sits between the minimum and the ideal, with criterion and references | `ill.scale(value, lo, hi, criterion=(v, label), refs=[(v, label)], ends=(...), f=fmt.pct)` | value, limits, criterion, references |
| 10 × 10 grid | "k out of 100": rate, coverage, precision, frequency | `ill.grid(k)` | k (rounded) |
| Average × segment bars | concentration (lift): how many times the base rate the segment has | `ill.concentration_bars(base, segment, labels=(...))` | two rates |
| Small multiples | the trend of several measures, each on its own axis | `ill.small_multiples([dict(title, points, ydom, yticks, yfmt, refs, hollow)], xfmt)` | series with the same x; hollow = not comparable |
| Comparative lines | two or three series on the same axis (method A × B) | `ill.lines([(name, color, points)], w, h, ydom, yticks, yfmt, refs, hollow, xfmt)` | series with the same x |
| Stacked composition bar | how the base splits into segments | `ill.composition([(label, share)], with_legend=True)` | shares (add to 1) |
| Availability bars | how much of the base has each piece of information | `ill.availability([(label, coverage)])` | coverage 0 to 1 |
| Table with a mini scale per row | result by segment, with CI | `ill.segment_table([dict(name, sub, share, value, ci, extras)], scale_=(lo, hi), criterion=, chance=)` | value and CI per row (`fmt.wilson`) |
| Paired bars | whether levels concentrate the outcome: % of base × % of outcome | `ill.paired_bars([(level, share_base, share_outcome, sub)], labels=(...))` | two proportions per level |
| Heatmap | evolution by cohort or period; a cross of two cuts | `ill.heatmap(rows, cols, values, f, intensity=)` | matrix (None = empty) |
| Weight bars | explainability: each factor's weight | `ill.weights([(label, weight)], f)` | weights |
| Waterfall | how contributions add up to a result | `ill.waterfall([(label, value, "base"/"delta"/"total")], illustrative_=True)` | steps; real or conceptual (labeled) |
| 30-day strip per source | how often each data source changes | `ill.event_strip([(name, days, note)], days=30)` | days with an event per source |
| Horizontal bars | simple ranking with values | `ill.hbars([(label, value)], w)` | values |
| Use for / don't use for | appropriate use | `ui.use_for(yes, no)` | short lists |
| Strengths / limits | verdict | `ui.strengths_limits(strengths, limits, verdict_line=)` | short lists |
| Proposal cards | candidate paths with their adoption condition | `ui.proposals([(title, description, condition, icon)])` | title, description, condition |
| Code | a short code listing on deep | `ui.code(source, lang)` | text |

## Common parameters

Full parameters are in the docstrings of `cutroom_deck/ill.py` and `cutroom_deck/ui.py`. The frequent ones:

| Parameter | Where | For |
|---|---|---|
| `w`, `h` | almost all | SVG width and height in px. Required in `hbars` and `lines` |
| `f` | scale, bars, waterfall, heatmap, segment table, weights | value formatter: `fmt.pct` (default in most), `fmt.dec`, `fmt.num`, `fmt.size`, `fmt.duration` or a `lambda` |
| `label_w` | `hbars`, `weights` (250/290), `heatmap` (86) | width of the label column on the left |
| `cell_w`, `cell_h` | `heatmap` (72 × 34) | cell size; the column header must fit `cell_w` |
| `size`, `gap` | `grid` (13 and 5) | dot diameter and spacing |
| `highlight_first` | `hbars` | first bar in primary and the rest on the scale (default `True`) |
| `hollow` | `lines`, `small_multiples` | x values with hollow points (not comparable) |
| `illustrative_`, `label` | `queue_scenarios`, `waterfall` | the fictitious-data notice; `illustrative_=False` when the example is real |
| `titles` | `use_for`, `strengths_limits` | the two boxes' titles (e.g. in another language) |
| `cols` | `cards` | number of card columns |

## Layout blocks (`ui`)

| Block | Use |
|---|---|
| `ui.summary(headline, text, kpis, highlights)` | summary slide: verdict on deep, three numbers and three highlights |
| `ui.verdict`, `ui.kpis`, `ui.highlights` | the summary's parts, separately |
| `ui.measures([(label, value, description, visual, reading)])` | measures side by side, each with its illustration |
| `ui.how_to_read(text_or_items, title="How to read")` | interpretation box next to a chart |
| `ui.columns(*blocks, widths=("1fr", "440px"), gap=24)` and `ui.stack(*blocks)` | composition |
| `ui.card(body, title, kicker, variant="outline"/"tint"/"deep")`, `ui.cards` | cards |
| `ui.steps([(icon, title, text)])` | numbered steps; take the full row (one card per step). Next to another block, use `ui.cards(..., cols=2)` |
| `ui.lead`, `ui.paragraph`, `ui.chart_title`, `ui.note`, `ui.big(value, text)` | text |
| `ui.table(header, rows, numeric)` and `ui.legend([(label, color, shape)])` | table and legend |
| `ui.icon(name)` | Lucide icons: calendar, clock, chart, search, database, document, check, alert, users, sliders, pin, text, layers, bolt, arrow, calendar-off, code, play, mic, image |

## Tips

- **Width:** the body is 1136 px. In `ui.columns`, add the SVG widths and gaps: `check` reports what does not fit.
- **Ranking queue:** with a single right item (search, recommendation), pass its real position (`{position - 1}`).
  To reproduce a model's AUC with many positives, use `positions_for_auc`. Say in the label what is real and what
  is illustrative.
- **Heatmap:** pass `intensity` so color follows what matters (e.g. darker = more failures). For a presence matrix
  (yes/no), `intensity=lambda v: 1.0 if v else 0.0` and `f=lambda v: "✓" if v else ""`. Widen `cell_w` until the
  longest column header fits: `check` reports a cut label.
- **`<b>` inside cards:** plain bold. Only the titles of `use_for` and `strengths_limits` have their own style.
- **End labels:** lines push apart end labels that touch. Look at the preview anyway.
