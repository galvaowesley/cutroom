---
name: cutroom-deck
description: "Builds 16:9 PDF presentations (1280 x 720) in the active brand, on any subject: project results, model evaluation, proposal, status, post-mortem, explaining a concept. Each slide has an eyebrow, a title that states the message with the number, a body and a source note. Illustrations are computed from the data: timeline, ranking queue that reproduces the AUC, scale, 10 x 10 grid, small multiples, composition, table with CIs, paired bars, heatmap, weights and waterfall. Also delivers self-contained HTML, a preview grid, and a layout check in Chrome; the same deck renders in any brand. Use when asked for a presentation, deck, slides or PDF report for leadership, a team or a client, or a PDF of results with charts. Video of slides goes to cutroom-motion. Usage: cutroom-deck <subject> [audience=executive|technical] [brand=<name>]"
metadata:
  version: "2.0.0"
---

# cutroom-deck: PDF presentations (cutroom_deck)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`. They include the brand rules.

`cutroom` = `~/.local/share/cutroom/bin/cutroom`. The `deck` shortcut runs the `cutroom_deck` library
(`~/.local/share/cutroom/harness/cutroom_deck/`, standard library only). Read this skill's references too:

| Reference | For |
|---|---|
| `references/composition.md` | format, slide structure, arc, audiences and brand |
| `references/illustrations.md` | catalog: what each illustration explains, its input and the call |
| `references/tone.md` | tone, numbers, sums, intervals, proposals |

## Step 0: component

Run `cutroom doctor --json` and check `components.deck.installed`. It downloads nothing (the library ships with the
harness) and only needs Chrome. If missing, offer `cutroom-init deck`.

## Step 1: folder, audience and script

1. Run `cutroom job "<title>"` and keep the path as `$J`. Small inputs (CSV, JSON) go to `$J/src/`, large raw data
   to `$J/work/`. Long documents go through `cutroom-extract` first.
2. Numbers: a `$J/src/data.py` reads the sources and writes `$J/src/results.json` with what the deck uses (CSV, the
   output of a CLI saved to a file, a query, extracted Markdown). When the source is text (a README, an email), copy
   the value into a JSON with the file and line it came from. `deck.py` only reads `results.json`.
3. Audience: if the request does not say, ask (executive or technical; see `references/composition.md`).
4. Script with `cutroom-script`: `$J/src/SCRIPT.md` with the facts table, the key message and one slide per scene,
   the title already written as a message. Run `cutroom script check "$J/src/SCRIPT.md"` until it passes. Long decks
   or decks leaving the team: confirm the script before building.
5. Brand: the active one (`cutroom brand show --json`), or the one requested. Read its `DESIGN.md`.

## Step 2: `deck.py`

The deck is a script, `$J/src/deck.py`, that reads the data and builds the slides. A script, not JSON, because
illustrations compute their geometry from the numbers and sentences depend on them.

```python
import json
from pathlib import Path
from cutroom_deck import Deck, Theme, fmt, ill, ui
from cutroom_deck.fmt import pct, dec, num

R = json.loads(Path(__file__).with_name("results.json").read_text())   # numbers: never typed by hand
SOURCE = "Source: ..., period ..."

deck = Deck("Piece title", footer="Team · Piece · edition", slug="my-piece", lang="en")   # theme=Theme.from_brand("acme")
deck.cover("Eyebrow", "Title", "Subtitle with the key message", "meta: what was measured and when")
deck.slide("Summary", f"Factual sentence with the number: {pct(R['rate'])} ...",
           ui.summary("Verdict in one line", "Justification with the number and the reference.",
                      [("Measure 1", pct(R["m1"]), "reference"), ("Measure 2", ...), ("Measure 3", ...)],
                      ["highlight 1", "highlight 2", "highlight 3"]),
           source=SOURCE)
deck.slide("What ranking is", "...", ill.queue_scenarios([...]), ui.columns(ui.how_to_read("..."), ui.how_to_read("...")),
           source="...")
deck.closing("Final message", ["contact or link"], signature="Team")
```

- The full API is in the catalog (`references/illustrations.md`) and in the docstrings of `cutroom_deck/ui.py` and
  `cutroom_deck/ill.py`. The repository example `examples/deck-fuzzy-search/src/deck.py` uses almost everything.
- **Numbers:** every number comes from the data, including those inside sentences ("1 in 7" is `round(1 / miss)`).
  Add and divide raw values and format at the end with `fmt.pct`, `fmt.dec`, `fmt.num`, `fmt.mult`, `fmt.size`
  (bytes) and `fmt.duration` (seconds). They follow the deck's `lang` (English: 5,571 and 85.5%; Portuguese: 5.571 e
  85,5%). Keep the source's decimals: if it says "14.0 s", do not write "14 s".
- **Texts:** simple HTML (`<b>`). Text from data goes through `fmt.esc()`. Default labels ("How to read",
  "Verdict", "Use for") are English: pass your own for other languages (`ui.how_to_read(..., title="Como ler")`).
- **Cover:** the title is the piece's name and the subtitle carries the key message.
- **Fictitious illustrations** (queue positions, conceptual waterfall) carry the illustrative label, which the
  functions add, or `ui.illustrative()`.
- **Brand:** the active brand by default; `Deck(..., theme=Theme.from_brand("paper"))` in the script, or
  `deck build "$J" --brand paper` to render the same deck in another brand. No color is fixed in the illustrations.

## Step 3: build and check

```bash
. ~/.local/share/cutroom/env.sh && deck build "$J" && deck check "$J" && deck preview "$J"
```

- `deck build` runs `src/deck.py` and writes `out/<slug>.pdf` and `out/<slug>.html`. The HTML is self-contained
  (fonts and logos embedded) and can be published as a page.
- `deck check` runs the check in Chrome and exits 1 on: text leaving the slide or its box; a chart shrunk for lack of
  room; a title over 2 lines; an element over the footer; body text under 13 px (12 px for chart labels); a cut chart
  label; a font that did not load. Fix `deck.py` and repeat until it passes. With a `src/SCRIPT.md`, it also warns
  (without failing) when a slide title differs from the "On screen" of scene `slide N`: align one of them.
- `deck preview` writes one PNG per page to `work/preview/` and the grid to `out/<slug>-grid.png`. **Open the grid
  and every page.** The check does not see labels touching inside a chart, a sentence that does not match its number,
  or an illustration that does not explain what the title says. For small text, `--scale 0.75`.

## Step 4: deliver

- Deliver `$J/out/<slug>.pdf`, the HTML next to it, and the sources (`src/deck.py`, data, `SCRIPT.md`).
- Agents that publish pages can turn the HTML into an artifact directly (in Claude, load `artifact-design` first).
- Say what was not verified (data from a source you did not check) and where each number comes from.
