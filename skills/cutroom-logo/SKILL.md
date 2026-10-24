---
name: cutroom-logo
description: "Designs logos from brief to production files with the logo-design skill (1,400+ reference logos, dependency-free scripts): discovery and brief, concepts across mark types (wordmark, monogram, letterform, pictorial, abstract, emblem), clean geometric SVG, 16 px, one-color, reversed and shelf tests, concept sheet, presentation board with industry mockups, export variants (favicon, app icon, web icons), then installs the logo into a cutroom brand. Also critiques and redesigns logos. Use when someone wants a logo, logotype, wordmark, monogram, symbol, app icon or favicon designed, redrawn as SVG, critiqued or compared, or when cutroom-brand needs a logo. Usage: cutroom-logo <name and what they do> [critique <file> | redesign <file>]"
metadata:
  version: "1.0.0"
---

# cutroom-logo: logo design (logo-design skill 1.4.5)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`).
`LD` = `~/.local/share/cutroom/upstream/logo/skills/logo-design` (official skill and scripts, pinned tag).

## Step 0: component

Run `cutroom doctor --json` and check `components.logo.installed`. If false, say the `logo` component downloads
~13 MB (skill, scripts and reference library) and offer `cutroom-init logo`. Stop until it is installed.

## Step 1: rules

1. Run `cutroom job "logo <name>"` and keep the path as `$J`. Concepts and tests go in `$J/work/logo/`, chosen files
   in `$J/out/logo/`.
2. Read `LD/SKILL.md` whole and follow its workflow (modes, phases, checkpoint, red flags). Read the references it
   points to as you reach each phase (`LD/references/...`).
3. Run its scripts with the full path: `python3 "LD/scripts/<script>.py" ...` (on Windows, `python` instead of
   `python3`). They are standard library only and render with the system Chrome.

What changes from the official skill:

- **Brief from the brand:** if a brand already exists (`cutroom brand show <name> --json`), its colors, fonts and
  `DESIGN.md` are constraints. Wordmarks use the brand's display font, outlined to paths (no live `<text>`).
- **Checkpoint:** the official checkpoint stands. Show the concept sheet (`concept_sheet.py`) and wait for a choice
  before building the kit. In a `cutroom crew` task, where nobody can answer, build the kit for the recommended
  concept and say so in the summary, with the other concepts available.
- **Kit into the brand:** after the kit (`export_variants.py`, presentation board), install the files into the brand:

  ```bash
  cutroom brand logo <brand> on_light="$J/out/logo/horizontal.svg" on_primary="$J/out/logo/horizontal-white.svg" \
    symbol_on_light="$J/out/logo/symbol.svg" symbol_on_primary="$J/out/logo/symbol-white.svg" \
    stacked="$J/out/logo/stacked.svg" app_icon="$J/out/logo/app-icon.svg"
  cutroom brand check <brand> && cutroom brand book <brand> --boards logo --format png --scale 2
  ```

  No brand yet: create one around the logo with `cutroom-brand` (`cutroom brand new <brand> --primary <hex>`).
  Built-in brands are read-only: make a copy with `cutroom brand new <name> --from cutroom`.
- **No outside services:** the library is local. Do not upload logos anywhere.
- **Trademarks:** the library is for learning, never tracing. Say that a logo must be cleared for trademark by the
  person before registration or wide use.

## Step 2: verify

- `svg_audit.py` on every final file: no live text, rasters, filters or near-miss angles.
- `preview_sheet.py` with `--refs-industry <closest>`: **open the sheet** (render it with Chrome to PNG if your
  agent cannot open HTML) and answer its questions: 16 px, squint, one color, reversed, mirrored, shelf test.
- On the brand book's logo board, check the lockups on light and dark.

## Step 3: deliver

- `$J/out/logo/`: masters (SVG), PNG sizes, favicon and web icons, the presentation board, the usage page.
- The brand updated (`cutroom brand show <brand>`), and its logo board.
- One sentence on the idea, the test results, and what is still open (trademark search, print proof).
