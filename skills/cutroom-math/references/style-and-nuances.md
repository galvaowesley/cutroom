# Editorial Math Video Style, Transitions, Narration & Sound Nuances

By default, `cutroom-math` produces editorial math and science videos that feel tactile, cinematic, and effortless to follow. The person can always override the aspect ratio (`9:16` portrait, `16:9` landscape, `1:1` square), background mode (dark stage vs warm paper), brand palette, or density — ask or follow their request when given, and use these defaults whenever unspecified.

---

## 1. Three-Zone Spatial Hierarchy

Every frame is organized into three clean, non-overlapping zones with generous breathing room (`>= 12%` open margin around the center mechanism):

| Zone | Position | What lives here | Typography & Color |
|---|---|---|---|
| **1. Context Breadcrumb & Formula** | Top-left (or top-center in 9:16) | A muted eyebrow that updates as the argument advances (`Laplace · counting cases`, `Calc I · local linearity`, `Bayes · updating prior`), with the active formula (`MathTex`) directly below it | Eyebrow in `F["text"]` `SEMIBOLD` (muted grey `#8E929F`); formula in warm white/ink with **only the active variable or number colored in the focal accent** |
| **2. Tactile Mechanism + Live Telemetry** | Center stage (`55–65%` of frame height) | **One** geometric, 3D, or particle mechanism at a time, paired with a live monospace readout (`ValueTracker` + `always_redraw`) that proves the claim numerically as the geometry moves | Construction/grid lines at `1–1.5 px` muted grey (`opacity=0.35`); focal curve/vector at `4–6 px` accent; area/volume fills at `0.12–0.22` opacity; telemetry in `F["mono"]` (`tabular-nums`) |
| **3. Synchronized Editorial Captions** | Bottom zone (2 lines max, centered) | Phrase-by-phrase progressive caption (`.srt` or on-canvas text) where **1–2 semantic keywords per sentence are highlighted in the active accent color** | `F["text"]` `BOLD`, high-contrast ink/white, keyword in `accent` matching the object currently moving on screen |

---

## 2. Two Default Palettes (Brand-Adaptable)

Unless the person requests a specific style, pick the palette that matches the active brand (or offer the choice between **Dark Editorial Stage** and **Warm Paper Editorial**):

### A. Dark Editorial Stage (Default for `cutroom` brand & philosophical/3D/probability pieces)
- **Canvas:** Brand `deep` (`#16072B`) or obsidian (`#0B0B10`)
- **Primary Ink:** `#F4F3EF` (warm off-white, never harsh pure `#FFFFFF` on long formulas)
- **Muted Guide / Grid / Inactive:** `#8E929F` at `0.30–0.45` opacity
- **Single Focal Accent per Scene:** Brand `primary`/`accent` (`#FF2D6F` Hot Signal, `#FF9E3D` Amber, `#38BDF8` Cyan, or `#10B981` Emerald). When a second quantity is contrasted (e.g. secant vs tangent, prior vs posterior), use a cool secondary (`#38BDF8`) against the warm primary (`#FF2D6F` or `#FF9E3D`).

### B. Warm Paper Editorial Stage (Default for `paper` brand & textbook/calculus miniatures)
- **Canvas:** `#FAF8F5` (warm editorial paper)
- **Primary Ink:** `#18181B` (deep charcoal)
- **Muted Guide / Secant / Grid:** `#A1A1AA` (`1.2 px` stroke)
- **Single Focal Accent per Chapter:** `#3B5BDB` (indigo), `#0CA678` (teal), or `#D9480F` (vermilion).

---

## 3. Signature Visual Metaphors & Telemetry Patterns

Prefer concrete, physical mechanisms over walls of algebra:

