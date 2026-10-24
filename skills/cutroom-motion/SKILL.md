---
name: cutroom-motion
description: "Creates video and motion graphics from HTML, CSS and GSAP animations with HyperFrames: faceless explainers, product launch videos, PR videos, animated slides, titles, lower thirds, animated charts, captions, videos with music, in the active brand. Renders mp4, webm with transparency, mov, gif and PNG sequences deterministically in headless Chrome. Narration comes from local voices (cutroom-voice); music, ducking, captions and vertical cuts from cutroom-edit. Use when asked for a video, animation, motion graphic, intro, reel or vertical video, a video summary of a report or PR, or an animated GIF with web-page typography and layout. Usage: cutroom-motion <what the video shows> [duration=30s] [format=landscape|portrait|square]"
metadata:
  version: "2.0.0"
---

# cutroom-motion: video from HTML (HyperFrames 0.8.183)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom`. `S` = `~/.local/share/cutroom/upstream/hyperframes/skills`: the 21
official skills, at the CLI's version.

## Step 0: component

Run `cutroom doctor --json` and check `components.motion.installed`. If false, say `motion` downloads ~150 MB and needs
Node 22, Chrome and ffmpeg; offer `cutroom-init motion` and stop until it is installed. Narration also needs `voice`.

## Step 1: rules

1. Run `cutroom job "<title>"` and keep the path as `$J`.
2. Read `S/hyperframes/SKILL.md`, the official router, and follow its route table to the workflow skill
   (`/general-video`, `/faceless-explainer`, `/motion-graphics`, `/slideshow`, `/pr-to-video`...). Before writing HTML,
   read `S/hyperframes-core/SKILL.md`, the composition contract.

Translating the official skill to this environment:

| The official skill says | Do |
|---|---|
| `npx hyperframes <cmd>` or `npx hyperframes@<version> <cmd>` | `hyperframes <cmd>` after `. ~/.local/share/cutroom/env.sh` |
| load `/hyperframes-core`, `/media-use`, `/<workflow>`... | read `S/<name>/SKILL.md` and its references |
| `hyperframes skills update <workflow>`, `skills add`, `upgrade` | do not run: the skills are in `S/` at the pinned version |
| `npm run <script>` (the `init` package.json uses `npx --yes hyperframes@...`, which downloads from npm) | run the `hyperframes` shortcut directly |
| `hyperframes usage --json`, `auth status` | skip: they read the agent's or HeyGen's account and do not change the piece |
| `prefs.mjs record` (writes `~/.media/preferences.json`) | skip: preferences live in the piece's `BRIEF.md` |
| `snapshot --describe` | use `--describe false`: with `GEMINI_API_KEY` set it sends frames to Gemini |
| open the Studio (`preview`) and wait for approval before rendering | optional: show the snapshots and go on, unless the person wants to edit in the Studio |
| voice from HeyGen, ElevenLabs or another cloud | generate with `tts` (`cutroom-voice`) and use the file as `<audio>` |
| `hyperframes publish`, shareable link | not without the person asking: it publishes off the machine |
| present the desktop app (Framey) | only if the person asks |
| motion recipes with spring, bounce, scale pops or binary opacity entrances | the brand wins: its `motion.ease`, short fades and translates |

Route: a short narrated piece with no product URL goes to `/general-video` (the official table would also match
`/product-launch-video`, but that workflow expects a site to capture). A short, clear piece (intro, title, video up to
~30 s with the text given) does not need the full intent interview: record the choices in a short `BRIEF.md` and go
on. Long pieces or pieces leaving the team: do the interview and confirm the script. In HyperFrames, `BRIEF.md` plus
the workflow's `STORYBOARD.md` play the role of the conventions' `SCRIPT.md` (or derive them from it).

## Step 2: project

```bash
. ~/.local/share/cutroom/env.sh && cd "$J/src" && hyperframes init <slug> --non-interactive --resolution landscape
rm -f "$J/src/<slug>/CLAUDE.md" "$J/src/<slug>/AGENTS.md"  # they ask to run skills update, upgrade and publish
```

- `--resolution portrait` for vertical (Reels/Shorts/TikTok), `square` for feeds. There is no 720p preset: for
  1280 × 720, change `data-width`/`data-height` on the root of `index.html` (the render follows the composition).
- The composition is `$J/src/<slug>/index.html`. Follow the core contract: root with `data-composition-id`,
  `data-width` and `data-height`; clips with `class="clip"`, `data-start` and `data-duration`; one paused GSAP
  timeline registered in `window.__timelines[<id>]`. No clock, no unseeded random, no `play()`. Inside
  `compositions/`, file paths are `../assets/...`.
- **Brand**, applied in full (conventions, "Brand"): solid backgrounds (`deep`, `primary`, `background`), the display
  font for titles and the text font for body, the brand's easing, one accent highlight at a time, the logo on the end
  card when the piece speaks for the brand, entering by cut or mask, never by fade. Copy the brand assets into the
  project, so the render needs no outside file or network:

  ```bash
  B=$(cutroom brand show --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["paths"]["dir"])')
  P="$J/src/<slug>/assets/brand"; mkdir -p "$P" && cp "$B"/tokens.css "$B"/fonts.css "$P/" && cp -R "$B"/fonts "$B"/logos "$P/"
  ```

  - Link `assets/brand/tokens.css` and `assets/brand/fonts.css`. `fonts.css` declares local `@font-face` for every
    weight the brand ships (HyperFrames only embeds a few weights of common families; others would be synthetic).
  - Write `font-family` with the literal name (`'Inter Tight'`): the lint does not expand `var()`.
