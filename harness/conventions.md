# cutroom conventions

Every `cutroom-*` skill follows these rules. They exist so anyone produces pieces the same way, in the same place,
with the same versions, in the chosen brand, without sending data out of the machine by accident.

## Environment

- The cutroom home is `~/.local/share/cutroom` on Linux and macOS and `%LOCALAPPDATA%\cutroom` on Windows, unless the
  person installed it elsewhere (`install.py --home <dir>`). The skills you are reading already point at the real
  home: use the paths exactly as written.
- Each shell call is a fresh shell. Start every command that uses a tool with
  `. ~/.local/share/cutroom/env.sh && ...` (Windows PowerShell: `. "<home>\env.ps1"; ...`). It puts the shortcuts
  on the PATH (`cutroom`, `tts`, `voice`, `deck`, `docling`, `manimgx`, `hyperframes`, `archify`, `record-html`,
  `earshot`, `cutroom-python`), points at Chrome, turns telemetry off and unsets cloud API keys.
- `cutroom` is the entry point: `cutroom catalog | doctor | setup | job | paths | config | brand | voice | script |
  deck | render | edit | crew`. It works the same in Claude Code, Cursor, Codex, Antigravity, Gemini CLI and Kiro: nothing in
  the skills depends on one agent's folders.
- Never use `pip install`, `uv tool install`, `uvx`, `npm i -g`, `npx <tool>@latest`, `npx skills add`,
  `hyperframes skills update` or `hyperframes upgrade`, even if an official skill says so: skip its installation
  section, the shortcuts are already on the PATH. Versions are pinned in `harness/cutroom.py` and change by pull request.
- Missing component: say which, how much it downloads (`cutroom catalog`) and offer the `cutroom-init` skill. Do not
  install without the person choosing.

## Piece folder

- Every new piece gets a folder: `cutroom job "<short title>"` creates `<output_dir>/<YYYY-MM-DD>-<slug>/` and prints
  it (`output_dir` is in `cutroom paths`; default `~/Documents/cutroom`). Inside:
  - `src/`: editable sources only (scene `.py`, HTML composition, diagram JSON, script, deck.py);
  - `work/`: neither source nor delivery (downloaded references, extracted frames, drafts, caches);
  - `out/`: deliverables.
- Do not write into the repository the person is working in unless they ask (e.g. a diagram for `docs/`).
- Changes to an existing piece reuse its folder. A new piece gets a new folder.

## Content

- **Language:** the `language` in `cutroom config` (default English) for text and narration, unless the request is in
  or asks for another language. Established technical terms stay as they are.
- Every number, name and fact comes from the person or from a source they gave (a document extracted with
  `cutroom-extract`, data, code). Examples in official skills are illustrative: never copy their data. If a number
  is missing, ask, or mark it as illustrative in the piece itself.
- **Script before production:** for video, narration and decks, write `src/SCRIPT.md` in the `cutroom-script` format
  (facts with sources, scenes, speech) and run `cutroom script check`. Confirm it with the person when the piece is
  longer than ~30 s or ~10 slides, or goes outside the team.

## Brand

The active brand is in `cutroom brand show --json` (another one: `cutroom brand show <name> --json`). Before
composing anything visual, read its `DESIGN.md` (rules) and `VOICE.md` (tone); the JSON gives colors, fonts, logos
and the absolute paths of `tokens.css` (CSS custom properties) and `fonts.css` (local `@font-face`). A brand the
person names in the request wins over the active one. No brand fits: offer the `cutroom-brand` skill to build one.

- **Color:** `primary` is the constant; `deep` gives depth (verdicts, code, dark video); `accent` marks the one thing
  to look at, never body text; `scale` is for ordered data; `success`, `warning`, `danger` only mean state.
