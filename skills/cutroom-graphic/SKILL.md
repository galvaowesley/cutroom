---
name: cutroom-graphic
description: "Makes static graphics in the active brand as HTML rendered to PNG, JPG, WebP or PDF at platform sizes: social posts and stories (Instagram, LinkedIn, X, Threads), YouTube thumbnails and banners, Open Graph and GitHub social previews, posters, infographics, quote cards, certificates, banners. Starts from brand-ready templates that adapt to the aspect ratio, renders several sizes at once at 1x or 2x, and embeds charts from cutroom-deck when the graphic shows data. Use when asked for a post, story, carousel slide, thumbnail, cover, OG image, poster, flyer, infographic, banner, certificate or any still image with text and layout. Usage: cutroom-graphic <what and where> [sizes=story,og] [format=png|jpg|pdf]"
metadata:
  version: "1.0.0"
---

# cutroom-graphic: still graphics in the brand

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`). Rendering is
`cutroom render` (Chrome); JPG and WebP also need ffmpeg.

## Step 0: component

Run `cutroom doctor --json` and check `components.graphic.installed` (Chrome only, nothing to download). If missing,
offer `cutroom-init graphic`.

## Step 1: brief

From the request, or by asking at once:

- **Where it goes**, which sets the sizes (`cutroom render presets`): `instagram-post` 1080², `instagram-portrait`
  1080 × 1350, `story` 1080 × 1920, `og` 1200 × 630, `x-post` 1600 × 900, `linkedin-post`, `linkedin-banner`,
  `youtube-thumb` 1280 × 720, `youtube-banner`, `github-social`, `a4`, `a3`, `letter`, `certificate`, or `WxH`.
- **The one message**, and the number if there is one (from the person or `SCRIPT.md`, with its source).
- **Brand** (active, or named) and **language**.
- **Format and resolution:** PNG (default, `--scale 2` for retina), JPG (photos), PDF (print), several sizes at once.

## Step 2: start from a template

```bash
cutroom job "<title>"            # → $J
cutroom render new <kind> "$J/src" [--brand <name>] [--name <file>]
```

| Kind | For | Adapts to |
|---|---|---|
| `social` | announcement, stat, launch: eyebrow, headline, big number, logo, source | wide, square and tall |
| `quote` | a quote card with name and role | any |
| `thumbnail` | video thumbnails: 3 words, one accent word, one visual | wide and tall |
| `poster` | A4/A3 poster or flyer, printable to PDF | portrait |
| `infographic` | tall page of findings with numbers and bars (`--full-page`) | width fixed, height grows |
| `certificate` | A4 landscape certificate, printable to PDF | landscape |

`render new` writes `<kind>.html` and copies the brand's `tokens.css`, `fonts.css`, `fonts/` and logos into
`$J/src/brand/`, so the folder renders offline and travels. Every color, font and radius comes from CSS custom
properties (`var(--primary)`, `var(--font-display)`...): never type hex values.

## Step 3: write it

- Replace the placeholder text. One message per graphic; the headline states it, with the number. Follow the brand's
  `VOICE.md`. Short: thumbnails ≤ 4 words, posts ≤ 12 words in the headline.
- The templates read `?w=&h=` and set `body[data-shape]` to `wide`, `square` or `tall`; adjust per shape in CSS
  (`body[data-shape="tall"] h1 { ... }`) instead of making one file per size.
- Sizes are in container units (`cqmin`, `cqw`): text scales with the canvas. Keep important content inside the
  platform's safe area (stories: away from the top 250 px and bottom 340 px at 1920).
- Data: build the chart with `cutroom_deck.ill` (`cutroom-python -c 'from cutroom_deck import ill; print(ill.grid(62))'`)
  and paste the SVG, or use the template's bars. Every number has a source line.
- Images: put them in `$J/src/` and reference them relatively; photos you did not take need the person's rights.
- More layouts (carousel slides, lower-thirds as stills, banners): copy a template and adapt it; keep the
  brand variables and the `ADAPT` script at the end.

## Step 4: render and check

```bash
cutroom render "$J/src/social.html" -o "$J/out/launch.png" --size instagram-portrait,story,og --scale 2
cutroom render "$J/src/poster.html" -o "$J/out/poster.pdf" --size a4
cutroom render "$J/src/infographic.html" -o "$J/out/findings.png" --size 1080x1920 --full-page
```

- Several sizes give `name-<size>.png`. `.jpg`/`.webp` convert through ffmpeg; `.pdf` prints with the page's `@page`.
- **Open every file.** Check: nothing cut or touching the edge, the headline readable at thumbnail size (look at
  the PNG at 25%), contrast of text on images, the logo on the right background (`on_primary` on dark,
  `on_light` on light), numbers matching their source.
- A carousel: one HTML per slide, same template, rendered with the same size; number the files.

## Step 5: deliver

- `$J/out/*` with sizes in the names, and `$J/src/` (HTML + brand folder) to edit later.
- Agents that publish pages can publish the HTML (self-contained once the brand folder is next to it).
