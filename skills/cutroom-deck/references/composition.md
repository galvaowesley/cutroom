# Slide composition

A pattern approved in a leadership presentation (evaluating an ML model) and generalized to any subject. The
library CSS (`cutroom_deck/render.py`) already applies the measures below; colors come from the brand.

## Format and structure

- **Page:** 1280 × 720 px (16:9), margins of 52 px top, 72 px sides and 44 px bottom.
- **Each slide, top to bottom** (`deck.slide(eyebrow, title, *blocks, source=...)` builds all of it):
  1. **eyebrow:** the slide's topic in 1 to 3 words, uppercase, in primary ("Summary", "By region");
  2. **title:** the slide's message in one factual sentence with the number, at most 2 lines (display font 600,
     32 px). E.g. "First-place accuracy goes from 84.2% in the Southeast to 87.7% in the South". A label like
     "Results by region" does not qualify;
  3. **body:** chart and boxes;
  4. **source note:** where the number comes from and the period (source, extraction date, window, cut);
  5. **footer:** the piece's name and page number.
- **One message per slide.** If the body needs two messages, that is two slides.
- **Body text 13 px or more.** Chart labels and uppercase labels may be 12 px.
- **A chart that needs interpretation gets a "How to read" box** (`ui.how_to_read`): what each mark is, what is good
  and bad, and what the title's number means.

## Standard arc

Adapt to the subject. **The concept always comes before the evidence that depends on it.**

| # | Slide | Typical blocks |
|---|---|---|
| 1 | Cover | `deck.cover`: eyebrow (team or context), title, subtitle, meta (what was measured and when) |
| 2 | Summary | `ui.summary`: verdict box, three numbers, three highlights |
| 3 | How we measured / where the data comes from | `ill.timeline` + `ui.steps` |
| 4 | One slide per concept the audience needs | the concept's illustration + `ui.how_to_read` (e.g. `ill.queue_scenarios` for ranking) |
| 5 | Evidence: the measures, the trend, the segments | `ui.measures`, `ill.small_multiples`, `ill.segment_table`, `ill.paired_bars`, `ill.heatmap` |
| 6 | Why the result is what it is: explainability, causes, hypotheses | `ill.weights`, `ill.waterfall`, hypothesis cards with evidence for and against |
| 7 | Verdict | `ui.strengths_limits` with the one-line verdict |
| 8 | How to use it today | `ui.use_for` + the why (e.g. `ill.grid`) |
| 9 | Next steps | `ui.proposals` (with the adoption condition) or `ui.next_steps` |
| 10 | Close | `deck.closing`: final message, contacts or links, and the logo |

Short decks (status, proposal) can go from 1 and 2 straight to 5, 8 and 9. A post-mortem replaces 3 to 6 with:
what happened → measured impact → cause with evidence → what changes.

## Audience

If the request does not say, ask.

- **Executive:** few measures, each defined in plain language without being childish ("ranking", "coverage",
  "concentration"), with the technical name next to it ("AUC · ranking"); percentages rather than absolute numbers;
  no code-level recommendations; talk about the nature of the data (what it is, who has it, how often it changes, how
  much is missing).
- **Technical:** full detail: intervals, criteria and sample sizes; definitions; technical recommendations; the
  method's limits.

## Brand

The deck uses the active brand (`cutroom brand show`), or `Theme.from_brand("<name>")`. A brand the person asks for
wins. The brand's `DESIGN.md` has the final word; the library maps it like this:

- **Colors:** `primary` is the constant accent (main bars, big values, eyebrow); `deep` holds the verdict box and
  code; `scale` (light → dark) colors ordinals (levels, groups, heatmaps); `success` and `danger` appear only in
  "use for / don't use for" and `warning` in "strengths / limits". Brand colors never stand for states.
- **Type:** display 600 for titles and 300 for big numbers; text font for body; mono for code.
- **Background:** solid. Only the cover carries the soft accent glow in one corner (if the brand's `cover.glow`).
- **Logo:** `on_primary` on the cover and `on_light` on the closing slide, and nowhere else.

## Data visualization

Follow the agent's dataviz skill if it has one (in Claude Code, `dataviz`).

- one axis per chart; for measures on different scales, small multiples (`ill.small_multiples`);
- thin marks: 2.5 px lines and 5 px points;
- a legend or direct labels (lines already label their last point);
- text in the text color, not the series color;
- hollow points for what is not comparable (another version, an incomplete period, a reference).

## Verification

`deck check` must pass; then `deck preview`, looking at the grid and every page. Check what the check cannot see:

- labels touching inside a chart;
- a legend that does not match its color;
- a title that does not match the chart's number;
- a concept used before it is explained;
- a fictitious illustration without the label.
