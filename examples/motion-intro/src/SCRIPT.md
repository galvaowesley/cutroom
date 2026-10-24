# cutroom in 34 seconds

| Field | Value |
|---|---|
| Format | product video, vertical 9:16 |
| Audience | technical (developers who use coding agents) |
| Goal | the viewer sees what cutroom makes, which agents it supports, and sends the repository link to their own agent |
| Key message | cutroom brings 15 media skills to 6 coding agents, with local voice and procedural sound, installed from the repository link. |
| Target duration | 34 s |
| Voice | af_heart (Kokoro, en-us, plain preset, speed 1.0) |
| Brand | cutroom |

The Portuguese (pt-BR) version of this piece is [`examples/motion-intro-pt`](../../motion-intro-pt): same scenes, its own script, pronunciation and cues.

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | skills in the repository | 15 skills | `skills/` folder | v2.0 |
| F2 | voice cloning languages | 23 languages | `harness/cutroom_voice.py`, CLONE_LANGS | Chatterbox 0.1.7 |
| F3 | sound bank | 252 sounds | earshot v0.4.0 | earshot 0.4.0 |
| F4 | supported coding agents | 6 agents | `install.py` and `cutroom crew` | v2.0 |

## Scenes

The camera never stops: scenes overlap and every change is a transition (zoom through the icons, circle mask, whip pan, vertical push, pink circle mask). The speech keeps natural pauses (a longer breath after "cutroom", 0.45 to 0.85 s between sentences); the animation keeps moving through them.

### 1. The name, the knife and the 15 skills · 0:00–0:05.9

- **Goal:** introduce the name and the Swiss army knife idea.
- **On screen:** wordmark, ring of skill icons, counter 15, a sentence whose words rise from a mask
- **Speech:** cutroom. (pause) A Swiss army knife, with fifteen skills, for making media.
- **Visual:** cutroom-motion: the wordmark reveals and moves up, the icons burst into a ring and the camera flies through the ring (zoom through) into the next scene.
- **Facts:** F1

### 2. What it makes · 0:05.0–0:16.7

- **Goal:** show each capability at the moment it is named.
- **On screen:** a vertical feed of cards that keeps rising; the card being spoken takes focus
- **Speech:** Slides, diagrams, three-D figures, and document extraction. Math and motion videos, brands, local voice in twenty-three languages, and sound effects.
- **Visual:** bars and KPI, a diagram with a pulse, an isometric drawer, a PDF laser, a tangent on a curve, a timeline, a palette, languages (23), a spectrum (252), the names of the 15 skills.
- **Facts:** F2, F3

### 3. Six agents · 0:15.7–0:23.3

- **Goal:** name the six agents with the camera moving from one to the next.
- **On screen:** 6 and "coding agents", a grid of six cards with the camera closing in on each card and pulling back to the full grid
- **Speech:** Works with six coding agents: Claude Code, Cursor, Codex, Antigravity, Gemini, and Kiro.
- **Visual:** lateral whip pan in, camera zoom on each name, pull back to the full grid.
- **Facts:** F4

### 4. Install · 0:22.2–0:29.0

- **Goal:** show that sending the link is enough.
- **On screen:** "Just send the link", a chat window that straightens, typed text, progress and replies
- **Speech:** To install, just send the repository link to your agent, and let it configure everything.
- **Visual:** vertical push in, a slow camera push through the whole scene.

### 5. End card · 0:28.1–0:34.1

- **Goal:** fix the brand and the URL; the last frame stays up for 3.5 s after the speech.
- **On screen:** stacked logo, "Every piece cut on your machine.", github.com/galvaowesley/cutroom
- **Speech:** cutroom. Every piece cut on your machine.
- **Visual:** pink circle mask, logo revealed bottom to top, a sheen across the URL and a slow push to the end.

## Pronunciation

| written | spoken |
|---|---|
| Kiro | Kee-ro |

The other names (cutroom, Cursor, Codex, Antigravity, Gemini, Claude Code) are read correctly by the en-us phonemizer: check with `voice phonemes af_heart "<word>"`.