- **Backgrounds:** solid. Depth from `deep` or a soft accent glow in one corner, not full gradients (unless the
  brand's DESIGN.md says otherwise).
- **Type:** `fonts.display` for titles and big numbers, `fonts.text` for body, `fonts.mono` for code. They are
  registered on the system by `cutroom brand use`, so ManimGX, Chrome and ffmpeg find them by family name; in HTML
  and video, link the brand's `fonts.css` (or copy it with the `fonts/` folder) so renders work offline.
- **Logo:** `logos.on_primary` over primary or deep, `logos.on_light` over light backgrounds; symbols for small
  spaces. Never recolored, rotated, shadowed or faded. In video it enters by cut or mask, never by fade. Only on
  pieces that speak for the brand (covers, closing slides, end cards).
- **Motion:** the brand's `motion.ease` and `duration_ms`; short fades and translates, no bounce.
- **Per tool:** HyperFrames, `cutroom-deck`, `cutroom-graphic` and HTML pages apply everything. In ManimGX,
  `background_color`, colors and `font=`. Archify and Anatomy have their own palettes: change only the accent if the
  tool allows. Hairline is colorless line (its rule 04): the brand enters through text and frame.

## Privacy

- Nothing leaves the machine without an explicit request: no cloud TTS (ElevenLabs, fal.ai, HeyGen), no cloud image
  or music generation, no `docling --enable-remote-services`, no public galleries (`anatomy scripts/publish.mjs`,
  `hyperframes publish`). Official skills offer these paths; here they are off by default.
- `env.sh` unsets cloud keys (`FAL_KEY`, `ELEVENLABS_API_KEY`, `HEYGEN_*`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`), so no
  tool uses a service by itself (e.g. `hyperframes snapshot --describe`).
- **Voice cloning only with the consent of the person whose voice it is.** `voice clone` requires `--speaker` and
  `--consent` and stores them with the reference audio, locally. Never clone a public figure or anyone who has not
  agreed; never present a cloned voice as the real person.
- **Crew:** `cutroom crew` sends the prompts of each task to the agent CLI that runs it, and through it to that
  provider. Use it only with providers the person already uses for this material.

## Verification

- Each tool has its check, and each skill says which. Run it until it passes and **look** at the result
  (storyboard, frames, PNG, grid) before saying it is good. If you could not look, say so.
- Draft first at low resolution (720p, 30 fps). Final render only after the draft is approved, or directly when the
  piece is short and the person already gave the format.

## Delivery

- List what is in `out/` (absolute paths) and where the sources are in `src/`, for whoever wants to edit.
- If the agent can publish pages (in Claude Code with claude.ai, the **Artifact** tool), offer to publish, or publish
  when the person asks for a shareable page. In Claude, load the `artifact-design` skill first. Self-contained HTML
  (decks, Archify, Anatomy, Hairline, graphics) publishes directly. Video, audio and images go as artifact files (up
  to 15 MB each): `cutroom edit compress in.mp4 -o out.mp4 --preset artifact`.
- Without publishing, deliver the files and say how to open them (`open` on macOS, `xdg-open` on Linux, `start` on
  Windows).

## Agents

The skills run in Claude Code, Cursor, Codex, Antigravity, Gemini CLI and Kiro. When a step names one agent's tool, use your
equivalent:

| For | Claude Code | Cursor / Codex / Antigravity / Gemini / Kiro |
|---|---|---|
| ask with options | `AskUserQuestion` (with `multiSelect` when it fits) | numbered list in the reply, then wait |
| skill arguments | `$ARGUMENTS` | the text after the skill name (Kiro CLI: also `$ARGUMENTS`) |
| long command (> 2 min) | Bash with `timeout: 600000` or in the background | run in the background and follow the log |
| parallel work, same agent | subagents (`Agent`) | subagents if available (Kiro has them); otherwise in sequence |
| parallel work, any provider | `cutroom crew run crew.json` (see `cutroom-studio`) | the same |
| publish a page | `Artifact` | deliver the file |
