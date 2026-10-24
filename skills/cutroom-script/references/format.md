# `src/SCRIPT.md` format

One file per piece, in `$J/src/SCRIPT.md`. People read it (the script is approved from it) and `cutroom script`
reads it (`check`, `speech`, `timing`), so the structure is fixed: the sections and fields below, with these names.
Anything else (a `## Notes` section, `## Hypotheses`, loose paragraphs) is free and skipped by the check.
Portuguese names from earlier versions (`## Fatos`, `## Cenas`, `## Pronúncia`, `Objetivo`, `Na tela`, `Fala`,
`Sincronia`) are accepted too.

Order: `# title`, brief table, `## Facts`, `## Scenes`, `## Pronunciation`.

## Complete example

A 40 s explainer video. `cutroom script check` passes with no errors and no warnings.

```markdown
# Why narration goes in blocks

| Field | Value |
|---|---|
| Format | explainer video |
| Audience | technical |
| Goal | whoever writes scripts for Kokoro understands why to split long speech and where to cut |
| Key message | Kokoro reads up to 510 phonemes per batch: above that, cut it yourself, at the end of a sentence. |
| Target duration | 40 s |
| Voice | narrator |
| Brand | cutroom |

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | phonemes Kokoro processes per batch | 510 phonemes | skills/cutroom-voice/SKILL.md, Step 2 | Kokoro v1.0 |
| F2 | speech that fits one batch | ~25 s | skills/cutroom-voice/SKILL.md, Step 2 | Kokoro v1.0 |
| F3 | phonemes of the intro video narration | 499 phonemes | examples/voice-narration/README.md | narration v1 |
| F4 | length of that narration | 28.42 s | examples/voice-narration/README.md | narration v1 |

## Scenes

### 1. Hook · 0:00–0:06

- **Goal:** show the symptom: the voice changes tone mid-text.
- **On screen:** Why does the voice change tone mid-text?
- **Speech:** A long narration can [change its intonation] halfway through. There is a simple reason.
- **Visual:** cutroom-motion: title on deep; a waveform with a step in the middle.
- **Facts:** —
- **Sync:** [change its intonation] lights the step in the waveform.

### 2. Problem · 0:06–0:13

- **Goal:** give Kokoro's limit.
- **On screen:** 510 phonemes per batch, about 25 s of speech
- **Speech:** Kokoro reads up to five hundred and ten phonemes at once, about twenty five seconds of speech.
- **Visual:** cutroom-motion: a phoneme ruler with the 510 mark.
- **Facts:** F1, F2

### 3. Concept · 0:13–0:18

- **Goal:** explain the seam.
- **On screen:** Above 510 phonemes, the text splits by itself
- **Speech:** Above that, it splits the text by itself, and the intonation changes at the seam.
- **Visual:** cutroom-motion: the text breaks into two blocks, the seam in the accent color.
- **Facts:** F1

### 4. Demonstration · 0:18–0:28

- **Goal:** show a real script that fits one batch.
- **On screen:** 499 phonemes: one batch, 28.4 s without a seam
- **Speech:** The intro video's script has [four hundred and ninety-nine phonemes]. It fits [in one batch], and its
  twenty-eight second narration has no seam.
- **Visual:** cutroom-motion: the ruler fills to 499, with the 510 mark ahead.
- **Facts:** F3, F4
- **Sync:** [four hundred and ninety-nine phonemes] fills the ruler; [in one batch] lights the room left before 510.

### 5. Result · 0:28–0:34

- **Goal:** show where to cut.
- **On screen:** Cut at the end of a sentence: the seam lands on a pause
- **Speech:** Cut at the end of a sentence, and the seam lands on a pause that was already there.
- **Visual:** cutroom-motion: the script splits at a full stop into `block-01.txt` and `block-02.txt`.
- **Facts:** —

### 6. Close · 0:34–0:40

- **Goal:** leave the rule to use today.
- **On screen:** One file per block, up to 510 phonemes each
- **Speech:** One block per file, up to five hundred and ten phonemes. Redo only what changes.
- **Visual:** cutroom-motion: end card on primary with the two files and the white logo.
- **Facts:** F1

## Pronunciation

| written | spoken |
|---|---|
| Kokoro | Ko-KO-ro |
```

## Header and brief

The first line is `# title`, short; it also names the piece folder (`cutroom job`). Below it, a two-column table
(the header `| Field | Value |` is free) with these rows:

| Field | What goes there | Example |
|---|---|---|
| Format | medium and arc | `deck`, `explainer video`, `product video`, `release video`, `social cut`, `narration`, `podcast`, `post-mortem (deck)`, `post-mortem (video)` |
| Audience | `executive` or `technical`, with the group if useful | `executive (leadership)` |
| Goal | what the person decides or understands at the end, with a verb | `decides whether to adopt fuzzy search in sign-up` |
| Key message | one factual sentence, with the number when there is one | — |
| Target duration | speech or video time; for a deck that is read, the number of slides or `—` | `40 s`, `1:30`, `60 to 70 s`, `15 min`, `12 slides` |
| Voice | a voice spec (`cutroom-voice`): profile, preset, blend, `clone:name`; `—` for silent decks | `narrator`, `af_heart@0.95`, `clone:ana` |
| Brand | visual identity | `cutroom`, `paper`, the client's brand |
| Language | if different from the default | `pt-BR` |

