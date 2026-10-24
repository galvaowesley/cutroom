---
name: cutroom-sound
description: "Sound effects, procedural synthesis and audio ears for coding agents, powered by earshot (Leonxlnx/earshot): 252-sound procedural and fitted bank (`earshot sfx`), coherent film kits (`earshot kit`), sample-accurate cue mixing onto motion and math videos (`cutroom edit sfx`), listening and sync critique of existing videos (`earshot measure`, `sheet`, `timeline`, `critique`, `describe`, `match`, `find`, `rank`, `ab`, `realness`), and sound synthesis in code (`earshot forge`, `earshot fit`). Use when adding sound effects to a motion or math video, designing a sound kit, synthesising a new sound effect, or listening to and auditing an existing video or audio file. Usage: cutroom-sound <video, cue sheet or sound description>"
metadata:
  version: "2.0.0"
---

# cutroom-sound: sound effects and audio ears for coding agents (`earshot`)

Read the shared conventions first: `~/.local/share/cutroom/harness/conventions.md`.

Then read the upstream `earshot` skill and sound-design guides cloned at the pinned tag:

- `~/.local/share/cutroom/upstream/earshot/skills/earshot/SKILL.md` — full CLI reference (`sfx`, `kit`, `measure`, `describe`, `match`, `rank`, `find`, `realness`, `timeline`, `sheet`, `critique`, `forge`, `fit`)
- `~/.local/share/cutroom/upstream/earshot/skills/real-sound/SKILL.md` — acoustic principles (modal synthesis, impact excitation, air/turbulence, avoiding "synth/8-bit" artifacts)
- `~/.local/share/cutroom/upstream/earshot/docs/SFX.md` — bank categories, roles, pitch/duration/apex knobs, level over bed (`--bed-db`), and kit manifests
- `~/.local/share/cutroom/upstream/earshot/docs/INTEGRATION.md` — aligning `onset_s`, `peak_s`, and `end_s` to video frame timestamps

Shortcuts (after `. ~/.local/share/cutroom/env.sh`): `earshot` and `cutroom edit sfx`.

## Step 0: check installation

Run `. ~/.local/share/cutroom/env.sh && earshot --version`.

- If `sound` is not installed, tell the person what it downloads (`~1.5 GB` Python environment; `sfx`, `kit`, and `measure` run immediately with **zero model downloads**) and offer `cutroom-init sound`.
- Commands that listen semantically (`describe`, `match`, `rank`, `find`, `realness`, `timeline`, `critique`, `forge`, `fit`) use two open models (CLAP + AudioSet AST, `~1.1 GB` total, cached locally in `~/.local/share/cutroom/models/earshot`). When needed, fetch them once with:
  ```bash
  . ~/.local/share/cutroom/env.sh && earshot doctor --fetch
  ```

## Step 1: always offer sound design on motion and math videos

When planning a video in `cutroom-motion`, `cutroom-math`, `cutroom-script`, or `cutroom-studio`, **ask the person whether they want sound effects added** (unless they already specified):

1. **Strategic editorial SFX (Recommended):** restrained, tactile cues on key visual transitions, structural reveals, discrete steps/counters, curve morphs, and the closing lockup (`4–10` cues in a 30 s piece, mixed `10–16 dB` below narration).
2. **Launch-film SFX + kit:** fuller rhythmic punctuation across scene cuts, UI pops, typing runs, whooshes, and tonal lockups.
3. **Narration / music only:** no sound effects.

Never add dense, cartoon-like sound effects everywhere: **restraint is what makes sound design feel expensive.**

---

## Step 2: choosing and rendering sounds (`earshot sfx` & `earshot kit`)

The shipped `earshot` bank has **252 sounds** across procedural recipes (`forge_v2.json`), music-led launch sounds (`forge04.json`), CC0-fitted real recordings (`fit.json`), and tuned kalimba plucks (`pluck.json`). It needs **no model weights** and renders in milliseconds.

```bash
. ~/.local/share/cutroom/env.sh && earshot sfx list                       # all 252 sounds with duration, attack, centroid, pitch
. ~/.local/share/cutroom/env.sh && earshot sfx list --role pop            # filter by film role (pop, tick, click, tock, land.light, whoosh.short, swell, hit, bell, key, sting...)
. ~/.local/share/cutroom/env.sh && earshot sfx list ui_pop knock fit      # filter by category
```

### Strategic sound palette for motion & math videos