1. **Live Numerical Telemetry (`ValueTracker` + `always_redraw`):**
   - Never just state a limit or derivative — show a live monospace counter updating every frame alongside the geometry:
     - Zooming into a curve or 3D surface until it flattens: `zoom ×3` → `×1,600` paired with `off straight: 589 px` → `1.0 px`.
     - Secant approaching tangent: `h = 2.00` → `0.00` paired with `Δy/Δx = 4.000` converging to `f'(2) = 2.000`.
     - Frequentist relative frequency: `n = 10` → `500` trials with live `P(A) = 0.502` stabilizing on a horizontal dashed asymptote.
2. **Stacked Synchronized Plots:**
   - For rate-of-change vs accumulation (e.g. Fundamental Theorem of Calculus, PDF vs CDF, loss vs gradient), stack two aligned coordinate systems vertically (`A(x)` above, `f(x)` below) linked by a single vertical dashed cursor line sweeping across `x`.
   - When adding a thin slice `Δx` of height `f(x)` in the bottom graph, extrude that exact strip and morph/slide it onto the top graph as the vertical step `ΔA`.
3. **Tactile 3D & Isometric Objects:**
   - Represent discrete sample spaces (`6 × 6` outcomes, matrix cells, state spaces) as bevelled 3D prisms or tiles that rise (`shift(OUT * h)`) and light up in the accent hue when selected (`6 / 36`).
   - Represent axiom systems or high-dimensional spaces as a translucent 3D wireframe cube (`Ω`) that rotates smoothly and projects 2D shadows onto its back walls.
4. **Bayesian & Distribution Morphing:**
   - Show a prior curve `P(H)` on a clean horizontal axis (`0` to `1`); drop small glowing data cubes onto the axis one by one, and smoothly morph (`Transform`) the curve into a sharper, taller posterior peak with each observation.
   - To show convergence across different starting beliefs, draw 4–5 distinct prior curves in muted grey and animate all of them collapsing onto the same accent posterior curve as evidence accumulates.

---

## 4. Narration, Pacing & Transition Choreography

1. **Hook in the First 3 Seconds:**
   - Open with a concrete question, paradox, or visual tension (*"What does a 30% chance of rain actually mean?"*, *"How can an area have a slope?"*), never with *"In this video we will learn..."*.
   - Put the central geometric object on screen during the very first sentence.
2. **Progressive Disclosure (Geometry → Perturbation → Symbol):**
   - **Beat 1 (Setup):** Draw the axes, object, or sample space while naming the intuition.
   - **Beat 2 (Action):** Perturb the tracker (`x.animate.set_value(...)`) so the viewer *sees* the behavior before the formal notation appears.
   - **Beat 3 (Verdict):** Reveal or highlight the compact equation (`MathTex`) and pause `0.35–0.45 s` (`self.wait(0.4)`) so the eye can read the formula while the voice rests.
3. **Continuous Stage Transitions (No Hard Slide Cuts):**
   - Keep the canvas continuous from scene to scene. Instead of clearing the whole screen abruptly (`self.clear()`), morph the active element into the next scene's anchor (`ReplacementTransform` or `FadeTransform` over `0.4 s`) while fading out secondary guides and updating the top-left breadcrumb.
   - Use `rate_func=m.rate_functions.ease_in_out_cubic` (or `smooth`) with `run_time=0.45` to `0.8` for structural moves, and `run_time=1.8` to `3.2` for continuous `ValueTracker` sweeps.

---

## 5. Strategic Sound Design (`cutroom-sound` / `earshot`)

Always ask the person whether they want strategic sound effects added to their math video. When enabled, keep SFX **tactile, sparse, and 10–16 dB below narration (`gain_db: -13` to `-18`)**:

