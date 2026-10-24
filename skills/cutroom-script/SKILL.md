---
name: cutroom-script
description: "Turns a request and the person's sources into a standard script, src/SCRIPT.md, that the other cutroom skills consume: brief (audience, goal, format, duration, voice, brand), a facts table with source and period, the key message in one sentence, the arc of the format, and scenes or slides with what goes on screen, the speech, the visual and the facts of each, plus pronunciation. `cutroom script` checks it (fact without source, number without fact, superlatives, long titles, speech that does not fit the scene) and exports the narration text and pronunciation. Use when asked for a deck, explainer, product or release video, narration, podcast or post-mortem from documents, data or PRs, before producing with cutroom-deck, cutroom-math, cutroom-motion, cutroom-voice or cutroom-graphic, or to review the tone and numbers of a script. Usage: cutroom-script <request>"
metadata:
  version: "2.0.0"
---

# cutroom-script: from request to standard script

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`). References in
`references/`, in this skill's folder.

`src/SCRIPT.md` is the single source of the piece: message, order, numbers and speech come from it, and production
skills only execute. It is the script the conventions require before any video, narration or deck.

## Step 0: nothing to install

`cutroom script` needs only `python3`. Run `cutroom job "<short title>"` and keep the path as `$J`, or use the
existing piece folder. Long sources go through `cutroom-extract` (component `extract`, ~2.3 GB); if it is missing,
offer `cutroom-init extract`, or read the document directly and warn that tables and scanned pages may be lost.

## Step 1: brief

Take what the request gives. Ask only what is missing, with options, all at once:

- **Audience:** executive or technical. It changes vocabulary, number of metrics and depth (`references/tone.md`).
- **Goal:** what the viewer decides or understands at the end, with a verb ("decides whether to adopt").
- **Format:** PDF deck, explainer video, product or release video, narration or podcast, social cut. Post-mortem is
  an arc: also ask the medium.
- **Target duration:** if not given, propose the arc's typical one (`references/arcs.md`).
- **Sources:** documents, sheets, queries, PRs, repository, the person's text. No source, no number.
- **Brand:** the active one (`cutroom brand list`) or the one requested. Read its `VOICE.md`: it shapes the speech.
- **Voice**, for video and narration: the default (`voice list`) unless another is asked (`cutroom-voice`).
- **Sound effects (`cutroom-sound`):** for motion and math videos, ask whether the person wants strategic `earshot` sound effects added (`Strategic editorial SFX`, `Launch-film SFX`, or `Narration only`) and note the key SFX cues in `$J/src/cues.json` or in each scene's **Sync** line.
- **Language:** `cutroom config language` unless the request says otherwise.

## Step 2: facts

1. Long document, PDF with tables or scanned: run `cutroom-extract` first and read the Markdown in `$J/src/extract/`.
   Docling's JSON has the page of each passage, for citing.
2. Every number and claim the piece will use becomes a row of the facts table (`F1`, `F2`...), with value, source
   (document and page, query saved in `$J/src/`, PR) and period. Sums go in unrounded.
3. Separate fact from hypothesis. Hypotheses go to `## Hypotheses` and appear in the piece as hypotheses. If a number
   is missing, ask, or mark it as illustrative in the source column and in the piece.

## Step 3: key message

One factual sentence, with the number when there is one: what the person should remember if they remember one
thing. It goes in the brief, opens the piece (summary or hook) and closes it. If it does not fit one sentence, it is
two pieces.

## Step 4: arc

Choose the format's arc in `references/arcs.md`. The concept comes before the evidence that depends on it. Count the
messages, one per scene or slide, against what the arc holds in the target duration. If they do not fit, change the
duration or cut messages before writing scenes.

## Step 5: scenes or slides

Write `$J/src/SCRIPT.md` in the format of `references/format.md` (its example is a good start).

- **On screen:** the title with the scene's message, factual, with the number, up to 2 lines.
- **Speech:** spoken language, following `references/tone.md` and the brand's `VOICE.md`, with animation cues in
  `[brackets]`.
- **Visual:** the producing skill and the part (`cutroom-math: scene`, `cutroom-deck: ill.queue_scenarios`,
  `cutroom-graphic: thumbnail`), plus a description.
- **Facts:** the ids the scene uses.
- In video, each scene's window (`0:00–0:08`) comes from the speech rate, about 2.6 words per second.
- Names and acronyms the voice reads badly go to the `## Pronunciation` table.

## Step 6: review

1. Run until there are no errors:

   ```bash
   . ~/.local/share/cutroom/env.sh && cutroom script check "$J/src/SCRIPT.md" && cutroom script timing "$J/src/SCRIPT.md"
   ```

   `check` exits 1 on errors. Resolve each warning, or tell the person why it stays (silence on purpose during an
   animation, a number that is an index and not a fact). For other speeds or a measured rate, pass `--wpm`.
2. Review the tone with the checklist at the end of `references/tone.md`: `check` does not catch everything.
3. Show the script and wait for the ok when the piece is longer than ~30 s or leaves the team. Short pieces for the
   person's own team can go straight on.

## Step 7: hand-off to production

| Format | Skill | What it uses from `SCRIPT.md` |
|---|---|---|
| deck | `cutroom-deck` | one scene per slide of `src/deck.py`: the first and last become `deck.cover` and `deck.closing`, the rest `deck.slide`. **On screen** is the title, **Visual** `cutroom-deck: ill.<name>` names the illustration, **Facts** give `source=` |
| math, algorithm or code video | `cutroom-math` | each **Speech** becomes a `self.say(...)` with the same cues; **Sync** says which animation enters on each. Pronunciation goes to `manimgx_voice(pronounce=...)` |
| product, release, PR or summary video | `cutroom-motion`, `cutroom-voice`, `cutroom-edit` | the brief becomes `BRIEF.md`; each scene a frame of `STORYBOARD.md` (`scene`, `duration`, `voiceover` without brackets); Sync goes to the cue sheet |
| narration or podcast | `cutroom-voice`, `cutroom-edit` | the speech text and pronunciation JSON from `cutroom script speech` (below) |
| posts, thumbnail, poster of the piece | `cutroom-graphic` | the key message and the facts it shows |
| figure of a scene or slide | `cutroom-diagram`, `cutroom-iso3d` | the scene whose **Visual** names the skill |
| piece mixing several | `cutroom-studio` | the whole script, "script and facts first" in its Step 3 |

Narration, in any format:

```bash
cutroom script speech "$J/src/SCRIPT.md" -o "$J/src/speech.txt" --pronounce "$J/src/pronounce.json"
```

`speech.txt` has one paragraph per scene, in normal spelling and without brackets. Pronunciation changes stay in
the JSON, which `tts --pronounce` applies to the audio only. The command also prints the brief's voice.

When done, say where `SCRIPT.md` is, the `check` result (with the remaining warnings and why) and which skill comes
next.