- **Dynamic style** (default for explainers, intros, product pieces; skip only if the person wants a static or
  minimal look): never still, scenes that overlap with a transition between them, one gesture per spoken
  word, last frame held 3 to 3.5 s. Read `references/dynamic-style.md` in this skill's folder. The pieces are
  `harness/cutroom_motionkit.js` (`cp ~/.local/share/cutroom/harness/cutroom_motionkit.js "$J/src/<slug>/assets/"`,
  then `<script src="assets/cutroom_motionkit.js">` after GSAP) and `harness/cutroom_timing.py` (sentence clips with
  natural pauses and word times, for any language). Worked example: `examples/motion-intro-vertical`.
- **Narration** (`cutroom-voice`): the audio the composition plays is a source of it, in `$J/src/<slug>/assets/`.
  Generate in `work/` and convert there:
  `tts -f "$J/src/speech.txt" -o "$J/work/narration.wav" --voice narrator && cutroom edit loudnorm "$J/work/narration.wav" -o "$J/src/<slug>/assets/narration.m4a" --target -16`.
  - Scene timing from the speech: `cutroom edit silences "$J/work/narration.wav"` lists the pauses. For a piece whose
    picture follows the voice, use `cutroom_timing.build(...)` instead: it places the sentences with natural pauses and
    gives the time of every word (`work/timing.json`), which the composition and the sound cues are built from.
  - Word-level captions: `hyperframes transcribe assets/narration.m4a --model small --language <lang>`. Without
    `--model` it uses `small.en`, which translates to English silently. The first run compiles whisper.cpp and
    downloads ~466 MB: warn first.
- **Sound effects (`cutroom-sound` / `earshot`):** always ask the person during planning whether they want strategic
  sound effects added (`cutroom-sound`, component `sound`). When chosen:
  - Write `$J/src/cues.json` mapping only strategic visual moments (scene cuts, key card/badge entrances, discrete
    counters/ticks, typing runs, curve sweeps, closing brand lockup — never every word or minor fade) to `earshot`
    bank sounds (`ui_pop/soft`, `fit/tick/domino`, `fit/whoosh.short/bamboo_swish`, `pluck/kalimba_soft`,
    `fit/key/thock`, `cut_hit/sub`, `notify/m0`...).
  - Either pre-render the stereo SFX stem into the composition (`cutroom edit sfx "$J/work/narration.wav" --cues "$J/src/cues.json" --stem "$J/src/<slug>/assets/sfx.wav" --stem-only -o "$J/src/<slug>/assets/sfx.wav"`) and add `<audio src="assets/sfx.wav" data-start="0"></audio>`, or mix onto the rendered video (`cutroom edit sfx "$J/out/<slug>.mp4" --cues "$J/src/cues.json" -o "$J/out/<slug>-sfx.mp4"`).
  - Verify the audio mix and cue alignment with `earshot measure "$J/out/<slug>.mp4"` and `earshot sheet "$J/out/<slug>.mp4" --cues "$J/src/cues.json" -o "$J/work/sound-sheet.png"` (open `sound-sheet.png` to inspect).
- **Music:** keep the composition's audio to the narration (and optional SFX stem) and add music after the render with ducking:
  `cutroom edit score "$J/out/<slug>.mp4" --music bed.mp3 --duck -o "$J/out/<slug>-music.mp4"`. Music must be
  licensed for the use; do not download music from the web without the person providing or approving it.

## Step 3: verify

- While writing, `hyperframes lint --json` until there are no errors.
- Final gate: `hyperframes check` (lint plus a browser run). `--snapshots` makes annotated frames.
- Frames to look at: `hyperframes snapshot --at 1,5,10 --describe false` writes PNGs to
  `.hyperframes/artifacts/snapshots/`. **Open the PNGs** before saying it is good.
- Draft: `hyperframes render --quality draft --output "$J/work/draft.mp4"`, then `cutroom edit sheet` for a contact
  sheet.
- "Screenshot capture (slower): BeginFrame did not run" is expected with the system Chrome: rendering is slower than
  with `chrome-headless-shell`, about real time.

## Step 4: final render and delivery

- Final: `hyperframes render --quality delivery --output "$J/out/<slug>.mp4"`. Long renders (> 2 min): the official
  detached mode (`HYPERFRAMES_RENDER_DETACHED=1`, log to a file) and follow the file.
- Cuts for other platforms: `cutroom edit reframe "$J/out/<slug>.mp4" -o "$J/out/<slug>-9x16.mp4" --aspect 9:16`
  (blur fill) or design a `portrait` composition when text must be reflowed. Covers and thumbnails: `cutroom-graphic`.
- GIF: `cutroom edit gif "$J/out/<slug>.mp4" -o "$J/out/<slug>.gif" --start 2 --duration 6 --width 720`.
- Transparency to overlay on another video: `--format webm` or `--format mov`.
- Deliver `$J/out/*` and the project in `$J/src/<slug>/`, which is editable and can be re-rendered.
