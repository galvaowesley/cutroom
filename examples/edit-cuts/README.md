# Example: post-production recipes and cuts (cutroom-edit / ffmpeg)

**Request:** "Demonstrate post-production editing recipes on existing video and audio assets: synthesize a music bed with ffmpeg aevalsrc, score video with ducking over narration and earshot SFX, normalize loudness, reframe to 9:16 with blur fill, burn subtitles, generate square audiogram, compress for email, make an animated GIF, and generate contact sheets."

<p align="center">
  <a href="out/intro-final.mp4"><img src="out/intro.gif" width="300" alt="Watch intro-final.mp4 with narration, earshot SFX, and ducked music bed"></a>
</p>
<p align="center">
  <a href="out/intro-final.mp4"><strong>▶ Watch &amp; listen: <code>out/intro-final.mp4</code> (34.1 s, 1080×1920, -14.1 LUFS)</strong></a> ·
  <a href="out/derivative-9x16-captions.mp4"><strong>▶ 9:16 Vertical + Captions (<code>out/derivative-9x16-captions.mp4</code>)</strong></a> ·
  <a href="out/intro-audiogram.mp4"><strong>▶ 1:1 Audiogram (<code>out/intro-audiogram.mp4</code>)</strong></a>
</p>

[`out/intro-final.mp4`](out/intro-final.mp4) (34.1 s, 1080×1920, -14.1 LUFS, 4.48 MB) · [`out/derivative-9x16-captions.mp4`](out/derivative-9x16-captions.mp4) (29.93 s, 1080x1920 vertical, 1.49 MB) · [`out/intro-audiogram.mp4`](out/intro-audiogram.mp4) (34.1 s, 1080x1080, 8.26 MB) · [`out/intro-email.mp4`](out/intro-email.mp4) (34.1 s, 304×540, 707 KB) · source in [`src/bed.m4a`](src/bed.m4a)

| File | Description |
|---|---|
| [`src/bed.m4a`](src/bed.m4a) | Synthesized music bed generated with `ffmpeg aevalsrc` (32.12 s, AAC stereo, -30.6 LUFS, 339 KB) |
| [`out/intro-final.mp4`](out/intro-final.mp4) | Scored product intro with music bed ducked under narration + `earshot` SFX, normalized to -14.1 LUFS (34.1 s, 4.48 MB) |
| [`out/intro-email.mp4`](out/intro-email.mp4) | Compressed 540 px email preset deliverable under 1 MB (34.1 s, 304×540, 707 KB) |
| [`out/derivative-9x16-captions.mp4`](out/derivative-9x16-captions.mp4) | 9:16 vertical reframe of math video with blur padding, `earshot` SFX, and burned brand captions (29.93 s, 1.49 MB) |
| [`out/intro-audiogram.mp4`](out/intro-audiogram.mp4) | 1:1 square audiogram with animated waveform in Sunflower yellow on Night Plum (34.1 s, 8.26 MB) |
| [`out/intro.gif`](out/intro.gif) | 300 px animated preview GIF of the first 12 s at 10 fps (2.0 MB) |
| [`out/intro-sheet.png`](out/intro-sheet.png) | 4×3 contact sheet of `intro-final.mp4` |
| [`out/derivative-9x16-sheet.png`](out/derivative-9x16-sheet.png) | 4×3 contact sheet of `derivative-9x16-captions.mp4` showing subtitle placement |

## Workflows and recipes

All operations use the `cutroom edit` tool wrappers around standard `ffmpeg` filters:

1. **Music Bed Synthesis (`ffmpeg aevalsrc`):**
   Synthesizes a 32.12 s ambient audio bed locally without external dependencies:
   ```bash
   ffmpeg -f lavfi -i "aevalsrc=sin(2*PI*220*t)*0.05+sin(2*PI*440*t)*0.02:s=48000:d=32.12" \
     -c:a aac -b:a 128k src/bed.m4a
   ```

2. **Scoring with Ducking (`cutroom edit score`):**
   Combines the English vertical intro (and its existing narration + `earshot` SFX audio track) from `examples/motion-intro` with `src/bed.m4a`. The music automatically ducks in volume whenever speech or accents occur:
   ```bash
   cutroom edit score ../motion-intro/out/intro.mp4 --music src/bed.m4a --duck -o work/intro-scored.mp4
   ```

3. **Loudness Normalization (`cutroom edit loudnorm`):**
   Normalizes the mixed video audio to the -14 LUFS target for online video and social delivery:
   ```bash
   cutroom edit loudnorm work/intro-scored.mp4 -o out/intro-final.mp4 --target -14
   ```

4. **Web / Email Compression (`cutroom edit compress`):**
   Re-encodes video to under 1 MB at 540 px tall for lightweight sharing or email attachments:
   ```bash
   cutroom edit compress out/intro-final.mp4 -o out/intro-email.mp4 --preset email
   ```

5. **Vertical Reframe (`cutroom edit reframe`):**
   Converts the 16:9 widescreen math explainer (`examples/math-derivative/out/derivative.mp4`) into 9:16 vertical (1080×1920) using Gaussian blurred copies of the video to fill top and bottom margins:
   ```bash
   cutroom edit reframe ../math-derivative/out/derivative.mp4 -o work/derivative-9x16.mp4 --aspect 9:16 --mode blur
   ```

6. **Burned Captions (`cutroom edit captions`):**
   Burns subtitles from `examples/math-derivative/out/derivative.srt` into the vertical video using brand typography:
   ```bash
   cutroom edit captions work/derivative-9x16.mp4 ../math-derivative/out/derivative.srt -o out/derivative-9x16-captions.mp4
   ```

7. **Square Audiogram (`cutroom edit audiogram`):**
   Generates a 1:1 social video (1080×1080) with dynamic audio waveform reactive to the speech track:
   ```bash
   cutroom edit audiogram ../motion-intro/src/intro/assets/narration.m4a \
     -o out/intro-audiogram.mp4 --title "cutroom in 34 seconds" --aspect 1:1
   ```

8. **Preview GIF (`cutroom edit gif`):**
   Generates an animated GIF preview of the first 12 seconds (300 px wide, 10 fps):
   ```bash
   cutroom edit gif out/intro-final.mp4 -o out/intro.gif --start 0 --duration 12 --fps 10 --width 300
   ```

9. **Contact Sheets (`cutroom edit sheet`):**
   Outputs visual proof grids:
   ```bash
   cutroom edit sheet out/intro-final.mp4 -o out/intro-sheet.png
   cutroom edit sheet out/derivative-9x16-captions.mp4 -o out/derivative-9x16-sheet.png
   ```

## What to verify

- `cutroom edit probe` verified file properties:
  - `out/intro-final.mp4`: duration 34.1 s, 1080×1920, 30.0 fps, loudness -14.1 LUFS (target was -14 LUFS).
  - `out/intro-email.mp4`: duration 34.1 s, 304×540, 30.0 fps, size 707 KB (below the 1 MB email limit).
  - `out/derivative-9x16-captions.mp4`: duration 29.93 s, 1080×1920, 19.01 fps, loudness -22.1 LUFS.
  - `out/intro-audiogram.mp4`: duration 34.1 s, 1080×1080, 30.0 fps, size 8.26 MB.
  - `src/bed.m4a`: duration 32.12 s, AAC 48,000 Hz stereo, loudness -30.6 LUFS.
- Subtitle placement: [`out/derivative-9x16-sheet.png`](out/derivative-9x16-sheet.png) confirms captions render within the lower third and do not collide with formulas.
- Audio ducking audit: music drops during voice sections and rises during scene transition pauses while preserving all 96 `earshot` cues.
