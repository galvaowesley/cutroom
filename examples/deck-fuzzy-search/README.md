# Example: fuzzy search over municipality names (cutroom-deck)

**Request:** "Evaluate fuzzy search over Brazilian municipality names: compare exact matching, Levenshtein distance on raw text, and Levenshtein after accent stripping. Present as a technical deck in 16:9 PDF format."

<p align="center"><img src="out/fuzzy-search-municipalities-grid.png" width="800" alt="17-slide contact sheet of the fuzzy search presentation in the cutroom brand"></p>

[`out/fuzzy-search-municipalities.pdf`](out/fuzzy-search-municipalities.pdf) (17 slides, 16:9 PDF, 362 KB) · [`out/fuzzy-search-municipalities.html`](out/fuzzy-search-municipalities.html) (self-contained HTML, 2.0 MB) · [`out/fuzzy-search-municipalities-paper.pdf`](out/fuzzy-search-municipalities-paper.pdf) (alternative paper brand, 387 KB) · source in [`src/`](src)

| File | Description |
|---|---|
| [`out/fuzzy-search-municipalities.pdf`](out/fuzzy-search-municipalities.pdf) | Deliverable: 17-slide presentation in PDF (16:9, cutroom brand), 362 KB |
| [`out/fuzzy-search-municipalities.html`](out/fuzzy-search-municipalities.html) | Self-contained HTML presentation (embedded styles and SVG figures), 2.0 MB |
| [`out/fuzzy-search-municipalities-grid.png`](out/fuzzy-search-municipalities-grid.png) | 17-slide preview contact sheet grid, 606 KB |
| [`out/fuzzy-search-municipalities-paper.pdf`](out/fuzzy-search-municipalities-paper.pdf) | Alternative brand build in `paper` (editorial serif theme), 387 KB |
| [`out/fuzzy-search-municipalities-paper-grid.png`](out/fuzzy-search-municipalities-paper-grid.png) | 17-slide preview grid in `paper` brand, 609 KB |
| [`src/ibge_municipalities.csv`](src/ibge_municipalities.csv) | Official list from IBGE localities API: 5,571 municipalities, 5,298 distinct names (179 KB) |
| [`src/data.py`](src/data.py) | Benchmark script: generates 22,284 queries with 0–3 errors and computes metrics (10.5 KB) |
| [`src/results.json`](src/results.json) | Output data consumed by `deck.py`: all metrics, counts, and segment tables (6.5 KB) |
| [`src/SCRIPT.md`](src/SCRIPT.md) | Structured presentation script: 17 slides with facts F1–F20 (8.1 KB) |
| [`src/deck.py`](src/deck.py) | Python presentation definition using `cutroom_deck` (20.9 KB) |

## Benchmark data and findings

Every metric in the presentation is computed by [`src/data.py`](src/data.py) from the official IBGE list and stored in [`src/results.json`](src/results.json). No numbers are hardcoded in the presentation layout.

- **Base data:** 5,571 municipalities across Brazil with 5,298 distinct names. 42.8% contain diacritics/accents, 47.8% are compound names (multiple words), and 9.1% share their name across different states.
- **Evaluation queries:** 22,284 synthetic queries generated with 0, 1, 2, and 3 errors across 5 error kinds (accent, deletion, insertion, substitution, transposition) using fixed seed 2026.
- **Ranking comparison (1 to 3 errors):**
  - **Exact match:** ranks the correct name first in 0.43% of queries with typos (`0.00432`).
  - **Raw Levenshtein:** ranks the correct name first in 85.5% of queries (`0.85537`) and in the top 5 suggestions in 94.9% (`0.94947`).
  - **Accents stripped (folded):** ranks the correct name first in 85.0% of queries (`0.85039`). While folding resolves 100% of accent errors, it increases ambiguities on other error types, lowering overall first-place accuracy by 0.5 percentage points.
- **Degradation by error count:** first-place ranking drops from 95.4% with 1 error to 86.4% with 2 errors, and 74.8% with 3 errors.
- **Error types:** letter transpositions (swaps) cause the most misses: in 1-error queries, a swap pushes the target municipality out of first place in 12.7% of cases, 2.5× more often than a letter deletion.
- **Length concentration:** short names (up to 6 letters) represent 13.9% of queries but account for 40.1% of all ranking misses. With 3 errors, short names place first in only 35.1% of queries.

## Commands

```bash
. ~/.local/share/cutroom/env.sh

# 1. Run benchmark calculation (writes src/results.json)
python3 src/data.py

# 2. Check SCRIPT.md facts against results.json
cutroom script check src/SCRIPT.md

# 3. Build HTML and PDF deliverables in active brand (cutroom)
deck build .

# 4. Check presentation layout in headless Chrome
deck check out/fuzzy-search-municipalities.html

# 5. Generate slide preview contact sheet
deck preview out/fuzzy-search-municipalities.html

# 6. Render in alternative brand (paper)
deck build . --brand paper -o out/fuzzy-search-municipalities-paper.pdf
deck preview out/fuzzy-search-municipalities-paper.html
```

## What to verify

- `deck check out/fuzzy-search-municipalities.html` exits with code 0: validates that no slide exhibits content overflows, broken layouts, or unrendered assets in Chrome.
- All 17 slides render in standard 16:9 widescreen format (1920×1080 viewBox).
- Numbers on slides strictly match `src/results.json`: `deck.py` imports `results.json` directly and formats numbers using `cutroom_deck.fmt` (`pct`, `num`, `dec`).
- Contact sheet grids (`out/*-grid.png`) display all 17 slides in sequential order without missing cards or visual cutoffs.

## How to open

```bash
# macOS
open out/fuzzy-search-municipalities.pdf
open out/fuzzy-search-municipalities.html

# Linux
xdg-open out/fuzzy-search-municipalities.pdf
```

## Brand applied

- **Primary brand:** `cutroom` (Hot Signal `#FF2D6F`, Night Plum `#16072B`, Sunflower `#FFC43D`, Blush Paper `#FFF7FA`).
- **Typography:** Bricolage Grotesque (display headings and large statistics), Inter (body and annotations), JetBrains Mono NL (data tables and code references).
- **Visuals:** charts and cards built using `cutroom_deck.ui` and `cutroom_deck.ill` components (`ui.summary`, `ill.small_multiples`, `ill.paired_bars`, `ill.heatmap`, `ui.strengths_limits`, `ui.proposals`).
- **Secondary brand:** `paper` (terracotta primary, warm paper surface, serif display font) generated via `--brand paper` to confirm brand portability.

## Limits

- Raw Levenshtein counts a transposition of neighboring letters as 2 edit operations (one deletion plus one insertion). A Damerau-Levenshtein implementation would count this as 1 edit.
- The 85.5% top-1 rate is insufficient for automated query correction without human confirmation; however, top-5 suggestions capture 94.9% of queries with up to 3 typos.
- 9.1% of municipal names are duplicated across states (e.g., Bom Jesus, São Domingos). Resolving duplicate names requires state context or geographic location.
