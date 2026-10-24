# Paper design system

> A sample editorial brand: the look of a well-set report or essay. `brand.json` holds the values; this file says
> how to use them.

## Principles

1. **Reads like print.** Warm paper background, generous margins, serif display. Pages should look typeset,
   not designed.
2. **Terracotta is ink, not paint.** Primary marks numbers, rules and the main series. It fills a surface only on
   covers.
3. **Slow and steady.** Motion is unhurried (600 ms) and only moves what the narration is about.

## Color

| Token | Value | Use |
|---|---|---|
| `primary` | `#A8432A` | big numbers, eyebrows, the main series, covers |
| `deep` | `#2A2420` | verdicts, code, dark video backgrounds |
| `accent` | `#2F6F62` | the highlight on paper backgrounds; second series when two must be compared |
| `accent_soft` | `#8CC7B8` | the highlight on `deep` |
| `tint` | `#F6ECE4` | "how to read" boxes and pull quotes |
| `background` / `surface` | `#FBF8F1` / `#F4EFE5` | paper and cards |
| `scale` | `#F6ECE4` → `#A8432A` | ordinal data |

## Type

- **Fraunces** for titles (600) and display numbers (300). Sentence case, never all caps except eyebrows.
- **Instrument Sans** for body copy (400; 600 for emphasis), 17 to 19 px, line height 1.55.
- **JetBrains Mono NL** for code.
- Eyebrows: Fraunces 600, 12 px, uppercase, letter-spacing 0.1 em, in primary.

## Shape and motion

- Radius 6 px: corners are nearly square, like cut paper. Thin rules (1 px `border`) separate sections.
- Ease `cubic-bezier(.25,.7,.25,1)`, 500 to 700 ms. Fades and short slides only.

## Logo

- Wordmark: "paper" in Fraunces 600 with a terracotta full stop. Symbol: the "p." monogram in a circle.
- `wordmark-light.svg` / `symbol-light.svg` on primary or deep; the others on paper.
- Clear space of one full stop's width times four. Never recolor or add effects.

## Do / don't

| Do | Don't |
|---|---|
| serif titles in sentence case | serif body copy at small sizes |
| terracotta for the key number | terracotta blocks behind body text |
| thin rules and whitespace | drop shadows, glows, gradients |
