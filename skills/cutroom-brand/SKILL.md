---
name: cutroom-brand
description: "Builds a brand and design system from whatever the person gives: logos, screenshots, photos, a website, PDFs or brand books, font files or font names, statements about who they are and how they speak. Extracts the palette from images, fetches open fonts, derives a complete accessible color system (checked against WCAG), writes brand.json, DESIGN.md (rules) and VOICE.md (tone), and renders the brand book as four boards (logo, color and type, icons, applications) in HTML, PNG and/or PDF at the resolution asked. Also imports existing brand folders, switches the active brand and lists brands. Every cutroom skill then produces in that brand. Use when someone wants a brand, visual identity, design system, style guide, brand book, palette, type pairing or brand voice, wants their pieces in their company's or client's brand, or says the current brand does not fit. Usage: cutroom-brand <name> [from: files, links, statements] | use <name> | list | book <name>"
metadata:
  version: "1.0.0"
---

# cutroom-brand: a brand and design system from your material

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`). Everything here uses
`cutroom brand ...` (Python standard library + Chrome). `cutroom brand schema` prints the `brand.json` reference.

A brand is a folder: `brand.json` (values), `DESIGN.md` (how to use them), `VOICE.md` (how it speaks), `fonts/`,
`logos/`, `icons/`. User brands live in `~/.local/share/cutroom/brands/`. Built-in: `cutroom` (default) and `paper`.

## Step 1: mode

| Request | Do |
|---|---|
| `list`, "which brands" | `cutroom brand list`; stop |
| `use <name>`, "make X the default" | `cutroom brand use <name>` (checks it and registers its fonts); stop |
| an existing brand folder (a `brand.json` inside) | `cutroom brand add <folder>`, then Step 6 |
| `book <name>`, "brand book", "style guide" of an existing brand | Step 6 |
| a new brand or a brand from material | Steps 2 to 6 |

## Step 2: collect the material

Take everything the person gave and ask, in one message, only for what is missing:

- **Name** (exact spelling and case), **what they do**, **audience**, **3 to 5 adjectives** and their opposites
  ("precise, never cold"), **competitors or references** to look like or to avoid.
- **Visual material:** logo files (SVG best), screenshots of their product or site, photos, an old brand book, a
  website URL. Copy them into `$J/src/inputs/` (`cutroom job "brand <name>"`).
- **Type:** font files they own, or names of fonts they use (Google Fonts are fetched; commercial fonts must come as
  files with their license).
- **Words:** how they talk to customers (a page of their site, an email, a post). This feeds `VOICE.md`.
- **Constraints:** colors they must keep, accessibility level, where it must work (slides, video, print, app).
- **Outputs:** which boards and formats they want (default: all four boards, HTML + PNG + PDF at 2x).

Reading material:

- Images and screenshots: open them yourself, and run `cutroom brand palette <images...> --json` for the dominant
  colors with their share, a role hint (background, text, neutral, brand candidate) and contrast on white.
- PDFs, decks, docs (an old brand book): `cutroom-extract` if installed, else read directly. Note the stated colors
  (HEX, RGB, CMYK, Pantone), fonts, logo rules and tone.
- A website: fetch the page (your web tool), read its CSS custom properties, fonts and copy; or ask for screenshots.
- A logo: keep the original. If they have none, or it is a raster at 200 px, offer `cutroom-logo` to design or
  redraw it (it needs the `logo` component, ~13 MB).

## Step 3: decide the system

Write a short brief back (name, audience, adjectives, what to keep, what to avoid) and decide, in this order:

1. **Primary:** the color that is unmistakably theirs (from the logo or the palette). It must hold white text at
   4.5:1 to work as a cover background; if it does not, darken it slightly and say so, or keep it and make covers
   `deep` with primary marks.
2. **Deep, accent, tint, scale, neutrals, semantic:** start from `cutroom brand new <name> --primary <hex>
   [--accent <hex>]`, which derives a complete, contrast-checked set, then replace each derived value with one from
   their material when there is one. One accent only: the "look here" color.
3. **Type:** display (titles, big numbers) and text (body), plus a mono for code. Use theirs. If they have none,
   pair by the adjectives: precise/technical → grotesque or neo-grotesque (Inter Tight, Manrope, Geist); warm or
   editorial → a serif display (Fraunces, Newsreader) with a humanist sans; playful → rounded (Nunito, Quicksand).
   Two families at most. Fetch: `cutroom brand font <name> "<Family>" --weights 300,600,800 --role display`
   (and `--role text`, `--role mono`).
4. **Shape and motion:** corner radius (technical 8–16 px, friendly 16–24, editorial 2–6), easing and duration.
5. **Logo slots:** `cutroom brand logo <name> on_light=logo.svg on_primary=logo-white.svg symbol_on_light=... `
   (also `symbol_on_primary`, `stacked`, `app_icon`, `mono`). White versions for dark backgrounds are required:
   make them (SVG: change the fills) if the person only has one.
6. **Icons (optional, for the book):** 12 icons for what they do, drawn on a 24 × 24 grid in the brand's stroke and
   accent (`cutroom brand icon <name> icons/*.svg --label ...`). Without icons, the book draws a default line set in
   the brand colors.
7. **Book metadata:** in `brand.json`: `tagline`, `palette` (each color's name, use and share of the surface),
   `book.headlines` (one sentence per board, in their voice), `book.version`, `book.date`, `contact`
   (placeholders for the applications). `language` sets the book labels (English and Portuguese built in).

## Step 3b: propose directions, then stop for approval

When the material leaves room for choice (no fixed palette, a new brand, or the person says the current one does
not fit), do not pick alone. Build two or three directions that differ in palette and display font, keep what is
fixed (the logo shape, colors they must keep), and show them side by side:

```bash
cutroom brand new acme-a --primary "#5B2EFF" --accent "#C5FF3D" --display "Inter Tight"
cutroom brand new acme-b --primary "#FF2D6F" --accent "#FFC43D" --display "Bricolage Grotesque"
cutroom brand new acme-c --primary "#1F4BFF" --accent "#FF6A13" --display "Space Grotesk"
# per direction: fonts (`cutroom brand font`), logo versions in its colors (`cutroom brand logo`), check
cutroom brand compare acme-a acme-b acme-c -o "$J/out/proposals" --title "acme · brand proposals" \
  --notes "electric violet + acid lime" "hot pink + sunflower" "ultramarine + volt orange"
```

- Each direction says its idea in one line (the `--notes`), and states its trade-off (e.g. "dark text on a bright
  primary"). Bright primaries that need dark text on them set `on_primary` dark and `on_deep` light.
- Open `compare.png` (or `compare.html`) yourself, then show it and ask which to keep, with "mix" as an option
  (one direction's colors with another's font). Wait for the answer before writing DESIGN.md.
- Keep the chosen direction under the final name (`cutroom brand add <folder> --name acme`) and remove the others,
  or keep them as a record. `examples/brand-proposals` in the repository is cutroom's own proposal round.

## Step 4: write DESIGN.md and VOICE.md

Replace the TODOs that `brand new` left. Concrete and short, like `harness/brands/cutroom/DESIGN.md`:

- **DESIGN.md:** three principles that decide close calls; a color table (token, value, use); type roles and sizes;
  shape and motion; logo rules (slots, clear space, minimum size, never-do list); a do/don't table. Write the rules
  the material implies, not generic advice. Cite the source when a rule comes from their old brand book.
- **VOICE.md:** how they address the audience, three "X, but never Y" pairs, how numbers appear, words to avoid,
  how the name is written, default language. Quote a sentence from their material when it shows the voice.

## Step 5: check

```bash
. ~/.local/share/cutroom/env.sh && cutroom brand check <name>
```

It validates the schema and files and the WCAG contrast of every pair the skills use (text on background, text on
primary, semantic pairs, accent on deep). Errors block `brand use`. Fix by adjusting the derived colors, never by
changing the person's logo color without telling them. Repeat until clean, then `cutroom brand preview <name>` for a
one-page specimen and **look at it**.

## Step 6: brand book

```bash
cutroom brand book <name> -o "$J/out/book" --format html,png,pdf --scale 2
```

- Boards: `01 logo` (lockups on light and dark, stacked, symbol, app icon, one color, clear space, minimum sizes),
  `02 color` (named palette with HEX, RGB and use, usage proportion, type specimens, hierarchy), `03 icons`,
  `04 applications` (business card, avatar, social banner, email signature, presentation cover, document, website).
- `--format` takes any of `html`, `png`, `pdf` (comma-separated); `--scale` sets the PNG resolution (1 = 1440 ×
  1120, 2 = 2880 × 2240); `--boards logo,color` renders only some.
- HTML is self-contained (fonts and logos embedded) and can be published as an artifact.
- **Open every PNG** and check: logos sharp and not distorted, no text overflowing cards, palette names and uses
  correct, headlines in the brand's voice. Fix `brand.json` or the logo files and render again.

## Step 7: deliver and activate

- Deliver `$J/out/book/*` and the brand folder path (`cutroom brand show <name>`).
- Ask whether to make it the default: `cutroom brand use <name>`. Otherwise, each request can name it ("in the acme
  brand"), and skills read `cutroom brand show acme --json`.
- To share the brand with a team: zip the brand folder; others run `cutroom brand add <folder>`.
- Say what came from their material and what you derived or chose, so they can correct it.
