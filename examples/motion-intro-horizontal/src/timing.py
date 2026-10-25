"""Narration timeline of the vertical intro: a thin wrapper over harness/cutroom_timing.py.

    python3 src/timing.py     # assembles work/en/narr_raw.wav and writes work/en/timing.json
build.py and make_cues.py read the result through `load()`. Sentence clips are work/en/v{n}.wav (synthesized with
`tts --voice af_heart@1.0 --pronounce src/pronounce.json` when missing).
"""
import json
from pathlib import Path

import cutroom_timing

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work" / "en"
PAUSE_AFTER = {1: 0.75, 2: 0.5, 3: 0.45, 4: 0.5, 5: 0.55, 6: 0.85}   # natural breath between sentences, in seconds
HOLD = 3.5                                                          # the last frame stays on screen this long

SENTENCES = [
    "cutroom.",
    "A Swiss army knife, with fifteen skills, for making media.",
    "Slides, diagrams, three-D figures, and document extraction.",
    "Math and motion videos, brands, local voice in twenty-three languages, and sound effects.",
    "Works with six coding agents: Claude Code, Cursor, Codex, Antigravity, Gemini, and Kiro.",
    "To install, just send the repository link to your agent, and let it configure everything.",
    "cutroom. Every piece cut on your machine.",
]


def build():
    return cutroom_timing.build(SENTENCES, WORK, voice="af_heart@1.0", lang=None,
                                pronounce=json.loads((HERE / "pronounce.json").read_text()),
                                pauses=PAUSE_AFTER, hold=HOLD)


def load():
    return cutroom_timing.load(WORK)


if __name__ == "__main__":
    d = build()
    for n, s in enumerate(d["sentences"], 1):
        print(n, s["start"], s["end"], " ".join(f"{w['w']}@{w['t0']:.2f}" for w in s["words"]))
    print("speech ends", d["speech_end"], "video", d["duration"])
