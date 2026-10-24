# Example: Gradient Descent (cutroom-math / ManimGX + Kokoro + earshot)

**Request:** "26 s ManimGX explainer demonstrating the new cutroom-math standard: 3-Zone Spatial Hierarchy, tactile loss landscape, live monospace telemetry, synchronized editorial captions, and strategic earshot sound design."

<p align="center">
  <video src="out/gradient-descent.mp4" controls preload="metadata" poster="out/sheet.png" width="800">
    <a href="out/gradient-descent.mp4"><img src="out/preview.gif" width="800" alt="Watch gradient-descent.mp4 with narration and earshot sound effects"></a>
  </video>
</p>
<p align="center">
  <a href="out/gradient-descent.mp4"><strong>▶ Watch &amp; listen with audio (<code>out/gradient-descent.mp4</code> · 25.78 s · 1080p)</strong></a>
</p>

[`out/gradient-descent.mp4`](out/gradient-descent.mp4) (25.78 s, 1920x1080 @ 40.72 fps, H.264 + AAC stereo, 1.40 MB) · [`out/gradient-descent.srt`](out/gradient-descent.srt) (subtitles, 52 lines) · [`out/sheet.png`](out/sheet.png) (contact sheet) · [`out/sound-sheet.png`](out/sound-sheet.png) (earshot audio-visual sheet) · [`src/cues.json`](src/cues.json) (10 earshot SFX cues) · source in [`src/`](src)

| File | Description |
|---|---|
| [`out/gradient-descent.mp4`](out/gradient-descent.mp4) | Deliverable: 25.78 s explainer video with embedded narration, 10 strategic `earshot` SFX cues, and live telemetry (1.40 MB) |
| [`out/gradient-descent.srt`](out/gradient-descent.srt) | Timed subtitles with 13 synchronized cues |
| [`out/preview.gif`](out/preview.gif) | Animated preview GIF of the descent trajectory and live telemetry (481 KB) |
| [`out/sheet.png`](out/sheet.png) | 4×3 contact sheet showing 12 keyframes with timestamps |
| [`out/sound-sheet.png`](out/sound-sheet.png) | `earshot sheet` audio-visual contact sheet showing spectrogram, waveform, loudness, and 10 cue sync markers |
| [`src/SCRIPT.md`](src/SCRIPT.md) | Structured production script with 4 scenes and verified facts F1–F5 |
| [`src/scene.py`](src/scene.py) | ManimGX scene implementing the 3-zone spatial layout, continuous updates, and telemetry |
| [`src/cues.json`](src/cues.json) | 10 sample-accurate sound cues mapped to visual events |

## The 3-Zone Spatial Hierarchy Applied

Following the new standard in [`skills/cutroom-math/references/style-and-nuances.md`](../../skills/cutroom-math/references/style-and-nuances.md):

1. **Zone 1: Context Breadcrumb & Formula (Top-Left)**
   - Eyebrow: `Optimization · gradient step` in Inter SemiBold muted mauve (`#8E929F`).
   - Formula: $w_{t+1} = w_t - \eta \nabla L(w_t)$ in warm white with the update term $\eta \nabla L$ highlighted in brand Hot Signal (`#FF2D6F`).
2. **Zone 2: Tactile Mechanism + Live Telemetry (Center Stage)**
   - Smooth non-convex loss bowl $L(w) = \frac{1}{2}w^2 + 0.3\cos(2.5w)$ with translucent area fill (`opacity=0.12`).
   - Dynamic tangent line (`#FF9BC0`) tracking local slope.
   - Negative gradient descent vector (`#FFC43D`) pointing in the step direction.
   - Monospace telemetry HUD (`JetBrains Mono NL`) updating live each frame:
     `step: 04  |  w: +0.81  |  L(w): 0.207  |  ∇L: +0.25  |  step: -0.05`
3. **Zone 3: Synchronized Editorial Captions (Bottom Zone)**
   - Phrase-by-phrase captions centered at the bottom, highlighting key concepts (*best weights*, *loss landscape*, *step in reverse*, *converges*) in focal brand accents.

## Sound Design (`earshot`)

10 strategic tactile sound cues mixed sample-accurately at -18 to -22 dBFS under the voice:
- `fit/land.light/fingertip_book` on opening setup;
- `fit/whoosh.short/bamboo_swish` on loss curve trace and descent sweep;
- `fit/tick/domino` on discrete parameter updates;
- `swipe/velvet` on tangent slope line adjustments;
- `pluck/kalimba_soft` (pitch E5) on convergence lockup at the minimum.

## How to reproduce

```bash
. ~/.local/share/cutroom/env.sh

# 1. Synthesize narration from script
tts -f src/speech.txt -o work/narration.wav --voice narrator --pronounce src/pronounce.json

# 2. Render ManimGX scene
manimgx render src/scene.py GradientDescent -o work/raw.mp4

# 3. Mix strategic earshot SFX cues
cutroom edit sfx work/raw.mp4 --cues src/cues.json -o out/gradient-descent.mp4

# 4. Generate contact sheet and sound analysis
cutroom edit sheet out/gradient-descent.mp4 -o out/sheet.png
earshot sheet out/gradient-descent.mp4 --cues src/cues.json -o out/sound-sheet.png
```
