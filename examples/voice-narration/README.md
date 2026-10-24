# Example: local narration, voice profiles and cloning (cutroom-voice / Kokoro + Chatterbox)

**Request:** "Demonstrate local voice synthesis with Kokoro and Chatterbox: English and pt-BR narrations using saved profiles, a custom Kokoro blend, and a voice clone with recorded consent of a synthetic reference voice."

[`out/intro-en.mp3`](out/intro-en.mp3) (28.42 s, 234 KB) · [`out/intro-pt-br.mp3`](out/intro-pt-br.mp3) (29.78 s, 233 KB) · [`out/blend-host.mp3`](out/blend-host.mp3) (1.88 s, 13 KB) · [`out/clone-pt-br.mp3`](out/clone-pt-br.mp3) (5.38 s, 42 KB) · source in [`src/`](src)

| File | Description |
|---|---|
| [`out/intro-en.mp3`](out/intro-en.mp3) | English narration synthesized with profile `narrator` (`af_heart@0.95`, 28.42 s, 234 KB) |
| [`out/intro-pt-br.mp3`](out/intro-pt-br.mp3) | Brazilian Portuguese narration synthesized with profile `narrador` (`pf_dora@1.0`, 29.78 s, 233 KB) |
| [`out/blend-host.mp3`](out/blend-host.mp3) | Voice blend sample combining Kokoro presets (`af_heart*0.6+bf_emma*0.4`, 1.88 s, 13 KB) |
| [`out/clone-pt-br.mp3`](out/clone-pt-br.mp3) | Cloned voice synthesis via Chatterbox from synthetic reference (`clone:george-synth`, 5.38 s, 42 KB) |
| [`src/speech-en.txt`](src/speech-en.txt) | English narration script across 6 paragraphs (455 bytes) |
| [`src/speech-pt.txt`](src/speech-pt.txt) | Portuguese narration script across 6 paragraphs (509 bytes) |
| [`src/pronounce-en.json`](src/pronounce-en.json) | English pronunciation substitutions (23 bytes) |
| [`src/pronounce-pt.json`](src/pronounce-pt.json) | Portuguese pronunciation substitutions for technical and agent terms (143 bytes) |
| [`src/clone-profile.json`](src/clone-profile.json) | Chatterbox voice clone metadata and consent record (404 bytes) |
| [`src/clone-reference-synthetic.mp3`](src/clone-reference-synthetic.mp3) | Reference speech audio generated locally from Kokoro preset `bm_george` (9.56 s, 75 KB) |

## Narration modes and profiles

1. **English Narration (`out/intro-en.mp3`):**
   - Profile: `narrator` (`af_heart@0.95`, Kokoro US English).
   - Speed: 0.95 for clear pacing in explainer videos.
   - Text source: [`src/speech-en.txt`](src/speech-en.txt).
   - Pronunciation: [`src/pronounce-en.json`](src/pronounce-en.json) (`"Kiro": "Kee-ro"`).

2. **Portuguese Narration (`out/intro-pt-br.mp3`):**
   - Profile: `narrador` (`pf_dora@1.0`, Kokoro Brazilian Portuguese).
   - Text source: [`src/speech-pt.txt`](src/speech-pt.txt).
   - Pronunciation: [`src/pronounce-pt.json`](src/pronounce-pt.json) applies phoneme corrections:
     - `cutroom` → `cât rum`
     - `Kiro` → `Káiro`
     - `Codex` → `Códex`
     - `Claude Code` → `Clód Côud`
     - `Antigravity` → `Antigráviti`
     - `Gemini` → `Jêmini`
     - `skills` → `isquíls`
     - `init` → `ínit`

3. **Kokoro Voice Blend (`out/blend-host.mp3`):**
   - Synthesizes a new voice by interpolating latent vectors between multiple Kokoro presets (e.g. `af_heart*0.6+bf_emma*0.4`).
   - Requires no reference audio and executes instantly on CPU.

