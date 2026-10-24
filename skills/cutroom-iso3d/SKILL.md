---
name: cutroom-iso3d
description: "Creates animated, interactive isometric figures that explain a technical concept as a physical object. Anatomy makes detailed machines with solid parts, four-tone shading, dials and live readouts, with optional WebGL. Hairline makes Linear-style single-line figures that answer the pointer. Delivers SVG or self-contained HTML, PNG and, with record-html, GIF or mp4, framed in the active brand. Use when asked for an isometric illustration, a premium explanatory figure for a landing page, article, documentation, report or artifact, an interactive explainer of how a system, algorithm or process works, or an animated icon. Usage: cutroom-iso3d <concept> [style=anatomy|hairline] [format=html|svg|gif]"
metadata:
  version: "2.0.0"
---

# cutroom-iso3d: isometric figures (Anatomy 1.1, Hairline 0.5.1)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom`. Official skills: `AN` = `~/.local/share/cutroom/upstream/anatomy`
and `HL` = `~/.local/share/cutroom/upstream/hairline/skills`.

## Step 0: component

Run `cutroom doctor --json` and check `components.iso3d.installed`. If false, say `iso3d` downloads ~30 MB, offer
`cutroom-init iso3d` and stop until it is installed.

## Step 1: which of the two

| | Anatomy | Hairline |
|---|---|---|
| Look | solid, dense machine with dials, springs, cables | single-line object, minimal |
| Idea | the whole mechanism working | one gesture, one reading |
| Agent time | Figure: 30 to 90 min. Hero: 2 to 4 h | 10 to 30 min |
| Output | HTML, standalone SVG, React, A4 PDF | one dependency-free HTML |
| Good for | report, article or product-page explainer | empty state, live icon, section header |

With no preference, use Hairline for something quick or decorative and Anatomy to explain a mechanism. Before
starting, give the size and estimated time, as both official skills ask.

## Step 2: produce

1. Run `cutroom job "<title>"` and keep the path as `$J`. Sources you write (`build.mjs`, `<name>.js`) live in
   `$J/src`. Run scripts from `$J/work`, because they write the page and PNGs to the current directory; then copy
   only deliverables to `$J/out/`.
2. **Anatomy:** read `AN/SKILL.md` and follow its workflow: size, real numbers, object, parts list, world, geometry
   with the kit, painting, card, motion and verification. Start from the closest example
   (`AN/examples/dial-indicator/` is the smallest). `$J/src/build.mjs` imports the kit through `ANATOMY_HOME`, which
   `env.sh` sets, so the build runs on any machine:

   ```js
   import { join } from "node:path";
   import { pathToFileURL } from "node:url";
   const AN = process.env.ANATOMY_HOME;  // ~/.local/share/cutroom/upstream/anatomy
   const kit = await import(pathToFileURL(join(AN, "kit/iso-kit.mjs")).href);  // same for audit.mjs, scripts/inline-kit.mjs
   ```

   - **Brand in Anatomy:** use the light theme (`--light`) on a white page. The accent goes in `--anatomy-lit`, the
     readout and the title: the brand's `primary`, and `accent` for the part in focus. Do not touch `paper` or the
     `shade-*` values, which make the four-tone shading. On the dark theme, use `accent_soft` instead of a primary
     that lacks contrast on the dark card (check with `cutroom brand check`).
   - **Language:** the kit's `pageHtml` writes `<html lang="en">`; change it if the piece is in another language.
   - **Fonts in one file:** for a self-contained page, embed the brand fonts in base64 (subset woff2 when possible),
     as `examples/iso3d-drawers/src/build.mjs` in the repository does.
