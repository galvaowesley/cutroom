---
name: cutroom-init
description: "Entry point of the cutroom media skills (cutroom-*), for Claude Code, Cursor, Codex, Antigravity, Gemini CLI and Kiro, on Linux, macOS and Windows. Shows the catalog (each skill, what it does, the tool behind it, what it downloads and how much) and installs only what the person chooses, in a pinned environment (uv + Python, Node 22, pinned versions). Tools: Docling, ManimGX, HyperFrames, Archify, Anatomy, Hairline, Kokoro, Chatterbox, earshot, the logo-design skill, Chrome and ffmpeg. Also diagnoses (doctor), listens for upstream skill/tool updates with manual or pre-approved automatic updates (updates), removes components and changes settings (output folder, language, brand, update policy). Use to install, configure, check, update or remove the media skills, or when another cutroom-* skill says a component is missing. Usage: cutroom-init [doctor | updates | remove <component...> | <component...> | config]"
metadata:
  version: "2.0.0"
---

# cutroom-init: catalog and opt-in installation

No tool skill or heavy download goes in without the person choosing it. This skill shows what exists and what it
costs on disk, and installs only the choice. Read the shared conventions first:
`~/.local/share/cutroom/harness/conventions.md`. Its "Agents" table says how to do each step in your agent.

`cutroom` = `~/.local/share/cutroom/bin/cutroom` (after `. ~/.local/share/cutroom/env.sh`).

## Step 1: mode

| Argument | Do |
|---|---|
| empty | Step 2 (catalog and choice) |
| `doctor` | run `cutroom doctor`, show it, explain what is missing, stop |
| `updates` | Step 7 (check/listen for upstream skill updates and configure manual or auto-update policy) |
| `remove <comp...>` | Step 5 |
| component names (`extract`, `math`...) | Step 3 with those |
| `config` | Step 6 |

## Step 2: catalog

Run `cutroom catalog --json` and show one row per component:

| Skill | What it does | Tool (license) | Downloads | Size | Status |
|---|---|---|---|---|---|

- **Status:** installed, available, or the missing prerequisite (`missing` and `missing_fix` in the JSON).
- Give the free disk space (`free_gb`).
- Point out the heavy ones: `extract` (~2.3 GB, torch and models) and `voice-clone` (~4.5 GB, torch and Chatterbox
  weights). The light voice (`voice`, Kokoro, ~740 MB) already narrates in English, Portuguese, Spanish, French,
  Italian, Hindi, Japanese and Mandarin; `voice-clone` is only for cloning a voice with consent or for its 23
  languages.

Ask which to install, multiple choice, listing only components not yet installed, each with its size. Group them if
the agent limits the number of options:

- Documents, decks and graphics: `extract`, `deck`, `graphic`, `diagram`, `iso3d`
- Video, voice, sound and editing: `math`, `motion`, `voice`, `sound`, `edit`
- Brand and optional: `logo`, `voice-clone`, `docling-mcp`, `earshot-mcp`

If nothing is chosen, stop and say how to come back (the `cutroom-init` skill again).

`docling-mcp` only makes sense with `extract`; it registers the `docling` MCP server in **Claude Code** (user scope).
Other agents use the CLI through `cutroom-extract`.

## Step 3: prerequisites and plan

Run `cutroom setup <components>` (without `--yes`). It prints the plan and exits with code 2 if a prerequisite is
missing. For each missing one, show the `fix`:

- System packages (ffmpeg, Chrome, git) stay with the person: `brew install ...` on macOS, `sudo apt install ...` on
  Linux, `winget install ...` on Windows. In Claude Code, suggest `! <command>` in the prompt.
- `node22`: with nvm, offer `bash -c '. ~/.nvm/nvm.sh && nvm install 22'` (it keeps the default node). On Windows,
  `winget install OpenJS.NodeJS.LTS`.
- `uv`: offer the installer from the `fix` field.

Run again until the plan has no blocker.

## Step 4: install

The choice in Step 2 confirms what was shown. If the list changed afterwards, confirm again.

Run `cutroom setup <components> --yes`. `extract` and `voice-clone` take minutes: run as a long command. For each
component, setup:

1. downloads what it needs: locked Python environment, pinned npm CLI, official skill at the pinned tag, models;
2. copies the matching `cutroom-*` skill into the skill folder of each agent chosen in `install.py`;
3. regenerates `env.sh`, `env.ps1` and the shortcuts in `bin/`.

If it fails midway, show the error. Setup is idempotent: running again continues where it stopped.

Then run `cutroom doctor` and a quick test of each installed component, after `. ~/.local/share/cutroom/env.sh &&`,
with `$T` a temporary folder:

