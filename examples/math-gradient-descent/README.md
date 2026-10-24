# Example: Gradient descent, from one weight to two (cutroom-math / ManimGX + Kokoro + earshot)

**Request:** "Explain the gradient in 2D, talk about the learning rate, explain the equation, and extrapolate to 3D, in under 50 seconds, with the fluid, dynamic look of the best vertical math explainers." This is the repository's official math example.

<p align="center">
  <a href="out/gradient-descent.mp4"><img src="out/preview.gif" width="320" alt="Gradient descent: a zoom that turns a curve into a line, three learning rates, then a surface"></a>
</p>
<p align="center">
  <a href="out/gradient-descent.mp4"><strong>▶ Watch &amp; listen with sound (<code>out/gradient-descent.mp4</code> · 49.8 s · 1080×1920 vertical)</strong></a>
</p>

[`out/gradient-descent.mp4`](out/gradient-descent.mp4) (49.8 s, 1080x1920 @ 30 fps, H.264 + AAC, 13 MB, -16 LUFS) · [`out/gradient-descent.srt`](out/gradient-descent.srt) · [`out/sheet.png`](out/sheet.png) (contact sheet) · [`out/sound-sheet.png`](out/sound-sheet.png) (earshot sheet) · [`src/cues.json`](src/cues.json) (122 earshot cues, generated) · source in [`src/`](src)

| File | Description |
|---|---|
| [`out/gradient-descent.mp4`](out/gradient-descent.mp4) | Deliverable: narrated vertical video with 122 `earshot` cues |
| [`out/preview.gif`](out/preview.gif) | 12 s silent preview of the 3D half: the surface, the two slopes, the arrow and the descent while the camera orbits |
| [`out/sheet.png`](out/sheet.png) | 4×3 contact sheet |
| [`out/sound-sheet.png`](out/sound-sheet.png) | `earshot sheet`: spectrogram, loudness and cue sync (81% of cues within 40 ms of their beat) |
| [`src/SCRIPT.md`](src/SCRIPT.md) | Script with six scenes and facts F1 to F6; `cutroom script check` passes with no warnings |
| [`src/scene.py`](src/scene.py) | The ManimGX scene; it also writes `work/events.json` with the time of every beat |
| [`src/make_cues.py`](src/make_cues.py) | Turns those events into `src/cues.json`: one sound per sentence, zoom tick, hop, tab and camera move |

## What happens

One continuous camera, no cuts. Captions reveal word by word at the top, a breadcrumb tracks the chapter (`slope · step · rate · 3D`), and live readouts prove each claim in numbers.

1. **Landscape (0 to 4 s).** A loss surface fades in while the camera swings round it. It fades out and the camera goes side-on: what is left is one slice, a 2D curve.
2. **Zoom and slope (4 to 13 s).** The camera dives onto a point of the curve. The curve is redrawn at constant stroke width, so it straightens against its tangent: the shaded gap falls from `593 px` to `1 px` while `zoom ×` climbs to 1600. A short label (`slope`) flashes and leaves. Then the point slides along the curve and the slope readout changes sign.
3. **Step and the rule (13 to 22 s).** An arrow points against the slope. The update rule is built piece by piece, each term appearing as it is spoken, with a label under it: `w(t+1)` *new weight*, `w(t)` *old weight*, `lr` *learning rate* (yellow), `f′(w(t))` *slope* (blue). Then the point hops down the curve; the flatter the curve, the shorter the hop.
4. **Learning rate (22 to 32 s).** Three runs from the same start: `lr = 0.04` crawls, `lr = 0.25` settles in a few hops, `lr = 1.5` bounces between +2.05 and −2.05 and never settles.
5. **Two weights (32 to 46 s).** The old curve stays as a slice of a surface drawn as a mesh, seen from above in an isometric view. The figure then turns: the camera orbits it and closes in on the point, so the two tangent lines (one per weight) and the gradient arrow are seen from the side where they are not hidden. The arrow flips on the tangent plane while the view keeps rotating, and the camera follows the point down in 12 steps from yet another side, with live `loss` and `|∇L|`. The mesh fades toward the top edge so it never reaches the text.
6. **Close (46 to 50 s).** `Billions of weights. One rule.` and the logo.

Nothing stays pinned to the top: each topic is introduced by a label that fades in, is read for two seconds and leaves; the rule leaves before the learning-rate section.

## Why it moves the way it does

- The zoom is done in screen space, not with the camera: the curve is recomputed each frame as `c + z·(x − x₀, f(x) − f(x₀))`. Strokes keep their width, and the `off straight` readout is measured on the same points.
- The rule, the topic labels and the captions are alpha-driven animations on objects that are always in the scene. Captions use one animation (old caption out, new one in word by word). A `FadeIn` inside a `Succession` starts early in ManimGX and shows the words ahead of time.
- Sounds are not placed by hand: the scene logs the start of every sentence (an invisible animation records `self.time`), and `make_cues.py` places ticks, hops and sweeps from those times plus each animation's known offsets.

## How it was made

```bash
. ~/.local/share/cutroom/env.sh

# 1. Check the script, export speech and pronunciation
cutroom script check src/SCRIPT.md
cutroom script speech src/SCRIPT.md -o src/speech.txt --pronounce src/pronounce.json

# 2. Render the scene (narration is synthesized per sentence and cached in src/voice/)
(cd src && manimgx render scene.py GradientDescent -r 1080x1920 --fps 30 -o ../work/raw.mp4)
cp work/raw.srt out/gradient-descent.srt

# 3. Cues from the logged events, mix, then normalize to -16 LUFS
python3 src/make_cues.py
cutroom edit sfx work/raw.mp4 --cues src/cues.json -o work/mixed.mp4
cutroom edit loudnorm work/mixed.mp4 -o out/gradient-descent.mp4 --target -16

# 4. Sheets and preview
cutroom edit sheet out/gradient-descent.mp4 -o out/sheet.png
cutroom edit gif out/gradient-descent.mp4 -o out/preview.gif --start 34 --duration 12 --fps 8 --width 240
earshot sheet out/gradient-descent.mp4 --cues src/cues.json -o out/sound-sheet.png
```

The style rules behind it are in [`skills/cutroom-math/references/style-and-nuances.md`](../../skills/cutroom-math/references/style-and-nuances.md), section 6.