3. **Hairline:** read `HL/hairline-create/SKILL.md` (or `HL/hairline-adopt/SKILL.md` to recreate an SVG). Offer 2 or
   3 concepts and wait for the choice. With nobody to choose (e.g. a crew task), follow the official rule: keep the
   concept with the best rest pose and say which. Write `$J/src/<name>.js` and build with
   `cd "$J/work" && node "<HL>/hairline-create/build.mjs" ../src/<name>.js`. Never edit `kernel.js` or `bench.html`.
   The tour stops ~2 s at each point: a response chained in three 700 ms tweens does not make it, so start the next
   move before the previous one ends.
4. Run everything as `. ~/.local/share/cutroom/env.sh && cd "$J/work" && node ...`. `env.sh` points at Chrome
   (`CHROME_PATH`) and the playwright-core cache Hairline's `look.mjs` uses (`HAIRLINE_LOOK_CACHE`).
5. Texts, labels, `means` and readouts in the piece's language, with one exception: Hairline's rest readout must be
   literally `rest`, or `look.mjs` fails. Numbers shown come from the figure's model and the person's real data,
   never from the examples.

Do not, even if the official skill offers it:

- `AN/scripts/publish.mjs` (public community gallery): only on explicit request.
- `npx skills add ...`: the skills are already at the pinned tag.

## Step 3: verify

- **Anatomy:** if the build uses `kit/audit.mjs` (required with tubes, cables or turned parts; recommended with moving
  parts), `node build.mjs --audit` must end in `audit passed`. A build without `recorder` and `auditOrExit` runs
  `--audit` silently, which proves nothing. The full audit can take minutes: iterate without `--audit`, run it at
  the end. `node "<AN>/scripts/lines.mjs" page.html --reduced --out shots/lines.png` must print `line ends: 0`
  (`--reduced` measures at rest; for open poses use `drive.mjs` with the `["lines"]` action). Capture with
  `AN/scripts/capture.mjs` and **read every PNG**.
- **Hairline:** `node "<HL>/hairline-create/look.mjs" ../src/<name>.js --answer=x,y,z --edge=x,y,z` until it exits 0.
  Use `=`: a negative coordinate after a space (`--answer -61,...`) breaks the parser. Then **read** the
  `hairline-<name>-look.png` sheet and answer the questions in `look.md`.

## Step 4: GIF, video and delivery

Both make interactive pages and do not export video. For GIF or mp4, record the page (the path may carry a query):

```bash
. ~/.local/share/cutroom/env.sh && record-html "$J/out/hairline-<name>.html?play=1&theme=light" "$J/out/<slug>.gif" \
  --wait 1.2 --seconds 8 --size 760x760 --fps 12 --width 720
```

- **Hairline:** `?play=1` runs the tour, about 2 s per stop (8 s cover a 3-stop loop plus the exit). A window close
  to the GIF width avoids a small figure.
- **Anatomy:** walk the pointer over the parts that react, by selector (`--hover-sel "css;css"`, also inside iframes)
  or coordinates (`--hover "x,y;x,y"`). `--click-sel "css;css"` (or `--click x,y`) clicks before recording, e.g. to
  leave drawers open.
- Record at the size of the frame or figure (`--size`), not a big window with empty space. For GIFs keep `--width`
  near 800. Sharp 2x PNG: `cutroom render <frame>.html -o "$J/out/<slug>.png" --size WxH --scale 2`.
- **Preview PNG:** the bare figure comes from `look.mjs --zoom rest` (Hairline) or `capture.mjs` (Anatomy). With the
  frame, take a frame of the recorded mp4: `cutroom edit frames prev.mp4 -o "$J/work/frames" --at 1`.
- **Brand frame:** record a simple page rather than the raw page: title in the brand's display font and primary,
  supporting line in the text font and `text_muted`, the figure in an `<iframe>` with the brand radius, and the
  `on_light` logo. `examples/iso3d-router/src/frame.html` and `examples/iso3d-drawers/src/frame.html` are starting
  points.

Deliver the HTML (or SVG) in `$J/out/`, the PNG or GIF preview and the sources in `$J/src/`. Self-contained HTML can be
published as an artifact directly.