| Component | Test (must finish without error) |
|---|---|
| `extract` | `echo '<h1>test</h1><table><tr><td>a</td><td>1</td></tr></table>' > $T/t.html && docling convert $T/t.html --to md --output $T` |
| `math` | `manimgx --version` |
| `voice` | `tts "Hello, team." -o $T/t.wav` |
| `voice-clone` | `voice presets --lang en` (the clone itself needs a reference: see `cutroom-voice`) |
| `motion` | `hyperframes doctor --json` (only the optional `whisper-cpp` and `BGM (MusicGen)` may fail) |
| `diagram` | `archify doctor` |
| `diagram`, `iso3d` | `record-html "data:text/html,<h1>ok</h1>" $T/t.mp4 --seconds 1 --wait 0.3` |
| `deck` | `deck --help` |
| `graphic` | `cutroom render new social $T/g && cutroom render $T/g/social.html -o $T/g.png --size og` |
| `edit` | `cutroom edit probe $T/t.mp4` (after the record-html test) or `ffmpeg -version` |
| `sound` | `earshot sfx render ui_pop/soft -o $T/pop.wav && earshot measure $T/pop.wav` |
| `logo` | `python3 ~/.local/share/cutroom/upstream/logo/skills/logo-design/scripts/search_library.py --summary --industry developer-tools` |

Summarize:

- the skills that are ready and how to call them: `/cutroom-diagram` in Claude Code, Cursor and Kiro, `$cutroom-diagram` in
  Codex, by name in Antigravity and Gemini CLI;
- if a new skill does not show up, open a new agent session;
- where pieces go (`cutroom paths` → `output_dir`), the active brand (`cutroom brand list`) and the default voice
  (`voice list`);
- how to update: `git pull` in the clone, `python3 install.py` again and, if a pinned version changed,
  `cutroom-init <component>`.

## Step 5: remove

Run `cutroom remove <components>` to see the plan. Show what goes and confirm with the person, then
`cutroom remove <components> --yes`. The skill goes too when no other component of it is left. Cloned voices and
user brands are kept (remove them with `voice remove` and `cutroom brand remove`).

## Step 6: settings

| Setting | Command |
|---|---|
| where pieces are created | `cutroom config output_dir <folder>` |
| default content and narration language | `cutroom config language pt-BR` (BCP 47: `en`, `en-GB`, `es`...) |
| default brand | `cutroom brand use <name>` (list: `cutroom brand list`; new: the `cutroom-brand` skill) |
| default voice | `voice default <profile or preset>` (see `cutroom-voice`) |
| where the harness lives | rerun `python3 install.py --home <folder>` from the clone (e.g. to keep it in Documents); components installed in the old home are not moved |
| agents | rerun `python3 install.py --agent claude,cursor,codex,antigravity,kiro` |
| upstream update mode | `cutroom updates policy --mode ask\|auto\|off` (or `--approve <source...>`) |

## Step 7: checking and watching upstream skill updates (`cutroom updates`)

The harness can listen to the upstream GitHub repositories of the skills and tools (`manimgx`, `archify`, `hyperframes`, `anatomy`, `hairline`, `logo`, `earshot`, `docling`, `kokoro-onnx`, `chatterbox`, and `cutroom` itself):

```bash
cutroom updates check                                 # check all upstream skill/tool repos in parallel
cutroom updates check --apply-auto                    # check and automatically apply any pre-approved updates
cutroom updates apply <source...> --yes               # manually approve and apply local update(s)
cutroom updates policy --mode ask                     # default: suggest updates and wait for manual approval
cutroom updates policy --mode auto                    # pre-approve automatic updates for all upstream repos
cutroom updates policy --mode ask --approve earshot   # auto-update earshot, ask manually for the rest
cutroom updates watch --interval 60 --apply-auto      # background listener (or --once on session start)
```

When `updates.mode` is `ask` (the default) and `cutroom updates check` finds a newer tag or commit, show the available update (`<source>: <installed> → <latest>`) and ask with options whether the person wants to:
1. Update locally now (`cutroom updates apply <source> --yes`),
2. Pre-approve automatic updates for that source (`cutroom updates policy --approve <source>`), or
3. Keep the current pinned version.

## The default environment

| Piece | Where | Why |
|---|---|---|
| Python via `uv`, one environment per tool group, locked (`harness/envs/*/uv.lock`) | `<home>/envs/{extract,media,clone}` | Docling needs `typer<0.27` and ManimGX `typer>=0.27.2`; Chatterbox pins torch 2.6. Locks give everyone the same result |
| CPU torch on Linux (`download.pytorch.org/whl/cpu`) | `extract`, `clone` | avoids GBs of CUDA; macOS uses Apple's MPS |
| Node 22 (from PATH or nvm) | `env.sh` | HyperFrames needs Node ≥ 22; the person's default node does not change |
| Official skills at the pinned tag | `<home>/upstream/` | authoring rules match the CLI version, without flooding the skill menu |
| Kokoro v1.0 (ONNX), Chatterbox weights | `<home>/models/` | local voices shared by `cutroom-voice`, `cutroom-math` and HyperFrames |
| Brands and voices | `<home>/brands/`, `<home>/voices/` | the person's own; they survive reinstalls |
