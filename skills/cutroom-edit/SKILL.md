---
name: cutroom-edit
description: "Post-production toolbox on ffmpeg, for any video, audio or image: trim, concatenate clips of different sizes, mix narration over music with automatic ducking, normalize loudness for podcasts and social, burn captions in the brand's font and colors, reframe to 9:16, 1:1 or 4:5 with blur fill, watermark with the brand logo, make GIFs, contact sheets and frames, compress for web, email or artifacts, turn stills into a Ken Burns slideshow, make audiograms, and find pauses in speech to time scenes. Every command prints the ffmpeg line it runs. Use when asked to cut, join, resize, crop, caption, add music, normalize audio, compress, convert, make a GIF or vertical version, or finish a video from cutroom-math or cutroom-motion. Usage: cutroom-edit <what to do> <files>"
metadata:
  version: "1.0.0"
---

# cutroom-edit: post-production on ffmpeg

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`). Everything is
`cutroom edit <recipe>`; `cutroom edit --help` lists every option, and `--dry-run` prints the ffmpeg command without
running it.

## Step 0: component

Run `cutroom doctor --json` and check `components.edit.installed` (needs ffmpeg, downloads nothing). If ffmpeg is
missing, show the `fix` from `cutroom doctor` (brew, apt or winget).

## Step 1: look before cutting

`cutroom edit probe <file>` gives duration, size, fps, codecs and loudness (LUFS). Work on copies: inputs stay in
`$J/src` or where the person keeps them; results go to `$J/work/` (intermediate) or `$J/out/` (delivery). Never
overwrite an input.

## Step 2: recipes

| Want | Recipe |
|---|---|
| a piece of a clip | `trim in.mp4 -o out.mp4 --start 0:03 --end 0:12` (re-encodes for exact cuts; `--copy` is instant but cuts on keyframes) |
| clips in a row | `concat a.mp4 b.mp4 c.mp4 -o all.mp4 [--size 1920x1080 --fps 30]` (different sizes are fitted and padded; silent clips get silence); audio files work too |
| narration over music | `mix --voice narration.wav --music bed.mp3 --duck -o mix.m4a [--music-db -20 --fade 1.5 --tail 1]` |
| narration and/or music under a video | `score video.mp4 --voice narration.wav --music bed.mp3 --duck -o out.mp4 [--offset 0.5]` |
| sample-accurate sound effects (`earshot`) | `sfx video.mp4 --cues src/cues.json -o out.mp4 [--stem work/sfx.wav --master-db 0]` (aligns each cue's measured `onset_s`, `peak_s` or `end_s` to the visual beat; see `cutroom-sound`) |
| loudness | `loudnorm in -o out --target -16` (podcast, voice-over, YouTube); `-14` for social video |
| burned captions | `captions video.mp4 subs.srt -o out.mp4 [--size 46 --position bottom]` (brand text font, white on a translucent deep box) |
| vertical or square | `reframe in.mp4 -o out.mp4 --aspect 9:16 [--mode blur\|crop\|pad]` (blur fills; crop keeps the center; pad uses `deep`) |
| logo on a video | `watermark in.mp4 -o out.mp4 [--on dark\|light] [--corner br] [--width 0.12]` (brand logo, full opacity, as the brand rules require) |
| GIF | `gif in.mp4 -o out.gif --start 2 --duration 6 [--fps 12 --width 720]` (safe with variable frame rate) |
| frames to look at | `frames in.mp4 -o folder --every 2` or `--at 1,5,10` |
| contact sheet | `sheet in.mp4 -o sheet.png [--cols 4 --rows 3]` (timestamps in the brand mono) |
| smaller file | `compress in.mp4 -o out.mp4 --preset web\|artifact\|email\|social [--max-mb 15]` |
| stills to video | `stills a.jpg b.jpg c.jpg -o slideshow.mp4 [--seconds 4 --zoom 1.08 --audio narration.wav]` |
| audio for social | `audiogram mix.m4a -o clip.mp4 --title "..." --aspect 9:16` (waveform in the brand accent on deep) |
| scene cut points from speech | `silences narration.wav [--json]` |
| audio track only | `extract-audio in.mp4 -o out.wav` |

Typical chains:

- **Narrated explainer:** render (math or motion) → `score` with music and `--duck` → `loudnorm --target -14` →
  `captions` → `reframe --aspect 9:16` for the vertical cut → `compress --preset social`.
- **Podcast from a script:** `tts` per block → `concat` the blocks → `mix` with intro music → `loudnorm --target -16`
  → `audiogram` for teasers.
- **Deliverable for an artifact:** `compress --preset artifact --max-mb 15`, and a `gif` preview.

## Step 3: check

- `probe` every output: duration as expected, resolution, audio present, loudness on target.
- **Look and listen:** `sheet` for the whole video, `frames --at` for the cut points, the first seconds of audio.
  Captions: check a frame with a long line (no overflow), and that names are spelled right in the `.srt`.
- Music: only files the person provided or licensed for the use.

## Step 4: deliver

List `$J/out/*` with duration, size and loudness, and the command chain used (it is printed by every recipe), so
the edit can be repeated on the next version.