`cutroom script` decides from the Format whether speech is required: `video`, `narration`, `podcast` or `audio` need
speech in every scene; `deck`, `slides`, `presentation` or `PDF` make it optional. Post-mortem is an arc, not a
medium: write the medium in parentheses, or speech is not required and `check` warns.

## Facts

Table with header `| id | fact | value | source | period |`, one row per number or claim the piece uses.

| Column | What goes there |
|---|---|
| id | `F1`, `F2`... Scenes cite by this id. |
| fact | what the number is, in a few words. |
| value | the number as the piece uses it, with its unit (`22.42 s`, `0.0944`, `$1.2M`, `8 × 8`). `check` reads numbers from here. Add before rounding: the value is the unrounded total. |
| source | where to check: document and page (`report.pdf, p. 4`), query saved in `src/` (`src/queries/churn.sql`), PR (`#123`), file and section. Illustrative number: `illustrative: <how it was computed>`, and the piece says it is illustrative. No source is an error. |
| period | data window, version or measurement date (`Jun–Sep 2026`, `Kokoro v1.0`); `—` when not applicable. |

A number on screen or in speech matches a fact when it is the value rounded to the decimals shown, directly or as a
percentage: `0.0944` covers `9.4%` and `9%`; `22.42 s` covers `22 s`. Years, dates, times, versions (`0.27.2`),
numbers stuck to letters (`F1`, `MP3`, `4K`), code in backticks and "scene 3"/"slide 3" are skipped. Spelled-out
numbers ("five hundred and ten") are not checked: put the same number in digits on screen, as in the example.

## Scenes

Each scene (or slide) is `### N. Name · window`, in order:

- **window:** `0:00–0:08` for video and narration (`m:ss`, optional tenths `0:03.5`; `-` and `to` work too), or
  `slide N` for decks. Video without a window gets a warning.
- Fields come as a list, bold name followed by a colon (`- **On screen:** ...`). Continue a field on the next line by
  indenting two spaces. Fields with other names (`**Notes:**`) are skipped by the check.

| Field | What goes there | Required | `—` allowed? |
|---|---|---|---|
| **Goal:** | what this scene makes the audience understand, in one sentence | always | no |
| **On screen:** | the title with the scene's message: one factual sentence with the number, up to 2 lines (~110 characters). In a code or formula scene with no title, the main text people read. Smaller labels go in Visual. | always | in video and narration; not on slides |
| **Speech:** | what the voice says, in spoken language (`references/tone.md`). `[brackets]` mark animation cues; an empty `[]` at the start delays the first animation to the start of the speech (`cutroom-math`). In a deck, the presenter's words. (`Voiceover:` also works.) | in video and narration | in video (silent scene) and decks |
| **Visual:** | `skill: part` plus a description: `cutroom-deck: ill.queue_scenarios`, `cutroom-math: scene`, `cutroom-motion: compositions/s2.html`, `cutroom-diagram: architecture`, `cutroom-iso3d: drawers`, `cutroom-graphic: thumbnail` | always | yes (narration) |
| **Facts:** | ids from the table the scene uses: `F1, F3` | no | yes |
| **Sync:** | each `[cue]` of the speech and what it triggers: `[derivative] draws the tangent` | no | — |

For a deck, header and speech look like this:

```markdown
### 2. Summary · slide 2

- **Goal:** give the verdict and the three numbers before any detail.
- **On screen:** A 499-phoneme script fits one batch; above 510, cut at the end of a sentence
- **Speech:** —
- **Visual:** cutroom-deck: verdict box, three numbers and three highlights.
- **Facts:** F1, F3, F4
```

## Pronunciation

Table `| written | spoken |`, one replacement per row. It applies to whole words, case-insensitive, in table
order, and changes only the audio: captions and screen keep the written form. Backticks around cells are ignored.
With no replacements, keep only the header.

`cutroom script speech SCRIPT.md -o speech.txt --pronounce pronounce.json` writes the `{"written": "spoken"}` JSON
that `tts --pronounce` and `manimgx_voice(pronounce=...)` use.

## What `cutroom script check` checks

| Type | Rule |
|---|---|
| error | scene without **Goal:**, **On screen:** or **Visual:**; slide with `—` on screen |
| error | scene without **Speech:** when the Format is video or narration; narration with a silent scene (`—`) |
| error | **Facts:** cites an id not in the table; fact without a source; repeated id |
| error | no scenes |
| warning | number on screen or in speech matching no fact's value |
| warning | **On screen:** longer than ~110 characters (2 lines at 32 px) |
| warning | superlative or alarm word on screen, in speech or in the key message (English: very, extremely, huge, incredible, amazing, revolutionary, game-changing, the best/biggest, drastic, dramatic, critical, alarming, shocking, massive, powerful, unprecedented; and the Portuguese equivalents) |
| warning | estimated speech longer than the scene window by more than 20% (does not fit), or filling less than half of it (silence; animation after the speech is common) |
| warning | total duration off the Target duration by more than 15% |
| warning | Sync cue not in brackets in the speech; unreadable window; brief without Format, Audience, Goal, Key message or (video and narration) Target duration |

Estimated speech is words ÷ 155 × 60 (words as written; change the rate with `--wpm`). The total duration is the
larger of the end of the last window and the sum of speech: speech that does not fit stretches the piece. Warnings
do not change the exit code. Resolve each, or tell the person why it stays.
