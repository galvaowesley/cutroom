---
name: cutroom-math
description: "Creates scripted math, algorithm and code videos in Python with ManimGX (the Manim Community API on a GPU engine in Rust): formulas (Typst/LaTeX), plots, geometry, 3D, code typed line by line and tables, with local narration in sync with the animations and .srt captions, in the active brand. Produces a storyboard to check layout before rendering, and H.264 mp4. Use when asked for a video or animation that explains a formula, a math concept like a derivative or an integral, statistics, an algorithm, a data structure or a piece of code, 3Blue1Brown style, or when a report or class needs an animated explanation. Usage: cutroom-math <what to explain> [duration=60s] [format=1920x1080|1080x1920]"
metadata:
  version: "2.0.0"
---

# cutroom-math: math and code videos (ManimGX 0.1.1)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`. They include the brand rules.

`cutroom` = `~/.local/share/cutroom/bin/cutroom`. `U` = `~/.local/share/cutroom/upstream/manimgx/skills/manimgx`.

## Step 0: components

Run `cutroom doctor --json`. The video needs `math` (~400 MB); narration also needs `voice` (~340 MB of model). If one
is missing, give the size and offer `cutroom-init <component>`. Without `voice`, make the video without narration.
Never use ManimGX's default voice (Step 2).

## Step 1: rules, style and script

1. Run `cutroom job "<title>"` and keep the path as `$J`.
2. Read `references/style-and-nuances.md` in this skill's folder (`skills/cutroom-math/references/style-and-nuances.md`):
   it defines the **default editorial style, three-zone spatial hierarchy, live telemetry readouts, narration pacing,
   continuous-stage transitions, and strategic `earshot` sound design**. Follow these defaults unless the person asks
   for a different style, aspect ratio (`16:9`, `9:16`, `1:1`), or palette.
3. **Ask about sound effects (`cutroom-sound`) and format** when planning (unless already stated):
   - Aspect ratio & canvas: `16:9` landscape or `9:16` vertical; **Dark Editorial Stage** (brand `deep` / `#0B0B10`) or
     **Warm Paper Editorial** (`#FAF8F5`).
   - Sound effects (`cutroom-sound` / `earshot`): ask whether the person wants **strategic tactile SFX** added on key
     mathematical transitions, steps, curve morphs, and theorem reveals (recommended when `sound` is installed, or offer
     `cutroom-init sound`), or narration-only.
4. Read `U/SKILL.md`: it is the authoring rule (scene, `inspect`, draft, final render). Skip its installation part
   (`uv tool install`, `uvx`): the `manimgx` shortcut is on the PATH. For a feature you do not know, read the guide in
   the primer `https://manimgx.academa.ai/llms.txt`. The full reference (`llms-full.txt`, 2.4 MB) goes to `$J/work/`:
   download it once and `grep` it, never read it whole.
5. Write `$J/src/SCRIPT.md` with `cutroom-script` (scenes, what appears, the speech of each, and optional SFX cues).
   Over ~30 s, confirm with the person before animating.

## Step 2: scene

Get the brand: `cutroom brand show --json` (colors, fonts) and read its `DESIGN.md`. Write `$J/src/scene.py`:

```python
import json, subprocess
import manimgx as m
from cutroom_voice import manimgx_voice

B = json.loads(subprocess.run(["cutroom", "brand", "show", "--json"], capture_output=True, text=True).stdout)
C, F = B["colors"], B["fonts"]
m.config.background_color = C["deep"]      # solid background: deep, primary or background


class Explainer(m.Scene):
    voice = manimgx_voice("narrator", pronounce={"ManimGX": "manim G X"})   # local voice (cutroom-voice)

    def construct(self) -> None:
        title = m.Text("Binary search", font=F["display"], weight=m.SEMIBOLD, font_size=64, color=C["on_primary"])
        self.say("[Binary search] halves the problem at every step.", m.Write(title))
```

- `import manimgx as m`. Never `import manim` nor `pip install manim`: ManimGX is a different engine with the Manim
  Community API.
- **Voice:** every scene with speech declares `voice = manimgx_voice(<spec>, ...)`, where the spec is any voice from
  `cutroom-voice` (profile, preset, `af_heart@0.95`, blend, `clone:name`; nothing = the default). ManimGX's default
  voice is ElevenLabs through fal.ai: it would send the text out and requires `FAL_KEY`. Do not use it.
- **Sync:** in `self.say("text with [marked] words", anim1, anim2)`, each animation starts at the bracketed words, in
  order. Kokoro does not return word timings, so ManimGX estimates from length: leave slack and check the draft. The
  speech becomes the `.srt` caption. An empty `[]` at the start delays the animation to the start of the speech.
- **Pronunciation:** `pronounce={"written": "spoken"}` changes only the audio; the caption keeps the text. Check a word
  first with `voice test narrator "f prime of x"`. Formulas are read as written in `say`: write the speech as you
  want it heard ("x squared"), and the formula on screen.
- **Cache:** lines live in `$J/src/voice/`, next to the scene. That is cache, not delivery. Only new lines, or lines
  with a changed voice, speed or pronunciation, are synthesized again.
