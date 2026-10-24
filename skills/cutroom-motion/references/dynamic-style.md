# Dynamic style for motion videos (HyperFrames)

The style of `examples/motion-intro` (English) and `examples/motion-intro-pt` (pt-BR): a piece that is never still, whose picture follows the voice
word by word. The reusable parts are `harness/cutroom_motionkit.js` (animation) and `harness/cutroom_timing.py`
(narration times). This page says when to use each pattern. It is a catalogue: add new patterns at the end of
each table (section 5 says how).

## 1. Principles

1. **Never still.** Something moves in every frame: a sliding grid, a scrolling feed, a slow push on the whole stage.
   The voice pauses (it must: a natural pause is 0.45 to 0.85 s, 0.75 s after a name); the picture does not.
2. **Each spoken thing is a gesture at its word.** The icon ring bursts on "fifteen skills", the card takes focus
   on "slides", the camera flies to each agent as it is named, the text is typed while the link is spoken.
3. **Times come from the audio.** Synthesize the narration, measure it, derive every time from it (section 2).
   Never type a time that depends on the voice: change a word, rebuild, and picture, cues and captions follow.
4. **Scenes overlap and a transition covers the join.** The next scene starts 0.4 to 0.6 s before its first word,
   already moving. Hard cuts and fades are not used; entries are masks, slides, zooms.
5. **The last frame stays alive for 3 to 3.5 s** after the last word, with a slow push, a sheen, anything that
   moves slowly. A frozen frame reads as the video having ended too early.
6. **Seek-safe.** A render may jump to any time: state is a function of time (`at(t)`) or a paused GSAP tween; never
   read layout or path geometry inside a callback (sample it once at build time: `K.pathTable`).

## 2. Workflow

```
speech.txt (one sentence per paragraph) + pronounce.json (respelled for the voice's language)
   -> cutroom_timing.build(...)   work/narr_raw.wav + work/timing.json   (word times, natural pauses, hold)
   -> build.py                    fills intro.template.html with times ({{r2}}, TM.A, TM.ag...) -> index.html
   -> make_cues.py                sound cues at the same times -> cutroom edit sfx --stem-only -> assets/sfx.wav
   -> hyperframes lint, snapshot at the transitions, render, compress (libx264 -crf 25 keeps 1080 x 1920)
```

- Anchors: name them in `build.py` from words, e.g. `W(5, 2)` = start of word 2 of sentence 5. Card focus times closer than
  0.6 s are pushed apart (a card needs that long to take focus); everything else is `anchor ± offset`.
- Natural pauses: `pauses={1: 0.75}` after a name, 0.45 to 0.85 s between sentences. Do not squeeze them.
- Pronunciation is per language: `voice phonemes <voice> "word"` shows how the voice's own phonemizer reads it.
  Respell for that language (see `cutroom-voice`).
- Root `data-duration` = last word + hold; clip windows come from the same numbers.

## 3. Pattern catalogue (`CutroomMotion`, harness/cutroom_motionkit.js)

| Pattern | Call | Use it when | Notes |
|---|---|---|---|
| Words from a mask | `K.words(tl, sel, times)` | headlines and taglines spoken word by word | markup `.ln > .w > i`; `.w` inline-block, overflow hidden |
| Typing | `K.typed(el, cursor, text, t0, t1, cursorUntil)` | a prompt, a command, a URL, while it is spoken | time function |
| Counter | `K.counter(el, to, t0, dur)` | a number that is said ("fifteen", "twenty-three") | ends as the word ends |
| Icon ring + zoom-through | `K.ring(items, {start, zoomStart})` | naming a set of things; also the exit of the scene | items centred on the container; fades while rushing past |
| Focus feed | `K.feed(feed, cards, A, {extra})` | a list of capabilities read one by one | scrolls to card i at A[i], drifts in between; focused card full size |
| Camera on a stage | `K.camera(el, keys, {w, h, base})` | a grid or map where each item is named | keys `{t, cx, cy, s}`; chains and clamps; `base` = slow push between keys |
| Circle mask | `K.circleIn(tl, sel, at, {x, y, r})` | a change of mood or colour, the end card | origin where the eye is |
| Whip pan | `K.whipIn` + `K.whipOut` | the next block of the same kind (list to grid) | blur 30 px snapping sharp in 0.8 s |
| Vertical push | `K.pushIn` + `K.pushOut` | the next step of a sequence | old scene goes up and away |
| Path table | `K.pathTable(sel)`, `K.pointAt(T, u)` | a pulse or tangent moving along an SVG path | measure once, read in `at(t)` |
| One clock | `K.clock(tl, DUR, [at, ...])` | always, for the time functions | single tween with onUpdate |

Transition guide: dark to light or to the brand end card -> circle; same kind of content -> whip; next step -> push;
leaving a scene that has a ring -> zoom-through (the ring's own exit) with the circle opening under it.
Camera: one move per beat (a focus at the word, then the next), never a shake; zoom 1.4 to 1.6 on a card, back to the
full grid at the end of the list.

## 4. Checklist before rendering

- Every spoken noun or number has a gesture within 0.2 s of its word (check the snapshot at that time).
- No beat longer than ~1.5 s with nothing moving (grid drift counts, but a feed or a push is better).
- A scene's first word is 0.4 to 0.6 s after the transition starts; the transition itself shows content, not an empty frame.
- Cards or names closer than 0.6 s are spaced; text never sits under a moving card.
- Last frame: voice end + hold (3 to 3.5 s), still moving slowly.
- Snapshots at every transition midpoint and at the last frame; `hyperframes lint` has 0 errors.
- Sound cues generated from the same times; `earshot sheet --cues` shows most cues within 100 ms.

## 5. Adding a pattern

1. Build it in a composition first, as a tween (`tl.fromTo(...)`) or a time function `at(t)`.
2. When a second piece needs it, move it into `harness/cutroom_motionkit.js` with the same shape: a tween helper takes `(tl, sel, at, options)`;
   a time function takes its elements and options and returns `at(t)`. Defaults reproduce the original look.
3. Refactor the original composition onto the kit and check the render is identical (`ffmpeg -i old.mp4 -i new.mp4 -lavfi psnr -f null -`
   says `inf` for identical frames).
4. Add a row to the table above (what, call, when, notes) and, if it needs a markup contract, say it in the notes.
5. Copy the kit to `~/.local/share/cutroom/harness/` (`python3 install.py` does it for everyone).

Ideas not built yet (write them when a piece needs them): split-screen wipe between two scenes, shared-element morph
(a card that becomes the next scene's header), parallax layers on the backdrop, number ticker with digits rolling,
spotlight that follows the spoken word, camera dolly through a stack of cards.