4. **Chatterbox Voice Clone (`out/clone-pt-br.mp3`):**
   - Spoken text: *"Toda peça de mídia começa por um roteiro. Primeiro os fatos, depois as cenas."*
   - Engine: Chatterbox Multilingual (23 languages supported).
   - Profile: `george-synth`.
   - Settings: `lang: pt`, `speed: 1.0`, `exaggeration: 0.5`, `cfg_weight: 0.5`.
   - **Consent and privacy compliance:**
     - Cloned from a 9.56 s synthetic reference audio ([`src/clone-reference-synthetic.mp3`](src/clone-reference-synthetic.mp3)) generated locally using Kokoro preset `bm_george`.
     - Stored consent record in [`src/clone-profile.json`](src/clone-profile.json):
       - Speaker: `"Kokoro preset bm_george (synthetic voice, no real person)"`
       - Statement: `"synthetic reference generated locally for the cutroom example; no human speaker"`
       - Recorded: `"2026-10-23"`

## Commands

```bash
. ~/.local/share/cutroom/env.sh

# 1. English narration with profile 'narrator'
tts -f src/speech-en.txt -o out/intro-en.mp3 --voice narrator --speed 0.95 --pronounce src/pronounce-en.json

# 2. Portuguese narration with profile 'narrador'
tts -f src/speech-pt.txt -o out/intro-pt-br.mp3 --voice narrador --speed 1.0 --pronounce src/pronounce-pt.json

# 3. Blended Kokoro voice test
voice test "af_heart*0.6+bf_emma*0.4" "cutroom. Media for coding agents." -o out/blend-host.mp3

# 4. Voice clone registration and synthesis (Chatterbox)
voice clone george-synth \
  --ref src/clone-reference-synthetic.mp3 \
  --speaker "Kokoro preset bm_george (synthetic voice, no real person)" \
  --consent "synthetic reference generated locally for the cutroom example; no human speaker" \
  --lang pt

tts "Toda peça de mídia começa por um roteiro. Primeiro os fatos, depois as cenas." \
  -o out/clone-pt-br.mp3 --voice clone:george-synth --lang pt
```

## What to verify

- `cutroom edit probe` verified properties:
  - `out/intro-en.mp3`: duration 28.42 s, MP3 mono, 24,000 Hz, loudness -22.3 LUFS.
  - `out/intro-pt-br.mp3`: duration 29.78 s, MP3 mono, 24,000 Hz, loudness -23.4 LUFS.
  - `out/blend-host.mp3`: duration 1.88 s, MP3 mono, 24,000 Hz, loudness -21.7 LUFS.
  - `out/clone-pt-br.mp3`: duration 5.38 s, MP3 mono, 24,000 Hz, loudness -20.9 LUFS.
  - `src/clone-reference-synthetic.mp3`: duration 9.56 s, MP3 mono, 24,000 Hz, loudness -21.3 LUFS.
- Pronunciation dictionaries: technical terms in English and Portuguese verify against acoustic playback without misreadings or dropped phonemes.
- Privacy compliance: consent statement is stored directly in `~/.local/share/cutroom/voices/george-synth/voice.json` and mirrored in `src/clone-profile.json`.

## How to open

```bash
# macOS
open out/intro-en.mp3
open out/clone-pt-br.mp3

# Linux
xdg-open out/intro-en.mp3
```

## Brand applied

- Default brand voices configured in `brand.json`:
  - English default: `af_heart`
  - Portuguese default: `pf_dora`
- Audio loudness across all rendered voice deliverables falls into the target voiceover range (-20 to -24 LUFS).

## Limits

- Kokoro generates audio at a native 24,000 Hz sample rate. For 48 kHz video deliverables, video production pipelines (`cutroom edit` or `hyperframes`) resample the track automatically.
- Chatterbox local voice cloning requires ~4.5 GB model weights and takes ~10–20 s on CPU for a 5-second sentence.
