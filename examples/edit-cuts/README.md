# Example: post-production recipes and cuts (cutroom-edit / ffmpeg)

**Request:** "Demonstrate post-production editing recipes on existing video and audio assets: synthesize a music bed with ffmpeg aevalsrc, score video with ducking, normalize loudness, reframe to 9:16 with blur fill, burn subtitles, generate square audiogram, compress for email, make an animated GIF, and generate contact sheets."

<p align="center"><img src="out/intro.gif" width="720" alt="Animated GIF preview of the final scored intro video"></p>

[`out/intro-final.mp4`](out/intro-final.mp4) (30.0 s, 1080p, -13.9 LUFS, 1.7 MB) · [`out/derivative-9x16-captions.mp4`](out/derivative-9x16-captions.mp4) (29.93 s, 1080x1920 vertical, 1.4 MB) · [`out/intro-audiogram.mp4`](out/intro-audiogram.mp4) (30.0 s, 1080x1080, 7.3 MB) · [`out/intro-email.mp4`](out/intro-email.mp4) (30.0 s, 540p, 431 KB) · source in [`src/bed.m4a`](src/bed.m4a)

| File | Description |
|---|---|
| [`src/bed.m4a`](src/bed.m4a) | Synthesized music bed generated with `ffmpeg aevalsrc` (32.12 s, AAC stereo, -30.6 LUFS, 339 KB) |
| [`out/intro-final.mp4`](out/intro-final.mp4) | Scored product intro with music bed ducked under narration, normalized to -13.9 LUFS (30.0 s, 1.7 MB) |
| [`out/intro-email.mp4`](out/intro-email.mp4) | Compressed 960×540 email preset deliverable under 500 KB (30.0 s, 431 KB) |
| [`out/derivative-9x16-captions.mp4`](out/derivative-9x16-captions.mp4) | 9:16 vertical reframe of math video with blur padding and burned brand captions (29.93 s, 1.4 MB) |
| [`out/intro-audiogram.mp4`](out/intro-audiogram.mp4) | 1:1 square audiogram with animated waveform in Sunflower yellow on Night Plum (30.0 s, 7.3 MB) |
| [`out/intro.gif`](out/intro.gif) | 720 px animated preview GIF at 12 fps (649 KB) |
| [`out/intro-sheet.png`](out/intro-sheet.png) | 4×3 contact sheet of intro-final.mp4 with brand monospace timestamps (114 KB) |
| [`out/derivative-9x16-sheet.png`](out/derivative-9x16-sheet.png) | 4×3 contact sheet of derivative-9x16-captions.mp4 showing subtitle placement (220 KB) |

## Workflows and recipes

All operations use the `cutroom edit` tool wrappers around standard `ffmpeg` filters:

1. **Music Bed Synthesis (`ffmpeg aevalsrc`):**
   Synthesizes a 32.12 s ambient audio bed locally without external dependencies:
   ```bash
   ffmpeg -f lavfi -i "aevalsrc=sin(2*PI*220*t)*0.05+sin(2*PI*440*t)*0.02:s=48000:d=32.12" \
     -c:a aac -b:a 128k src/bed.m4a
   ```

2. **Scoring with Ducking (`cutroom edit score`):**
   Combines the video from `examples/motion-intro` with `src/bed.m4a`. The music automatically ducks in volume whenever speech occurs:
   ```bash
   cutroom edit score ../motion-intro/out/intro.mp4 --music src/bed.m4a --duck -o work/intro-scored.mp4
   ```

3. **Loudness Normalization (`cutroom edit loudnorm`):**
   Normalizes the mixed video audio to the -14 LUFS target for online video and social delivery:
   ```bash
   cutroom edit loudnorm work/intro-scored.mp4 -o out/intro-final.mp4 --target -14
   ```

4. **Web / Email Compression (`cutroom edit compress`):**
   Re-encodes video to under 1 MB at 960×540 for lightweight sharing or email attachments:
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
     -o out/intro-audiogram.mp4 --title "cutroom in 30 seconds" --aspect 1:1
   ```

8. **Preview GIF (`cutroom edit gif`):**
   Generates a 720 px animated GIF preview:
   ```bash
   cutroom edit gif out/intro-final.mp4 -o out/intro.gif --start 0 --duration 6 --fps 12 --width 720
   ```

9. **Contact Sheets (`cutroom edit sheet`):**
   Outputs visual proof grids with timestamp markers:
   ```bash
   cutroom edit sheet out/intro-final.mp4 -o out/intro-sheet.png
   cutroom edit sheet out/derivative-9x16-captions.mp4 -o out/derivative-9x16-sheet.png
   ```

## What to verify

- `cutroom edit probe` verified file properties:
  - `out/intro-final.mp4`: duration 30.0 s, 1920×1080, 30.0 fps, loudness -13.9 LUFS (target was -14 LUFS).
  - `out/intro-email.mp4`: duration 30.0 s, 960×540, 30.0 fps, size 431 KB (well below 1 MB email limit).
  - `out/derivative-9x16-captions.mp4`: duration 29.93 s, 1080×1920, 19.01 fps, loudness -22.1 LUFS.
  - `out/intro-audiogram.mp4`: duration 30.0 s, 1080×1080, 30.0 fps, size 7.63 MB.
  - `src/bed.m4a`: duration 32.12 s, AAC 48,000 Hz stereo, loudness -30.6 LUFS.
- Subtitle placement: [`out/derivative-9x16-sheet.png`](out/derivative-9x16-sheet.png) confirms captions render within the lower third and do not collide with formulas.
- Audio ducking audit: music drops during voice sections and rises during scene transition pauses.

## How to open

```bash
# macOS
open out/intro-final.mp4
open out/derivative-9x16-captions.mp4
open out/intro-audiogram.mp4

# Linux
xdg-open out/intro-final.mp4
```

## Brand applied

- **Burned captions:** Inter font in white `#FFFFFF` over semi-translucent Night Plum `#16072B` pill container.
- **Audiogram:** Night Plum `#16072B` solid background, Sunflower `#FFC43D` waveform amplitude bars, Bricolage Grotesque title text.
- **Contact sheets:** frame timestamps styled in JetBrains Mono NL.

## Limits

- Gaussian blur reframe maintains centered content, but elements plotted at the extreme edges of 16:9 may require manual scale adjustment.
- Email compression achieves its 431 KB size by downscaling resolution to 960×540 and applying higher quantization.
