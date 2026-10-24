---
name: cutroom-voice
description: "Local narration and voice-over from text or a script, in many languages, with voices that are easy to specify: saved profiles (`narrator`), Kokoro presets (`af_heart`, `pf_dora`), speed (`af_heart@1.1`), blends that design a new voice without cloning (`af_heart*0.6+bf_emma*0.4`), and local voice cloning from 10 to 20 s of audio with the speaker's recorded consent (Chatterbox, 23 languages, watermarked). Auditions candidate voices side by side, applies a pronunciation dictionary to the audio only, and delivers WAV, MP3 or M4A for video (ManimGX, HyperFrames), decks, podcasts and audiograms. Use when asked for narration, voice-over, text to speech, reading a text aloud, an audiobook or podcast, choosing or designing a voice, a brand voice, or cloning a voice. Usage: cutroom-voice <text | file | SCRIPT.md> [voice=<spec>] [speed=1.0] [lang=en] | clone <name> <audio> | audition [lang]"
metadata:
  version: "2.0.0"
---

# cutroom-voice: local narration, profiles and cloning

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md` (Privacy covers cloning).

`tts` speaks, `voice` manages voices (both in `~/.local/share/cutroom/bin`, after `. ~/.local/share/cutroom/env.sh`).
`tts --help` and `voice --help` list every option.

| Engine | Component | Size | For |
|---|---|---|---|
| Kokoro-82M (default) | `voice` | ~740 MB (environment shared with `math`) | presets in 8 languages, blends, fast on CPU |
| Chatterbox Multilingual | `voice-clone` | ~4.5 GB | cloning a consenting speaker's voice, 23 languages, expressiveness control |

## Step 0: component

Run `cutroom doctor --json`. Kokoro needs `voice`; cloning needs `voice-clone` too. If missing, give the size and
offer `cutroom-init <component>`. Do not suggest cloning when a preset or blend does the job.

## Step 1: the voice, in one spec

Everywhere a voice is asked (`tts --voice`, the `Voice` row of SCRIPT.md, `manimgx_voice(...)`), one string:

| Spec | Means |
|---|---|
| `narrator` | a saved profile (`voice list`) |
| `af_heart` | a Kokoro preset; the first letter is the language: `a` US English, `b` UK English, `p` Brazilian Portuguese, `e` Spanish, `f` French, `i` Italian, `h` Hindi, `j` Japanese, `z` Mandarin |
| `af_heart@1.1` | the same, at speed 1.1 (0.9 dense content, 1.0 normal, 1.1 short calls to action) |
| `af_heart*0.6+bf_emma*0.4` | a blend of presets: a new voice, no cloning (weights are normalized) |
| `clone:ana` | a cloned profile (Chatterbox) |
| nothing / `default` | `voice default` → the brand's `narration` for the language → the language default (`af_heart` en, `pf_dora` pt-BR) |

Choosing with the person:

1. **Audition:** `voice audition --lang <lang> -o "$J/work/audition"` writes one sample per preset of the language
   (`voice presets --lang <lang>` lists them with notes). For a specific set: `--voices af_heart,am_michael,bf_emma`.
   Share the files and let the person choose by ear; do not pick on description alone.
2. **Design (optional):** blend the two they liked: `voice test "af_heart*0.7+am_michael*0.3" -o "$J/work/mix.wav"`.
3. **Save:** `voice add narrator af_heart@0.95 --lang en-us --note "explainers" --default` (add
   `--pronounce pronounce.json` to carry a dictionary). From now on `narrator` (or no voice at all) is that voice.
   For a brand, put the profile name in the brand's `narration` (`brand.json`) per language.

## Step 1b: cloning (only with consent)

A cloned voice is someone's identity. Clone only when:

- the speaker is the person asking, or gave explicit consent for this use (ask how: written, recorded, contract);
- it is not a public figure, a minor, or anyone who has not agreed; the result is never presented as a real
  recording of the person.

Then:

1. Reference: 10 to 20 s of clean speech by the speaker alone (no music, no room echo, one sentence or two), any
   format. Ask for its transcript.
2. `voice clone ana --ref "$J/src/ana.m4a" --speaker "Ana Souza" --consent "recorded consent, 2026-10-23, internal
   training videos" --ref-text "<transcript>" --lang pt [--exaggeration 0.5] [--default]`. The reference (24 kHz mono,
   up to 30 s) and the consent record stay in `~/.local/share/cutroom/voices/ana/`.
3. `voice test ana` and listen. `--exaggeration` (0.25 calm … 0.7 expressive) and `--cfg` (0.3 slower and steadier …
   0.6) are the controls; re-run `voice clone` with new values to change them.