| Visual moment | Recommended `earshot` sounds | Alignment (`align`) | Typical `gain_db` under voice |
|---|---|---|---|
| **Soft element / card / badge appearing** | `ui_pop/soft`, `ui_pop/step`, `pro_pop_in/round`, `fit/land.light/fingertip_book` | `onset` | `-13` to `-16` |
| **Discrete step, counter tick, axis tick, grid cell** | `fit/tick/domino`, `tap/knuckle`, `knock/wood`, `knock/plastic`, `hover_tick/mid` | `onset` | `-15` to `-18` |
| **3D extrusion, block landing, prism snapping** | `knock/desk`, `cut_hit/sub`, `fit/hit/bamboo_tok`, `pro_tap/soft` | `onset` | `-12` to `-15` |
| **Curve trace, coordinate morph, camera glide, wipe** | `fit/whoosh.short/bamboo_swish`, `swipe/velvet`, `swish/soft`, `whoosh_fast/crisp` | `peak` | `-14` to `-17` |
| **Scene cut or chapter transition** | `cut_hit/kick`, `whoosh_big/thump_airy`, `reverse_swell/short` (max 1 per film) | `onset` (`hit`) / `peak` (`swell`) | `-11` to `-14` |
| **Typing prompt, code line, CLI command** | `fit/key/thock`, `fit/key.space/thock_space`, `typing_key/thock`, `pro_typing_run/soft` | `onset` | `-15` to `-18` |
| **Key formula, theorem reveal, insight highlight** | `pluck/kalimba_soft`, `mallet/celesta`, `mallet/marimba`, `notify/m0` | `onset` | `-12` to `-15` |
| **Closing brand / logo lockup** | `pluck/kalimba_ring` (tuned via `pitch`), `pro_logo_sting/taps_tone`, `shimmer/m0` | `onset` | `-10` to `-13` |

### Rendering individual takes or a coherent kit

```bash
# Render one sound, retuned or timed through its recipe knobs (never post-hoc time-stretched):
. ~/.local/share/cutroom/env.sh && earshot sfx render pluck/kalimba_soft -o "$J/work/sfx/reveal.wav" \
  --pitch E5 --dur 0.65 --peak-db -6 --json

# Or level it automatically 6 dB above a music bed of known LUFS:
. ~/.local/share/cutroom/env.sh && earshot sfx render ui_pop/soft -o "$J/work/sfx/pop.wav" \
  --bed-db 6 --bed-lufs -20

# Or scaffold and render a whole film kit (consistent tuning and family across the piece):
. ~/.local/share/cutroom/env.sh && earshot kit init "$J/src/kit.json" --template launch
. ~/.local/share/cutroom/env.sh && earshot kit render "$J/src/kit.json" -o "$J/work/kit"
. ~/.local/share/cutroom/env.sh && earshot kit check "$J/work/kit"
```

---

## Step 3: sample-accurate cue mixing (`src/cues.json` + `cutroom edit sfx`)

Never guess where a sound's peak is. A whoosh starts softly and peaks `80–250 ms` into the file; a hit attacks in `2–15 ms`. `cutroom edit sfx` reads `$J/src/cues.json`, renders each `earshot` sound, reads its exact measured `onset_s`, `peak_s`, or `end_s`, aligns that anchor to the visual beat timestamp, mixes the stereo stem at 48 kHz, and muxes it into the video without re-encoding the video stream (`-c:v copy`).

### Format of `$J/src/cues.json`

```json
{
  "cues": [
    {"time": 0.45, "sound": "ui_pop/soft", "align": "onset", "gain_db": -14, "note": "eyebrow badge enters"},
    {"time": 1.80, "sound": "fit/whoosh.short/bamboo_swish", "align": "peak", "gain_db": -15, "note": "secant line sweeps toward P"},
    {"time": 3.20, "sound": "fit/tick/domino", "align": "onset", "seed": 0, "gain_db": -16, "note": "h = 2.0 step"},
    {"time": 4.10, "sound": "fit/tick/domino", "align": "onset", "seed": 1, "gain_db": -16, "note": "h = 1.0 step"},
    {"time": 5.00, "sound": "fit/tick/domino", "align": "onset", "seed": 2, "gain_db": -15, "note": "h = 0.5 step"},
    {"time": 6.40, "sound": "pluck/kalimba_soft", "align": "onset", "pitch": "E5", "gain_db": -12, "note": "tangent lockup f'(2) = 2"}
  ]
}
```

### Cue fields

- `time` (seconds or `"M:SS.ms"`): exact visual beat timestamp from the HyperFrames timeline (`data-start` + GSAP offset) or ManimGX scene clock.
- `sound`: any `earshot sfx list` ID **or** a path to a `.wav` file.
- `align`:
  - `"onset"` (default for hits, pops, knocks, ticks, keys, plucks): places the sound's `onset_s` at `time`.
  - `"peak"` (default for `whoosh_*`, `swish`, `swipe`, `reverse_swell`, `pro_zip`): places the sound's loudest moment (`peak_s`) right on the visual cut or motion midpoint.
  - `"end"` (default for `riser`, `pro_riser`, `pro_glitch`): ends the build right on the cut.
- `gain_db`: level relative to `-6 dBFS` peak (default `-12.0`). Under narration (`-16 LUFS`), use `-12` to `-18` so effects stay tactile and never compete with the voice.
- `seed`: integer offset (`0, 1, 2...`) so repeated cues (e.g. a sequence of steps or ticks) render distinct micro-variations and never comb-filter.
- `pitch` (`"C5"`, `"E5"`, `440`), `dur` (seconds), `apex` (seconds), `pan` (`-1.0` left to `+1.0` right).

### Generating the cues from the scene (recommended for ManimGX)

