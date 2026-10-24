---
name: cutroom-diagram
description: "Builds interactive, validated diagrams as self-contained HTML with Archify: architecture, workflow, sequence, data flow, lifecycle/state, ERD, class, tree, timeline and waterfall, with light/dark themes, search, route tracing, presentation mode and PNG/SVG/WebM export. Also draws from a repository's code (with per-file evidence) or from Mermaid, framed in the active brand for previews. Use when asked to draw, diagram or visualize a system, flow, pipeline, API, schema, process or history, or when a report, deck or artifact needs a real diagram. Not for dashboards. Usage: cutroom-diagram <what to draw> [repo=<path>]"
metadata:
  version: "2.0.0"
---

# cutroom-diagram: interactive diagrams (Archify 3.2)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom`. `A` = `~/.local/share/cutroom/upstream/archify/archify` (official
skill and CLI, at the pinned tag).

## Step 0: component

Run `cutroom doctor --json` and check `components.diagram.installed`. If false, say `diagram` downloads ~40 MB, offer
`cutroom-init diagram` and stop until it is installed.

## Step 1: folder and rules

1. Run `cutroom job "<title>"` and keep the path as `$J`. Archify resolves paths from the current directory, so run
   everything with `cd "$J/src" && ...`.
2. Read `A/SKILL.md` whole: it is the authoring rule (type router, `candidate.json` format, `finalize`, repair,
   delivery). Read the references it points to for the chosen type (`A/references/...`). For a code diagram, also
   `A/references/repository-authoring.md`.
3. In every official command, replace `node bin/archify.mjs` with `archify`:

```bash
. ~/.local/share/cutroom/env.sh && cd "$J/src" && archify finalize architecture candidate.json ../out/<slug>.html --quality showcase --json
```

What changes from the official skill:

- **Folder:** the candidate lives in `$J/src` and the final HTML in `$J/out/<slug>.html`, instead of
  `.archify/<type>-<slug>-<date>/`. In the candidate, `meta.output` is just `"<slug>.html"` (the schema refuses `..`
  and absolute paths; the real destination is the `../out/<slug>.html` argument). To keep receipts out of `out/`,
  pass `--out-dir "$J/work/archify-1"` from the first round and use `archify-<n>` for each new round (after
  `browser-check`, the official skill requires a new folder). Only `.delivery.json` stays next to the HTML: delete
  it from `out/` on delivery if you want the folder clean.
- **Repair:** follow the official skill exactly, including the attempt limit per problem and the single position round
  when the receipt has `visualReviewRecommendation.signals.resolvedCrossovers`.
- **Language:** labels, texts and `meta` in the piece's language. Archify ships an English interface; for Portuguese,
  put the content of `A/examples/locales/pt.json` in `meta.translations`; for other languages, say the viewer menus
  stay in English.
- **Visible facts:** node tags only show at high zoom or in focus. Versions, sizes and numbers that matter go in
  `label`, `sublabel` or the cards.
- **Brand:** the candidate has no free color field (only `visual_preset` and the cards' `dot`, an enum). Use the
  light theme (`?theme=light` in the URL), the `dot` closest to the brand's primary, and for previews a frame in the
  brand: a page with the title in the display font and primary color, the brand logo (`cutroom brand show --json` →
  `paths.logos.on_light`), and the diagram in an `<iframe>`. `examples/diagram-architecture/src/frame.html` is a
  starting point. Load fonts through the brand's `fonts.css` (copy it with its `fonts/` folder into `$J/src/brand/`)
  so the frame renders offline.
- **Code:** use `--repo-root <repo>` and real per-file evidence. No invented nodes.

## Step 2: verify

- `finalize` with a non-zero exit is never success.
- To see the result, use the official optional capture (`--out-dir "$J/work/visual-check"`) or the PNG below, and
  **open the PNGs** before claiming visual quality. Without looking, say the check was only automatic.

## Step 3: deliver

- Deliver `$J/out/<slug>.html` (opens directly in a browser, no server) and `candidate.json` in `$J/src`.
- The HTML is self-contained; agents that publish pages can turn it into an artifact. For a report, export PNG/SVG
  from the viewer or embed the HTML in a section.
- Static PNG, light theme, tall enough for the whole diagram (adjust to the type):
  `cutroom render "$J/out/<slug>.html?theme=light" -o "$J/out/<slug>.png" --size 1600x2000 --wait 3`
- GIF or mp4 showing focus and routes (for a README, slide or email):

  ```bash
  . ~/.local/share/cutroom/env.sh && record-html "$J/out/<slug>.html?theme=light" "$J/out/<slug>.gif" \
    --seconds 7 --size 1400x900 --hover-sel '[data-node-id="<id1>"];[data-node-id="<id2>"];[data-node-id="<id3>"]' \
    --fps 10 --width 860
  ```

  The ids are the nodes' `id` in the candidate. Hover only, without the "Live" mode, and `--width` up to ~860 keep the
  GIF under 4 MB. Use the brand frame's URL instead of the raw HTML when the piece leaves the team.
