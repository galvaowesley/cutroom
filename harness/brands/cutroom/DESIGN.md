# cutroom design system · Hot Signal

> The default brand of cutroom. `brand.json` holds the values; this file says how to use them.
> Read it before composing any page, slide, figure or video in this brand.

## Principles

1. **Loud color, quiet layout.** Hot pink and night plum carry the energy; the composition stays simple: one
   message, generous space, big type. If a frame feels busy, remove elements, never color.
2. **One cue per frame.** Sunflower marks the single thing to look at right now (the playhead, the answer, the active
   step). Two sunflower elements on screen means one of them is wrong.
3. **The number is the headline.** Titles state the finding with its number; big numbers use Bricolage Grotesque 300
   in hot pink, everything around them is quiet.

## Color

| Token | Value | Name | Use |
|---|---|---|---|
| `primary` | `#FF2D6F` | Hot Signal | the brand: covers, marks, big numbers, the main data series, buttons |
| `on_primary` | `#16072B` | Night Plum | text and logo **on hot pink are dark**, never white (white on #FF2D6F fails contrast) |
| `deep` | `#16072B` | Night Plum | code panels, verdicts, dark video backgrounds |
| `on_deep` | `#FFFFFF` | White | text on night plum; logo on deep keeps the pink c with a white word (`wordmark-deep.svg`) |
| `accent` | `#FFC43D` | Sunflower | the one cue: playhead, active element, the answer. Never body text, never on white for text |
| `accent_soft` | `#FF9BC0` | Pink Soft | labels and secondary highlights on night plum |
| `tint` | `#FFE9F0` | Blush | "how to read" boxes, highlight cards |
| `background` / `surface` | `#FFFFFF` / `#FFF7FA` | White / Blush Paper | pages and cards |
| `text` / `text_muted` | `#16072B` / `#55466B` | Night Plum / Mauve Grey | body copy and secondary copy |
| `scale` | `#FFE9F0` → `#FF2D6F` | | ordinal data: levels, groups, heatmaps |
| `success`, `warning`, `danger` | on their `_bg` | | state only (pass/fail, use/don't use). Never a data series |

- Light pieces: white or blush paper, hot pink marks and numbers, night plum text.
- Dark pieces (video, code): night plum background, white text, pink soft labels, sunflower cue.
- Covers and banners: hot pink background with night plum type and logo; a sunflower dot or bar as the cue. No
  glow: the color is loud enough on its own.
- Usage proportion: about 38% night plum, 28% paper, 22% hot pink, 6% sunflower, 6% mauve grey.

## Type

- **Bricolage Grotesque** for titles (600 to 700), heavy statements (800) and display numbers (300). Its slightly
  quirky, ink-trapped shapes are the brand's young voice in type: use it big, tracking −0.02 em from 32 px up.
- **Inter** for body copy (400; 600 for emphasis), 16 to 18 px, line height 1.5.
- **JetBrains Mono NL** for code. The NL cut has no ligatures, so `->` and `==` render as typed.
- Eyebrows: Bricolage Grotesque 700, 12 to 13 px, uppercase, letter-spacing 0.1 em, in hot pink.

## Shape and motion

- Radius 16 px for cards and boxes, 20 px for covers and frames, pills for buttons and tags.
- Ease `cubic-bezier(.2,.8,.2,1)`, 300 to 500 ms: quick and confident. Fades, translates of 8 to 32 px and hard cuts.
  No spring, no bounce, no scale pops.
- In video, cut between scenes or wipe with a pink bar; never cross-fade logos.

## Logo

- **Symbol: the offset c.** The c of cutroom, cut through its middle with the lower half slid right, like two takes
  spliced on a timeline. Built as filled geometry (two ring halves, outer radius 92, inner 46 on a 256 grid).
- **Wordmark:** "cutroom" in Bricolage Grotesque 700, always lowercase, outlined to paths.
- Versions: `wordmark.svg` (pink c, plum word) on light; `wordmark-deep.svg` (pink c, white word) on night plum;
  `wordmark-light.svg` (all plum) on hot pink; `mono.svg` (all plum) for one-color print; `app-icon.svg` (plum c on a
  pink rounded square); `stacked.svg`.
- Clear space: one ring thickness (46/256 of the symbol) on every side. Minimum: symbol 16 px, horizontal logo 96 px
  wide.
- Never recolor the halves differently, close the splice, rotate, outline, add shadows or reduce opacity. The logo goes
  on covers, closing slides, end cards and app surfaces only.
- Tested with the logo-design skill: 16/32/48 px pixel test, one-color, reversed, squint, mirrored and rotated
  readings, shelf test against developer-tool marks.

## Do / don't

| Do | Don't |
|---|---|
| state the finding in the title, with the number | label a slide "Results" |
| plum type on hot pink | white type on hot pink |
| one sunflower cue per frame | sunflower text on white, two cues |
| night plum behind code and verdicts | gradients across the whole background |
| `scale` for ordered groups | semantic green/red for data series |