Placing 100+ cues by hand drifts. Have the scene log the time of every sentence and beat (`kit.EventLog` in
`harness/cutroom_mathkit.py` writes `work/events.json`), then generate `cues.json` from those times plus each animation's
known offsets with a small script: see `examples/math-gradient-descent/src/make_cues.py` (a soft pop per sentence, a tick per
zoom doubling, a knock per hop, a swish per camera move, a note per arrival; 80 to 120 cues in 50 s, 12 to 22 dB under the voice).

### Mixing onto a video or audio track

```bash
. ~/.local/share/cutroom/env.sh && cutroom edit sfx "$J/work/draft.mp4" \
  --cues "$J/src/cues.json" \
  --stem "$J/work/sfx-stem.wav" \
  -o "$J/out/video.mp4"
```

If you are building a **HyperFrames** composition (`cutroom-motion`), you can either:
1. Render the stereo stem first (`cutroom edit sfx "$J/work/narration.wav" --cues "$J/src/cues.json" --stem "$J/src/intro/assets/sfx.wav" --stem-only -o "$J/src/intro/assets/sfx.wav"`) and include `<audio src="assets/sfx.wav" data-start="0"></audio>` in `index.html`, **or**
2. Render the HyperFrames video with narration first and run `cutroom edit sfx` on the rendered `.mp4`.

---

## Step 4: listening to and critiquing existing videos (`earshot` ears)

An agent cannot hear raw `.mp4` or `.wav` bytes directly. `earshot` turns audio into measurements, contact sheets, and sync/mix critiques so you can **see and verify** how a video sounds.

### 1. Fast acoustic & loudness measurement (no models needed)

```bash
. ~/.local/share/cutroom/env.sh && earshot measure "$J/out/video.mp4"
```
Reports integrated loudness (`LUFS`), true peak (`dBTP`), onset/peak/end times, attack time (`ms`), spectral centroid (`Hz`), and 7-band energy balance (`sub`, `low`, `low_mid`, `mid`, `high_mid`, `presence`, `air`).

### 2. Visual + audio contact sheet (`earshot sheet`) — **always inspect this!**

```bash
. ~/.local/share/cutroom/env.sh && earshot sheet "$J/out/video.mp4" \
  --cues "$J/src/cues.json" \
  -o "$J/work/sound-sheet.png"
```
`earshot sheet` renders a single high-resolution PNG combining:
- Video thumbnails at key moments and cue timestamps;
- Waveform + RMS envelope with cue markers overlaid;
- Mel spectrogram (showing voice formants vs SFX transients and sub energy).

**Always open `$J/work/sound-sheet.png` with your image-reading tool (`Read` / `read_file`)** to visually confirm that every cue transient lines up with the intended video frame and that there are no unexpected dead silences or clipped peaks.

### 3. Timeline sync & mix critique (`earshot timeline` & `earshot critique`)

Requires the local listening models (`earshot doctor --fetch` once):

```bash
# Verify that every cue in cues.json is audible and lands within tolerance of its visual beat:
. ~/.local/share/cutroom/env.sh && earshot timeline "$J/out/video.mp4" --cues "$J/src/cues.json"

# Full sound-design critique (sync drift, masking over speech, spectral mud, repetition/comb warnings):
. ~/.local/share/cutroom/env.sh && earshot critique "$J/out/video.mp4" --cues "$J/src/cues.json"
```

### 4. Listening to unknown audio or reference videos (`describe`, `match`, `find`, `rank`, `ab`, `realness`)

When the person gives you an existing video or audio file and asks *"how does this sound?"*, *"what effects does this video use?"*, or *"pick the best take"*:

```bash
# Extract audio if needed, then describe events over time + acoustic character:
. ~/.local/share/cutroom/env.sh && earshot describe reference.mp4

# Score how well a take matches a text description (CLAP cosine similarity):
. ~/.local/share/cutroom/env.sh && earshot match take.wav "soft wooden knock on a desk"

# Rank candidate takes against a prompt (and penalize synth/artificial artifacts):
. ~/.local/share/cutroom/env.sh && earshot rank "$J/work/candidates/"*.wav --prompt "crisp mechanical keyboard thock"

# Check whether a synthesized sound feels acoustic/real vs 8-bit/chirpy:
. ~/.local/share/cutroom/env.sh && earshot realness take.wav

# Compare two mixes or takes side by side:
. ~/.local/share/cutroom/env.sh && earshot ab before.mp4 after.mp4
```

---

## Step 5: creating new sounds (`earshot forge` & `earshot fit`)

When none of the 252 bank sounds fit a specialized mechanism:

1. **Synthesize in Python (`earshot forge`):** follow `~/.local/share/cutroom/upstream/earshot/skills/real-sound/SKILL.md` and run `earshot forge` to evolve and audit procedural DSP recipes against a target description.
2. **Fit a real CC0 recording (`earshot fit`):** decompose a real recording into a deterministic parametric recipe (`earshot fit recording.wav -o "$J/work/model.json"`) that renders clean takes at any seed or pitch.