| Mathematical event | Recommended `earshot` cue | `align` | Why it works |
|---|---|---|---|
| Breadcrumb / chapter title updates | `ui_pop/soft` or `fit/land.light/fingertip_book` | `onset` | Gives a subtle physical weight to a new section without breaking concentration |
| Discrete step (`h` halving, coin flip, grid cell lighting up, counter tick) | `fit/tick/domino`, `tap/knuckle`, or `knock/wood` (increment `seed: 0, 1, 2...`) | `onset` | Makes discrete mathematics and step-by-step limits feel tactile |
| Smooth curve trace, `ValueTracker` sweep, or prior→posterior morph | `fit/whoosh.short/bamboo_swish` or `swipe/velvet` | `peak` | Gentle air movement peaking at the steepest part of the motion |
| 3D prism extrusion or slice `ΔA` locking into place | `knock/desk` or `cut_hit/sub` | `onset` | Grounds 3D geometry with a soft, warm low-mid body |
| Key theorem reveal, convergence lockup, or final identity (`f'(x)`, `P(H\|E)`) | `pluck/kalimba_soft` (e.g. `pitch: "E5"`) or `mallet/celesta` | `onset` | Marks the intellectual "aha" moment with a single warm acoustic note |

### Workflow to attach SFX to a ManimGX video

1. Log the timestamps of your key visual beats (from the rendered `.srt` or by printing `round(self.time, 2)` at key animations in `scene.py`).
2. Write `$J/src/cues.json` with `5–10` strategic cues (never on every sentence).
3. Mix sample-accurately with `cutroom edit sfx`:
   ```bash
   . ~/.local/share/cutroom/env.sh && cutroom edit sfx "$J/work/raw.mp4" \
     --cues "$J/src/cues.json" \
     --stem "$J/work/sfx-stem.wav" \
     -o "$J/out/<slug>.mp4"
   ```
4. Inspect the audio-visual alignment sheet with `earshot sheet "$J/out/<slug>.mp4" --cues "$J/src/cues.json" -o "$J/work/sound-sheet.png"` and view `$J/work/sound-sheet.png`.

---

## 6. Perspective, camera and zoom (the reference look)

The reference videos this style comes from are vertical (9:16), one mechanism at a time, and built on motion that never stops: a camera that never cuts, captions that arrive word by word, and numbers that climb while the picture changes. `examples/math-gradient-descent/src/scene.py` is the worked example (a 3D surface sliced into a 2D curve, a zoom to a line, three learning rates, the curve swept back into a surface).

1. **Default to 9:16 for explainers** (`-r 1080x1920`, frame 8 × 14.2 units): chapter tabs and captions top-left, live readouts under them, the mechanism in the middle. Landscape stays for slides and classes.
2. **One `m.ThreeDScene` for the whole piece, even the flat parts.** A 2D view is the camera at `phi=90°`, `theta=-90°` looking at the x-z plane; the curve is a slice of the surface. Tilting the camera (`phi` 90 to 64, `theta` -90 to -58) turns the curve into a surface without a cut, and fading the surface out leaves the slice as the 2D curve.
3. **Zoom in screen space, not with the camera.** For "a curve is a line up close", redraw the curve each frame as `c + z·(x − x₀, f(x) − f(x₀))` with a log-zoom `ValueTracker` (about 0.45 s per doubling, linear in the log), over a fixed tangent line and a shaded gap between them. Strokes keep their width, the gap visibly collapses, and a readout of the gap in pixels (`off straight 593 px` to `1 px`) proves it. A camera zoom would fatten strokes and fill the screen.
4. **Show scale while zooming:** a faint fixed grid (opacity 0.07), the readout `zoom ×N` climbing, and the point pinned at one screen position.
5. **Captions: word by word, top-left,** two lines, the keyword bold in the focal accent, the rest in a muted tint. Drive the whole caption with one `UpdateFromAlphaFunc` (old out, each new word in on its own alpha window), with the words in the scene at opacity 0. Do not put a `FadeIn` inside a `Succession` or a `LaggedStart`: ManimGX can start it early and the words show before the voice.
6. **One bracketed span per sentence:** `self.say("[Sentence one.] [Sentence two.]", anim_one, anim_two)`. Each span carries its caption and the sentence's own animation. An invisible animation (`UpdateFromAlphaFunc` on a dummy dot) logs `self.time` when its span starts.
7. **Readouts and chips:** a monospace readout per beat (`step`, `loss`, `|∇L|`, `lr`), swapped, never crossfaded in place. Re-anchor each `DecimalNumber` after `set_value` (`.next_to(label, RIGHT)`). A large chip at the bottom names each variant (`lr = 1.5 · overshoots`).
8. **Compare variants on the same curve:** runs from the same start, one after another, each with its own trail color and its own tick sound (small taps for the slow one, ticks for the good one, knocks panned left and right for the one that bounces). Simulate them first and pick values that show the effect inside the plot (`lr = 1.5` ping-pongs at ±2.05).
9. **A 3D scene must never hide the point.** Draw the surface as a mesh (about 10% fill, lines at 0.75 opacity) and look from above in an isometric view (`phi` 46 to 52°, `theta` about -45°, a long `focal_distance` of about 45 for weak perspective), small in the establishing shots. For the descent, glide the camera frame onto the point and follow it (`UpdateFromAlphaFunc` on `cam.frame`, zoom about ×1.6), with the point lifted above the surface (`+0.11`). A fixed viewpoint is not enough: even from above, part of the figure hides what sits behind a ridge. **Turn the figure** (orbit `theta` by 60 to 100° over the 3D section, in one move per beat) and close in (zoom ×1.5) on the point for the arrows and the flip, so every element is seen from a side where it is clear. Fade the mesh toward the top edge with a stack of background-colored strips, under the captions, so it never runs into the text.
    - Introduce, do not pin: a topic is a label that fades in, is read for two seconds and leaves. Readouts are per beat; the rule leaves when the next topic starts.
    - Explain an equation before using it: build it term by term as the words are spoken, each term with a short colored label under it (`new weight`, `old weight`, `learning rate`, `slope`).
