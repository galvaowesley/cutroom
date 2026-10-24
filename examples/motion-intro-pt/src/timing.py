"""Narration timeline of the vertical intro: a thin wrapper over harness/cutroom_timing.py.

    python3 src/timing.py     # assembles work/v4/narr_raw.wav and writes work/v4/timing.json
build.py and make_cues_pt.py read the result through `load()`. Sentence clips are work/v4/v{n}.wav (synthesized with
`tts --voice pf_dora@1.0 --pronounce src/pronounce_pt.json` when missing).
"""
import json
from pathlib import Path

import cutroom_timing

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work" / "v4"
PAUSE_AFTER = {1: 0.75, 2: 0.5, 3: 0.45, 4: 0.5, 5: 0.55, 6: 0.85}   # natural breath between sentences, in seconds
HOLD = 3.5                                                          # the last frame stays on screen this long

SENTENCES = [
    "cutroom.",
    "Um canivete suíço, com quinze skills, para criação de mídia.",
    "Slides, diagramas, figuras em três dê, e extração de documentos.",
    "Vídeos de matemática e motion, marcas, voz local em vinte e três idiomas, e efeitos sonoros.",
    "Funciona com seis agentes de código: Claude Code, Cursor, Codex, Antigravity, Gemini e Kiro.",
    "Pra instalar, é só mandar o link do repositório pro seu agente, e deixar ele configurar tudo.",
    "cutroom. Toda peça gerada na sua máquina.",
]


def build():
    return cutroom_timing.build(SENTENCES, WORK, voice="pf_dora@1.0", lang=None,
                                pronounce=json.loads((HERE / "pronounce_pt.json").read_text()),
                                pauses=PAUSE_AFTER, hold=HOLD)


def load():
    return cutroom_timing.load(WORK)


if __name__ == "__main__":
    d = build()
    for n, s in enumerate(d["sentences"], 1):
        print(n, s["start"], s["end"], " ".join(f"{w['w']}@{w['t0']:.2f}" for w in s["words"]))
    print("speech ends", d["speech_end"], "video", d["duration"])
