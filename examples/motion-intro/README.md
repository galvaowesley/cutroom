# Example: cutroom product intro (cutroom-motion / HyperFrames 0.8.183 + Kokoro)

**Request:** "30 s HyperFrames video with narration presenting cutroom: what it makes, the 5 coding agents supported, 14 media skills, brand adaptation and local voice cloning, offline/pinned execution, and how to get started."

[`out/intro.mp4`](out/intro.mp4) (30.0 s, 1920x1080 @ 30.0 fps, H.264 + AAC stereo, 1.91 MB) · source in [`src/intro/`](src/intro) · narration in [`src/intro/assets/narration.m4a`](src/intro/assets/narration.m4a) (28.5 s)

| File | Description |
|---|---|
| [`out/intro.mp4`](out/intro.mp4) | Deliverable: 30.0 s product video with synchronized voiceover (1.91 MB) |
| [`src/SCRIPT.md`](src/SCRIPT.md) | Structured production script with 6 scenes and verified facts F1–F3 (2.7 KB) |
| [`src/speech.txt`](src/speech.txt) | Raw narration text across 6 paragraph blocks (455 bytes) |
| [`src/pronounce.json`](src/pronounce.json) | Phonetic dictionary for English synthesis: `"Kiro": "Kee-ro"` (23 bytes) |
| [`src/intro/index.html`](src/intro/index.html) | HyperFrames HTML composition using GSAP timelines (14.2 KB) |
| [`src/intro/hyperframes.json`](src/intro/hyperframes.json) | HyperFrames project configuration (318 bytes) |
| [`src/intro/package.json`](src/intro/package.json) | Node package definition (294 bytes) |
| [`src/intro/meta.json`](src/intro/meta.json) | Composition metadata (81 bytes) |
| [`src/intro/assets/narration.m4a`](src/intro/assets/narration.m4a) | Synthesized voiceover track (28.5 s, AAC mono, -16.3 LUFS, 575 KB) |
| [`src/intro/assets/brand/`](src/intro/assets/brand) | Local copy of brand tokens.css, fonts.css, SVG icons, logos, and TTF font files |

## Script and verified facts

Every number and claim in the video is drawn directly from repository code and configuration:

- **F1 (Supported agents):** 5 coding agents supported by `install.py` and `cutroom crew`: Claude Code, Codex, Antigravity, Gemini CLI, and Kiro.
- **F2 (Skill library):** 14 built-in media skills in the `skills/` directory (`cutroom-init`, `cutroom-studio`, `cutroom-script`, `cutroom-extract`, `cutroom-deck`, `cutroom-diagram`, `cutroom-iso3d`, `cutroom-math`, `cutroom-motion`, `cutroom-voice`, `cutroom-edit`, `cutroom-graphic`, `cutroom-brand`, `cutroom-logo`).
- **F3 (Cloning languages):** 23 languages supported locally by Chatterbox voice cloning in `cutroom_voice.py`.

| Scene | Time | Speech | Visuals |
|---|---|---|---|
| 1. Title | 0:00–0:04 | "cutroom. Media for coding agents, made on your machine." | Hot pink background (`#FF2D6F`); cutroom logo cuts in; tagline types out in Night Plum |
| 2. Agents | 0:04–0:09 | "It works in Claude Code, Codex, Antigravity, Gemini and Kiro." | Night Plum background (`#16072B`); 5 agent chips enter; Sunflower horizontal sweep line |
| 3. Range | 0:09–0:17 | "Decks, diagrams, figures, math videos, motion, voice, graphics and edits. Fourteen skills, one folder per piece." | Blush Paper background (`#FFF7FA`); 4-column grid displaying brand icons and skill titles |
| 4. Brand & Voice | 0:17–0:22 | "Bring your brand, or build one. Your voice too: with consent, it clones locally." | Night Plum background; 3 palette swatches animate across card; audio waveform bars oscillate |
| 5. Offline | 0:22–0:27 | "Nothing leaves the machine, and every version is pinned. Agents can even work in parallel." | Blush Paper background; three stacked rows ("Local", "Pinned", "Parallel") highlight sequentially |
| 6. Call to action | 0:27–0:31 | "Start with install dot py. Then, cutroom init." | Terminal prompt typing `python3 install.py → /cutroom-init`; endplate logo on Hot Signal |

## Pronunciation dictionary

Kokoro's US English voice model mispronounces "Kiro" without phonetic guidance. [`src/pronounce.json`](src/pronounce.json) provides the substitution:

| Written | Pronounced |
|---|---|
| `Kiro` | `Kee-ro` |

## Commands

```bash
. ~/.local/share/cutroom/env.sh

# 1. Validate script facts
cutroom script check src/SCRIPT.md

# 2. Synthesize English voiceover with Kokoro
tts -f src/speech.txt -o src/intro/assets/narration.m4a --voice af_heart --speed 0.95 --pronounce src/pronounce.json

# 3. Check and render video composition with HyperFrames
cd src/intro
hyperframes lint
hyperframes check
hyperframes render --quality delivery --output ../../out/intro.mp4

# 4. Probe output
cutroom edit probe ../../out/intro.mp4
```

## What to verify

- `cutroom edit probe out/intro.mp4` verified properties:
  - Duration: 30.00 s
  - Resolution: 1920×1080
  - Frame rate: 30.0 fps
  - Video codec: H.264
  - Audio codec: AAC stereo (2 channels), 48,000 Hz
  - Loudness: -17.3 LUFS
- Narration audio file probe: [`src/intro/assets/narration.m4a`](src/intro/assets/narration.m4a) has duration 28.5 s, AAC mono, loudness -16.3 LUFS.
- `hyperframes lint` passed with 0 errors and 0 warnings.
- `hyperframes check` passed with WCAG AA compliance on all scenes.

## How to open

```bash
# macOS
open out/intro.mp4

# Linux
xdg-open out/intro.mp4
```

## Brand applied

- **Palette transitions:** solid background cuts between Hot Signal `#FF2D6F`, Night Plum `#16072B`, and Blush Paper `#FFF7FA`.
- **Typography:** Bricolage Grotesque (700 and 600 weight) for display typography, eyebrows, and agent chips; Inter for body copy; JetBrains Mono NL for terminal command.
- **Logos & Icons:** SVG brand icons embedded directly from `assets/brand/icons/` into the scene 3 grid; official cutroom wordmark cuts in without partial opacity fades.
- **Motion:** custom GSAP easing curves (`power2.out`, `expo.out`) with short translations and clean cut transitions.

## Limits

- GSAP 3.14.2 is loaded via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js`); font files, CSS tokens, and logos are bundled locally in `src/intro/assets/brand/` for offline rendering.
- Scene cuts are timed to word cues in the narration audio; altering narration speed requires adjusting timeline offsets in `index.html`.
