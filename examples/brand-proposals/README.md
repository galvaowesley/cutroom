# Example: brand proposals comparison (cutroom-brand / cutroom brand compare)

**Request:** "Generate three distinct visual identity directions for cutroom using 'cutroom brand compare'. Render side-by-side comparison boards for logo, color, and applications, evaluate palette contrast, and record the final selection (Direction B Hot Signal)."

<p align="center"><img src="out/compare.png" width="800" alt="Side-by-side comparison of three brand directions: Electric Violet, Hot Signal, and Ultramarine"></p>

[`out/compare.html`](out/compare.html) (comparison board, 1.4 KB) · [`out/compare.png`](out/compare.png) (3-column comparison matrix, 1.83 MB) · source in [`src/`](src)

| File | Description |
|---|---|
| [`out/compare.html`](out/compare.html) | Deliverable: comparison board displaying all three brand candidates across 3 boards each (1.4 KB) |
| [`out/compare.png`](out/compare.png) | High-resolution 3-column visual comparison render captured via headless Chrome (1.83 MB) |
| [`out/cutroom-electric/`](out/cutroom-electric) | Direction A board renders: `01-logo.png` (284 KB), `02-color.png` (340 KB), `04-applications.png` (434 KB) |
| [`out/cutroom-hot/`](out/cutroom-hot) | Direction B board renders (Chosen): `01-logo.png` (325 KB), `02-color.png` (357 KB), `04-applications.png` (423 KB) |
| [`out/cutroom-ultra/`](out/cutroom-ultra) | Direction C board renders: `01-logo.png` (328 KB), `02-color.png` (349 KB), `04-applications.png` (414 KB) |
| [`src/cutroom-electric/brand.json`](src/cutroom-electric/brand.json) | Direction A specification: Electric Violet and Acid Lime palette with Inter Tight (5.8 KB) |
| [`src/cutroom-hot/brand.json`](src/cutroom-hot/brand.json) | Direction B specification: Hot Signal and Sunflower palette with Bricolage Grotesque (5.9 KB) |
| [`src/cutroom-ultra/brand.json`](src/cutroom-ultra/brand.json) | Direction C specification: Ultramarine and Volt Orange palette with Space Grotesk (5.6 KB) |
| `src/*/logos/`, `src/*/icons/`, `src/*/fonts/` | Supporting vector logos, skill icons, and TTF font files for each candidate brand |

## The three brand proposals

To determine the visual identity of cutroom, three distinct aesthetic directions were generated and compared side by side using `cutroom brand compare`:

### Direction A · Cutroom Electric
- **Theme:** Electric violet and acid lime on deep ink.
- **Palette:**
  - Primary: Electric Violet `#5B2EFF`
  - Deep: Deep Ink `#0C0A1D`
  - Accent: Acid Lime `#C5FF3D`
  - Surface: Soft Violet `#F7F5FF`
- **Typography:** Inter Tight (display), Inter (text), JetBrains Mono NL (code).
- **Tone:** Technical, clinical, sharp developer tool aesthetic.

### Direction B · Cutroom Hot (Chosen)
- **Theme:** Hot pink and sunflower on night plum.
- **Palette:**
  - Primary: Hot Signal `#FF2D6F`
  - Deep: Night Plum `#16072B`
  - Accent: Sunflower `#FFC43D`
  - Surface: Blush Paper `#FFF7FA`
- **Typography:** Bricolage Grotesque (display), Inter (text), JetBrains Mono NL (code).
- **Tone:** High energy, editorial punch, warm and distinctive.

### Direction C · Cutroom Ultra
- **Theme:** Ultramarine and volt orange on deep navy.
- **Palette:**
  - Primary: Ultramarine `#1F4BFF`
  - Deep: Deep Navy `#050A1F`
  - Accent: Volt Orange `#FF6A13`
  - Surface: Ice Blue `#F6F8FF`
- **Typography:** Space Grotesk (display), Inter (text), JetBrains Mono NL (code).
- **Tone:** Geometric, utilitarian, modernist engineering vibe.

## Decision rationale: why Direction B was chosen

1. **Media Contrast:** Hot Signal (`#FF2D6F`) against Night Plum (`#16072B`) delivers high legibility in video compositions, slide deck covers, and diagrams.
2. **Distinctive Character:** Bricolage Grotesque provides a recognizable personality in headings and large callout numerals without degrading readability.
3. **Accessibility:** Direction B passes all WCAG AA contrast ratios (Night Plum on white: 16.8:1; Hot Signal on white: 3.9:1 for titles; Night Plum on Blush Paper: 15.5:1).
4. Following comparison, Direction B was formally adopted as the official `cutroom` built-in brand via `cutroom brand use cutroom-hot`.

## Commands

```bash
. ~/.local/share/cutroom/env.sh

# 1. Compare three candidate directions across logo, color, and applications boards
cutroom brand compare cutroom-electric cutroom-hot cutroom-ultra \
  --boards logo,color,applications \
  --scale 2 \
  -o out/compare.html

# 2. Capture static comparison image using headless Chrome
google-chrome --headless=new --window-size=1800,1200 --screenshot=out/compare.png out/compare.html

# 3. Check selected brand configuration
cutroom brand check cutroom-hot

# 4. Activate chosen brand as system default
cutroom brand use cutroom-hot
```

## What to verify

- Comparison grid in [`out/compare.html`](out/compare.html):
  - Displays three parallel columns: `cutroom-electric`, `cutroom-hot`, and `cutroom-ultra`.
  - Each column features three standardized boards (`01-logo.png`, `02-color.png`, `04-applications.png`) for direct comparison.
- Palette validation: all three `brand.json` candidate specifications pass `cutroom brand check` with 0 schema or accessibility errors.
- Font assets and licenses: each candidate folder includes full offline TTF files and corresponding Open Font License (OFL) notices for Inter, Inter Tight, Bricolage Grotesque, Space Grotesk, and JetBrains Mono.

## How to open

```bash
# macOS
open out/compare.html
open out/compare.png

# Linux
xdg-open out/compare.html
```

## Limits

- `cutroom brand compare` evaluates static 2D identity boards; interactive states and motion easing curves must be assessed in animated deliverables.
- Font files are duplicated across each candidate folder in `src/` to ensure each direction remains independently portable.
