# Arcs by format

An arc is the order of the scenes or slides. Rules for all of them:

- **Concept before the evidence that depends on it.** If the result only makes sense to whoever knows the metric, the
  scene that defines the metric comes first.
- **One message per scene or slide**, written in **On screen:** as one factual sentence with the number.
- **The key message appears at the start** (summary or hook) **and returns at the close.**
- More messages than the arc holds become another piece, not faster scenes.

## Speech rate

`cutroom script` estimates speech at **155 words per minute**, pauses included (Kokoro at speed 1.0). That is about
2.6 words per second:

| Window | 5 s | 8 s | 10 s | 15 s | 20 s | 25 s | 30 s | 60 s |
|---|---|---|---|---|---|---|---|---|
| Words | 13 | 21 | 26 | 39 | 52 | 65 | 78 | 155 |

The real rate depends on the text: many names, acronyms and numbers bring it near 150 wpm; plain prose near 180 to
200. After generating the narration, measure it (`cutroom edit probe narration.wav`) and pass the measured rate with
`--wpm`. For another speed, multiply: at 0.9, use `--wpm 140`.

Kokoro reads up to 510 phonemes per batch, about 25 s of speech. A scene with more speech than that should be split
in two, or cut at the end of a sentence.

## Deck (16:9 PDF)

| # | Slide | What it carries |
|---|---|---|
| 1 | cover | the piece's name as title, the key message as subtitle (`deck.cover(eyebrow, title, subtitle, meta)`), audience and date or period in the meta |
| 2 | summary | the verdict in one sentence, three numbers and three highlights: the rest of the deck supports these three |
| 3 | how we measured / where the data comes from | sources, period, sample size, what was left out |
| 4 | one slide per concept, with an illustration | each term the evidence uses, explained by a figure (`cutroom-deck`, `cutroom-diagram`, `cutroom-iso3d`) |
| 5 | evidence | one per slide: the title states the result with the number, against the reference |
| 6 | why the result is what it is | the verified explanation; a hypothesis marked as one |
| 7 | verdict | strengths and limits, side by side |
| 8 | how to use it today | use for / don't use for |
| 9 | next steps | proposals with their adoption condition (`references/tone.md`) |
| 10 | close | the key message again, and where the data and material are |

- **Typical length:** 10 to 15 slides. Read as a PDF it has no speech (`Speech: —`). Presented, 1 to 2 min of speech
  per slide (155 to 310 words): the presenter's words go in **Speech:** and `cutroom script timing` adds them up.
- **Messages:** one per slide. For executives, stay near 10 slides with few concepts. Technical audiences take one
  slide per concept and per evidence, and the deck can pass 15.
- Each slide's source note comes from the facts cited in **Facts:** (source and period).

## Explainer video (45 to 90 s)

hook → problem → concept → demonstration → result → close

| Scene | What it does | Typical length | Words at 155 wpm |
|---|---|---|---|
| hook | a question or a concrete contrast | 4 to 8 s | 10 to 20 |
| problem | why it matters, with the number | 6 to 10 s | 15 to 26 |
| concept | the idea the demonstration uses | 8 to 15 s | 20 to 39 |
| demonstration | the concept working on a real case; may take several scenes | 15 to 30 s | 39 to 78 |
| result | the number or the effect, against a reference | 6 to 10 s | 15 to 26 |
| close | the key message and what to do with it | 5 to 8 s | 13 to 21 |

- **Messages:** 3 to 4 in total, one per content scene. A fifth one asks for another video.
- `examples/math-derivative` uses this arc: the hook is a car's speedometer, the concept is the secant turning into
  the tangent, and the demonstration computes the derivative of x² step by step.

## Product or release video (20 to 45 s)

what changed → for whom → how to use it → call to action

| Scene | What it does | Typical length | Words at 155 wpm |
|---|---|---|---|
| what changed | the change in one sentence, with the number if there is one (source: PR, changelog) | 4 to 8 s | 10 to 20 |
| for whom | who gains and in which situation | 4 to 8 s | 10 to 20 |
| how to use it | the minimal path: the command, the screen, the button | 8 to 20 s | 20 to 52 |
| call to action | the command or link, and the logo when the piece speaks for the brand | 4 to 6 s | 10 to 15 |

- **Messages:** two: what changed and how to use it. The rest goes to the documentation.
- `examples/motion-intro` (cutroom's own intro) uses a variant: what it is, where it runs, what it makes, how it
  installs, what stays local, and the call to action.

## Social cut (15 to 60 s, vertical)

hook in the first 2 s → one idea → proof → call to action. Captions burned in (most people watch muted), text inside
the platform's safe area, the number on screen as early as possible. Usually a cut of a longer video
(`cutroom edit reframe`, `cutroom edit captions`), plus a cover (`cutroom-graphic`, `story`).

## Narration or podcast of a document (3 to 15 min)

opening → map → one block per section → recap → close

| Block | What it does | Typical length | Words at 155 wpm |
|---|---|---|---|
| opening | what the document is, for whom, and the key message | 15 to 25 s | 39 to 65 |
| map | the parts, in order | 10 to 20 s | 26 to 52 |
| sections | one block per section or idea, in the document's order (concept before evidence) | 20 to 25 s each | 52 to 65 |
| recap | three points | 15 to 25 s | 39 to 65 |
| close | where the document is | 5 to 10 s | 13 to 26 |

- **Messages:** one per block, 3 to 5 every 5 minutes.
- Each block is a scene with **On screen:** and **Visual:** as `—`. Tables and charts become one sentence with the
  number that matters: do not read the table.
- `cutroom script speech` writes one paragraph per scene. Above 1 minute, `cutroom-voice` wants one file per block.
- Finish with `cutroom edit loudnorm` (-16 LUFS) and, to share on social, `cutroom edit audiogram`.

## Post-mortem

what happened → measured impact → cause with evidence → what changes

| Part | What it carries |
|---|---|
| what happened | the factual timeline: start, detection, mitigation, end; no blame |
| measured impact | numbers with source and period (people, requests, time), against normal |
| cause with evidence | the cause and what supports it (log, PR, query). A hypothesis stays marked |
| what changes | what was decided (what and who) and the proposals, with their adoption condition |

- **Typical length:** 5 to 8 slides, or a 60 to 90 s video in four scenes of 10 to 25 s.
- **Messages:** four, one per part. The Format says the medium: `post-mortem (deck)` or `post-mortem (video)`.