- **Brand:** solid background (`deep`, `primary` or `background`), text in `on_primary` on dark (or `text` on light),
  highlight in `accent` (one at a time), `scale` for ordered things, `success`/`warning`/`danger` only for state.
  Fonts: `font=F["display"]` for titles, `F["text"]` for text, `F["mono"]` for code; registered on the system by
  `cutroom brand use`. Prefer a mono without ligatures (e.g. JetBrains Mono NL): with ligatures `->` shows as `→`,
  and `disable_ligatures` does not turn that off. Check with `fc-list | grep -i "<family>"` (macOS: `fc-list` from
  ManimGX's environment, or the Font Book): a missing font becomes a serif without warning. Weight through ManimGX's
  constants: `weight=m.HEAVY` (900), `m.BOLD`, `m.SEMIBOLD` (600), `m.LIGHT` (300). An unknown string such as
  `"BLACK"` silently falls back to 400. Logo only at the end of a piece that speaks for the brand.
- Formulas with `m.MathTex(r"...")`. Code with `m.Code(code_string=..., language="python")`. `m.Code` only has the
  "vim" style: a `#000080` comment vanishes on a dark background. Recolor glyph by glyph (map the "vim" colors to brand
  colors) and use your own panel, with `background_config={"fill_opacity": 0, "stroke_width": 0}`; highlight the
  running line with `set_z_index`. `examples/math-derivative/src/scene.py` shows the brand, live readouts
  (`always_redraw`, `ValueTracker`) and a traced graph.
- `.animate` (or `Transform`) inside a `say` only on an object already on screen. If it enters in the same `say`, the
  object appears from the start of the speech: split into two `say`, or use `FadeIn`/`Create`, which wait their turn.
- Layout with `VGroup`, `next_to`, `arrange` and `to_edge`, so labels follow objects. Changing values: `ValueTracker`
  with `always_redraw`.
- **Editorial hierarchy & nuances (`references/style-and-nuances.md`):**
  - **Three zones:** top-left context breadcrumb + active formula (coloring only the focal symbol in `accent`); center
    geometric/3D mechanism with a live monospace readout (`ValueTracker` + `always_redraw`) proving the claim in real
    time; bottom 2-line captions with 1–2 keywords accented.
  - **Restraint:** thin muted grey (`1–1.5 px`, opacity `0.35`) for grids and reference lines; bold `4–6 px` accent
    stroke for the single active curve or vector; `0.12–0.22` opacity for area/volume fills.
  - **Pacing & transitions:** open with a concrete hook or paradox in the first 3 s; show geometry first, perturb it
    second, and lock in the symbolic formula third with a `0.35–0.45 s` micro-pause (`self.wait(0.4)`). Morph or
    dissolve between scenes on a continuous stage rather than hard-clearing the screen.

## Step 3: verify

```bash
. ~/.local/share/cutroom/env.sh && cd "$J/src" && manimgx inspect scene.py Explainer -o "$J/work/storyboard.png"
```

- `inspect` writes the storyboard and exits 1 on a 2D layout problem. **Open the PNG** and fix overlaps and cuts. Use
  `-t 0.5,8,end` for specific moments. Sampling is sparse: touching labels, a duplicated arrow or an object appearing
  over another that is still fading only show in the frames.
- Draft: `manimgx render scene.py Explainer -r 1280x720 --fps 30 -o "$J/work/draft.mp4"`. Watch the motion, not only
  frames: `cutroom edit sheet "$J/work/draft.mp4" -o "$J/work/sheet.png"` gives a contact sheet;
  `cutroom edit frames "$J/work/draft.mp4" -o "$J/work/frames" --every 3` gives single frames.
- "no GPU adapter": the agent's sandbox is hiding the GPU. On Linux, ManimGX falls back to CPU (lavapipe). If it still
  fails, run the command outside the sandbox (Claude Code: ask to disable the sandbox for that command; Codex: ask
  for approval).

## Step 4: final render and delivery

- Final: `manimgx render scene.py Explainer -o "$J/out/<slug>.mp4"`. Default 1920 × 1080 at 60 fps; vertical
  `-r 1080x1920`. For artifacts or email, `-r 1280x720 --fps 30` usually stays under 15 MB, or
  `cutroom edit compress ... --preset artifact`.
- The render writes the `.srt` and the storyboard sheets (`<slug>.storyboard.png`, `-2.png`...) next to it.
- **Variable frame rate:** ManimGX only writes a frame when the image changes, so a "30 fps" mp4 averages lower and
  `-ss`/`-t` cut at the wrong time. `cutroom edit gif` already decodes everything and trims after `fps`. For tools
  that need constant rate: `ffmpeg -i in.mp4 -fps_mode cfr -r 30 -c:a copy out.mp4`.
- Captions burned in for social: `cutroom edit captions "$J/out/<slug>.mp4" "$J/out/<slug>.srt" -o "$J/out/<slug>-captions.mp4"`;
  vertical cut: `cutroom edit reframe ... --aspect 9:16`.
- **Strategic sound effects (`cutroom-sound` / `earshot`):** when the person chose SFX, write `$J/src/cues.json` with
  tactile cues aligned to the scene's visual beats (`ui_pop/soft` on section headers, `fit/tick/domino` with
  incrementing `seed` on discrete steps, `fit/whoosh.short/bamboo_swish` with `align: "peak"` on curve sweeps,
  `pluck/kalimba_soft` on the theorem lockup, at `gain_db: -13` to `-18`), mix onto the rendered video with
  `cutroom edit sfx "$J/out/<slug>.mp4" --cues "$J/src/cues.json" --stem "$J/work/sfx-stem.wav" -o "$J/out/<slug>-sfx.mp4"`,
  and inspect the alignment with `earshot sheet "$J/out/<slug>-sfx.mp4" --cues "$J/src/cues.json" -o "$J/work/sound-sheet.png"`.
- Deliver `$J/out/<slug>.mp4`, the `.srt` (and `src/cues.json` when SFX are used) and the scene in `$J/src/scene.py`.
- For slides: `manimgx present scene.py` opens the sections in the browser (`self.next_section()` marks each slide),
  and `--pdf` makes the handout.
