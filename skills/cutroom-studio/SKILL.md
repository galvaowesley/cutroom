---
name: cutroom-studio
description: "The Swiss army knife: orchestrates the cutroom-* skills to produce a complete piece of media in a brand, alone or with a crew of agents from different providers working in parallel (Claude Code, Cursor, Codex, Antigravity, Gemini CLI, Kiro). Pieces: report or page from documents with diagrams and figures; narrated explainer video; product, release or PR video; deck; social posts, thumbnails and posters; podcast or audiogram; brand book; vertical cuts of a video. Picks the installed tools (Docling, Archify, Anatomy, Hairline, ManimGX, HyperFrames, Kokoro, Chatterbox, earshot, ffmpeg, Chrome), plans, chains and delivers in one folder, or as a published artifact when the agent can. Use when a request mixes media types, when it is unclear which tool to use, to make a report or artifact more visual, or to split the work across agents. Usage: cutroom-studio <what you want to deliver> [crew]"
metadata:
  version: "2.0.0"
---

# cutroom-studio: one piece, many tools, optionally many agents

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`).

## Step 0: what is installed

Run `cutroom doctor --json`. Plan only with installed components. If the best route needs a missing one, say which,
how much it downloads and the alternative with what exists. Installation goes through `cutroom-init`, by the
person's choice.

## Step 1: understand the delivery

Ask only what cannot be deduced from the request:

- **what:** page or report, video, deck, graphic, audio, or a mix;
- **for whom and where:** team, leadership, clients, social; artifact, email, slides, platform (sizes!);
- **sources:** documents, data, repository, PR, the person's text. No source, no number;
- **format:** duration, orientation (16:9, 9:16, 1:1), language (default from `cutroom config language`), brand
  (default `cutroom brand list` → active; no brand fits → `cutroom-brand`).

Run `cutroom job "<title>"` once and use that folder (`$J`) for every part.

## Step 2: route

| Request | Skills, in order |
|---|---|
| deck or slides in PDF, report with charts | `cutroom-extract` (if documents) → `cutroom-script` → `cutroom-deck` |
| report, summary or comparison from PDFs, sheets, slides, as a page | `cutroom-extract` → text → `cutroom-diagram` and/or `cutroom-iso3d` → page |
| architecture or flow of a system or repository | `cutroom-diagram` (with `repo=`) |
| explain a formula, algorithm, statistic or code in video | `cutroom-script` → `cutroom-math` (narrates with `cutroom-voice`) → optional `cutroom-sound` (`earshot` SFX) |
| product, release, PR or report-summary video, reel, slides video | `cutroom-script` → `cutroom-voice` → `cutroom-motion` → optional `cutroom-sound` (`earshot` SFX) → `cutroom-edit` (music, captions) |
| sound effects, sound kit, or listening/sync audit of an existing video | `cutroom-sound` (`earshot`) |
| vertical or square cuts of a video, captions, music, compression | `cutroom-edit` |
| social posts, stories, thumbnails, OG images, posters, infographics, certificates | `cutroom-graphic` |
| narration of a document, audiobook, podcast | `cutroom-extract` → `cutroom-script` → `cutroom-voice` → `cutroom-edit` (loudnorm, audiogram) |
| a voice for the brand, or a cloned voice (with consent) | `cutroom-voice` |
| a logo | `cutroom-logo` → `cutroom-brand` |
| a brand, design system or brand book | `cutroom-brand` (and `cutroom-logo` if there is no logo) |
| figure that explains a mechanism | `cutroom-iso3d` (Anatomy); live icon, empty state: `cutroom-iso3d` (Hairline) |
| one-page answer | `cutroom-diagram` (Archify explainer mode) |
| a campaign: video + cuts + posts + thumbnail | `cutroom-script` → parallel: `cutroom-motion`, `cutroom-graphic`, `cutroom-voice` → `cutroom-edit` |

Each skill has its own rules and checks: open its `SKILL.md` in the agent's skill folder and follow it.

## Step 3: plan

Show a short plan before producing: the parts, the tool for each, the duration or size and the estimated time (an
Anatomy figure takes 30 to 90 min; a 60 s video, 30 to 60 min; a deck, 20 to 40 min; a set of posts, 10 to 20 min).
For long pieces or pieces leaving the team, wait for the ok.

- Script and facts first, with `cutroom-script`: `$J/src/SCRIPT.md` with the source of each number, checked with
  `cutroom script check`. Every part reads it; that is what keeps them coherent.
- Independent parts (diagram, figure, narration, deck, graphics) can run in parallel: Step 3b.

## Step 3b: parallel parts (optional)

Two ways, chosen by what the person has:

- **Same agent:** your own subagents (in Claude Code, the `Agent` tool). Give each one `$J`, its part, the path of
  the `SKILL.md` to follow and the files it may write.
- **Crew across providers:** `cutroom crew` runs each part on a headless agent CLI (Claude Code, Cursor, Codex, Antigravity,
  Gemini CLI, Kiro), each following a cutroom skill and writing only its own files. You stay the orchestrator.
  1. `cutroom crew runtimes`: which CLIs exist here and whether the cutroom skills are installed for them
     (`python3 install.py --agent ...` adds agents). Use only providers the person already uses (conventions,
     Privacy), and say which part goes to which provider.
  2. Write `$J/work/crew.json` (start from `cutroom crew example`). One task per independent part, with `runtime`,
     `skill`, a precise `prompt` (the scene numbers of `SCRIPT.md`, the output file names, the brand) and `writes`
     globs relative to `$J` that never overlap; `"root": ".."`. Models: `model` for an exact id, or `profile`
     (`fast`, `balanced`, `quality`, configurable in `config.json` → `crew.profiles`).
  3. `cutroom crew run "$J/work/crew.json" --dry-run` until it shows no overlap; then without `--dry-run` (a long
     command). Logs go to `$J/work/logs/<id>.log`.
  4. Review every part as if you had made it: open the outputs, run each skill's check, fix or rerun one task with
     `--only <id>`. If an agent answered with code instead of writing files, `cutroom crew materialize` writes the
     blocks to their files.

## Step 4: assemble

- **Page or report (HTML):** text from the extracted Markdown and the person's data. Archify diagrams and
  Anatomy/Hairline figures are self-contained HTML: embed each in `<iframe src="...">`, or use PNG/SVG when the page
  must be static. Short video: `<video controls>` with a 720p mp4. Use the brand's `tokens.css` and `fonts.css` and
  the recipes in its `DESIGN.md`.
- **Composite video:** render ManimGX clips into `$J/out/clips/`, assemble in HyperFrames as video clips with the
  narration as its own audio, then `cutroom edit score` (music with ducking), `cutroom edit captions` and
  `cutroom edit reframe` for vertical cuts.
- **Campaign:** one SCRIPT.md, one brand, then the cuts (`cutroom edit reframe`), the posts and thumbnail
  (`cutroom-graphic`, same headline and number), the compressed versions (`cutroom edit compress`).
- **Coherence:** the same brand, terms and numbers in every part.

## Step 5: verify and deliver

- Run each part's check (in its skill) and look at the whole: open the page, watch the video or its contact sheet
  (`cutroom edit sheet`), open every graphic.
- Check every number against the source noted in the script.
- **Artifact (Claude Code with claude.ai):** to share, publish the page with the Artifact tool after loading the
  `artifact-design` skill. Diagrams and figures go as page files (`files`, referenced by `<iframe>`); video, GIF and
  images as binary files up to 15 MB. Other agents: deliver the folder.
- Final summary: the path of each deliverable in `$J/out/`, where the sources are, which agent made which part (if a
  crew ran), what was not verified, and the sources of the numbers.
