# cutroom in 28 seconds

| Field | Value |
|---|---|
| Format | product video |
| Audience | technical (developers who use coding agents) |
| Goal | whoever watches sees each media capability in action, knows which coding agents are supported, and knows to paste the repo link into their agent to set it up |
| Key message | cutroom gives 6 coding agents 15 media skills with local voice and 252 procedural sound effects, configured by handing the repository link to your agent. |
| Target duration | 24 to 30 s |
| Voice | narrator (af_heart@0.95) |
| Brand | cutroom |

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | skills in the repository | 15 skills | skills/ folder (4 base + 11 opt-in components) | v2.0 |
| F2 | languages of cloned voices | 23 languages | harness/cutroom_voice.py, CLONE_LANGS | Chatterbox 0.1.7 |
| F3 | procedural and fitted sound bank | 252 sounds | Leonxlnx/earshot v0.4.0 bank (forge_v2 + forge04 + fit + pluck) | earshot 0.4.0 |
| F4 | coding agents supported | 6 agents | install.py (claude, cursor, codex, antigravity, kiro) and cutroom crew (gemini) | v2.0 |

## Scenes

### 1. Capabilities I: Decks, Diagrams, 3D and Extraction · 0:00–0:06

- **Goal:** open immediately on what cutroom produces, with animated visual representations of decks, diagrams, 3D figures and extraction.
- **On screen:** cutroom · 15 media skills, cut in code
- **Speech:** [cutroom]. [Fifteen skills] that turn data and docs into [decks], [live diagrams], and [isometric figures].
- **Visual:** cutroom-motion: 4 animated capability cards on night plum (rising bar chart deck, pulsing node-graph diagram, sliding isometric 3D drawers, laser-scanned PDF-to-Markdown extraction).
- **Facts:** F1

### 2. Capabilities II: Math, Motion, Brand, Voice and Sound · 0:06–0:14

- **Goal:** show animated math curves, motion timelines, brand systems, local voice cloning and earshot sound design.
- **On screen:** Math, motion, brand, 23-language voice, 252 sounds
- **Speech:** [Scripted math] and [motion videos], [brand systems], local voice cloning in [twenty-three languages], and [earshot] sound design.
- **Visual:** cutroom-motion: 4 live widgets on blush paper (cubic curve with moving tangent readout f'(x)=1.25, multi-track GSAP timeline playhead, morphing brand palette swatches, and 32-bar voice + earshot spectrum).
- **Facts:** F2, F3

### 3. Compatible with the Major Coding Agents · 0:14–0:22

- **Goal:** show compatibility with the 6 major coding agents and the local/pinned/parallel architecture.
- **On screen:** Runs in 6 coding agents · Local, pinned, parallel
- **Speech:** Compatible with [six coding agents]: [Claude Code], [Cursor], [Codex], [Antigravity], [Gemini], and [Kiro]. [Local, pinned, and parallel].
- **Visual:** cutroom-motion: central cutroom hub radiating animated connection pulses to 6 agent cards (Claude Code, Cursor, Codex, Antigravity, Gemini CLI, Kiro), with Local, Pinned and Parallel status badges lighting up below.
- **Facts:** F4

### 4. Simplified Agent Setup · 0:22–0:28

- **Goal:** show how effortless installation is: just give the repository link to your coding agent.
- **On screen:** Give the repository link to your coding agent
- **Speech:** To start, just [give the repository link] to your coding agent, and [let it configure cutroom].
- **Visual:** cutroom-motion: agent prompt window typing "Configure github.com/galvaowesley/cutroom", followed by animated setup checkmarks and an iris wipe to the Hot Signal cutroom end card.

## Pronunciation

| written | spoken |
|---|---|
| Kiro | Kee-ro |
| earshot | ear-shot |