4. Chatterbox adds an inaudible Perth watermark to every output. It runs on CPU by default (about 15 s to load the
   model, then roughly 4 to 5 s per second of speech on a recent laptop) or on CUDA when present;
   `CUTROOM_CLONE_DEVICE=mps` tries Apple's GPU, which was slower in our tests. Run long texts as a long command.
5. `voice remove ana` deletes the profile and the reference audio when the person asks or consent ends.

## Step 2: text

1. Run `cutroom job "<title>"` (or use the piece folder) and keep it as `$J`.
2. From a script: `cutroom script speech "$J/src/SCRIPT.md" -o "$J/src/speech.txt" --pronounce "$J/src/pronounce.json"`.
   Otherwise write `$J/src/speech.txt` in spoken language:
   - spell out ambiguous numbers and acronyms ("$1.2M" → "one point two million dollars");
   - short sentences, one idea each; punctuation is pause;
   - over ~1 minute: one file per block (`block-01.txt`...) so only the changed part is redone. Kokoro processes up
     to 510 phonemes per batch (about 25 to 30 s: the 28.4 s intro narration is 499); above that it splits by
     itself and the intonation changes at the seam. Cut at the end of a sentence yourself.
3. Long scripts or pieces leaving the team: confirm the text before generating.

## Step 3: generate

```bash
. ~/.local/share/cutroom/env.sh && tts -f "$J/src/speech.txt" -o "$J/out/narration.mp3" --voice narrator --pronounce "$J/src/pronounce.json"
```

- Output by extension: `.wav` (for editing and video), `.mp3`, `.m4a`. The command prints duration and the resolved
  voice: check it is the one you meant.
- Where: narration that is the delivery goes to `$J/out/`; narration for a video goes to `$J/work/` and the video's
  skill copies it where it needs (in HyperFrames, `src/<slug>/assets/`).
- **Pronunciation:** names, versions and acronyms read badly get a `{"written": "spoken"}` entry, which changes the
  audio only. Check a word before: `voice test narrator "ManimGX 0.1.1"`. For Kokoro, phonemes:
  `cutroom-python -c 'from kokoro_onnx.tokenizer import Tokenizer; print(Tokenizer().phonemize("text", "en-us"))'`.
  Write each respelling for the language the voice speaks and check it with that language's phonemes (`"pt-br"` for
  `pf_dora` and `pm_alex`, not `"en-us"`): an English-style respelling such as "esquíls" for "skills" sounds right to
  the English phonemizer and wrong in Portuguese, where "iskíus" gives the Brazilian reading. A preset voice always
  speaks its own language (the first letter of its name); only `--lang` overrides it. Foreign names and English
  terms inside a Portuguese text are where a Brazilian ear hears a foreign accent first: respell them, then listen.
- **Word times for the picture:** Kokoro gives none. Measure each sentence (`cutroom edit silences`, or the energy
  envelope), place the sentences on the timeline with natural pauses (0.45 to 0.85 s), and spread the words of a
  sentence between its measured silences in proportion to their phoneme counts (phonemes of the voice's own language).
  `harness/cutroom_timing.py` does this (`build(sentences, work_dir, voice=..., pronounce=...)` or the command line),
  and a composition built from its `timing.json` (`examples/motion-intro-vertical`) cannot drift from the voice.
- **Cue points** to time scenes: `cutroom edit silences "$J/work/narration.wav"` lists the pauses.
- **Finishing:** loudness for podcasts and voice-over `cutroom edit loudnorm in.wav -o out.m4a --target -16`; music
  under the voice with ducking `cutroom edit mix --voice narration.wav --music bed.mp3 --duck -o mix.m4a`; a
  shareable clip `cutroom edit audiogram mix.m4a -o clip.mp4 --title "..." --aspect 9:16`.

## Step 4: verify and deliver

- Check the duration and listen, or ask the person to listen to, the first seconds and every name. A wrong reading:
  add it to the pronunciation file and regenerate only that block.
- Deliver `$J/out/*` with the speech text and pronunciation in `$J/src`, and the voice spec used (so it can be
  reproduced).

## Inside other skills

- **ManimGX** (`cutroom-math`): `from cutroom_voice import manimgx_voice` and `voice = manimgx_voice("narrator",
  pronounce={...})` in the scene. The `manimgx` shortcut already has the module on `PYTHONPATH`. Cloned voices work
  too (they run in their own environment, called per line and cached by ManimGX).
- **HyperFrames** (`cutroom-motion`): generate the WAV here and use it as `<audio>`. `env.sh` also points
  `HYPERFRAMES_PYTHON` at the Kokoro environment so `hyperframes tts` works locally.
- **Python**: `cutroom-python -c "from cutroom_voice import synth; open('x.wav','wb').write(synth('Hello', voice='narrator'))"`.