10. **Moves with meaning:** flip an arrow 180° about the plane's normal for "the opposite way"; hop a point step by step with an eased-per-step rate function and one tick per landing; keep a slow camera drift on still beats.
11. **Keep it under the length you were given.** Kokoro speaks about 4 words per second at 0.95: write the sentences first, render a draft at `-r 540x960 --fps 24`, read the event times, and trim animations before words.
12. **Sound from events, not by hand.** The scene writes `work/events.json`; a small `make_cues.py` turns sentence starts and animation offsets into `cues.json` (a soft pop per sentence, a tick per zoom doubling, a knock per hop, a swish per camera move, a kalimba note per arrival). For an explainer like this, 80 to 110 cues in 47 s is a dense, rhythmic mix at 12 to 22 dB under the voice, normalized to -16 LUFS afterwards.

### The building blocks are in the harness

`harness/cutroom_mathkit.py` (`import cutroom_mathkit as kit`; the `manimgx` shortcut already has the harness on `PYTHONPATH`) holds what this section describes, so a new scene does not rewrite it: `kit.caption` and `kit.cap_swap` (word-by-word captions), `kit.topic_label` and `kit.topic_anim` (introduce, do not pin), `kit.show_parts` (build an equation term by term), `kit.hop_rate` (ease every discrete step), `kit.EventLog` (log every beat for the sound cues), and, for 3D, `kit.iso_view`, `kit.glide` (follow a moving point), `kit.orbit` (swing round the figure and close in) and `kit.top_fade` (fade the mesh under the text).

### Checklist before rendering any 3D beat

1. Is the subject (the point, the arrow, the trail) visible from the camera's side, or does a ridge hide it? Look at the draft frames of that beat, not only the establishing shot.
2. Mesh, not a solid: about 10% fill, lines at 0.75 opacity.
3. Weak perspective (`focal_distance` about 45) and a view from above (`phi` 46 to 52°).
4. One move per beat: `orbit` to a new `theta`, `glide` onto the point, close in (zoom ×1.5) for arrows and flips; total orbit 60 to 100° or more over the section.
5. The point is lifted above the surface (`+0.11`) and arrows are thick enough to read at phone size.
6. Nothing from the surface reaches the text: `top_fade` under the captions.
