"""Narration timeline for pieces whose picture follows the voice (HyperFrames, ManimGX, decks).

Kokoro returns no word timings. This module places sentences on a timeline with natural pauses, measures each one
(speech onset and end, silences inside it) and spreads its words between the measured silences in proportion to
their phoneme counts. Phonemes come from the voice's own language (pt-br, es, fr...), not from English.

    from cutroom_timing import build, load
    data = build(["First sentence.", "Second one, with a comma."], work_dir="work", voice="pf_dora",
                 pronounce={"cutroom": "Cátrum"}, pauses={1: 0.75}, pause=0.5, hold=3.5)
    # work/narr_raw.wav (the narration, 24 kHz) and work/timing.json:
    # {"sentences": [{"start", "end", "words": [{"w", "t0", "t1"}]}], "speech_end", "duration"}

    cutroom-python harness/cutroom_timing.py speech.txt --voice pf_dora --pronounce p.json -o work   # one sentence per paragraph

Sentence clips `work/v{n}.wav` are synthesized when missing (and reused when present, so a text change only
re-synthesizes what changed: delete that clip). Everything downstream (composition, cues) reads timing.json:
see examples/motion-intro/src/build.py and make_cues.py.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 24000


def tokens(sentence, pronounce=None):
    """[(spoken word, pause_after)]: the words as the voice is asked to say them (after the pronunciation
    dictionary), with a flag for a comma, colon or full stop that follows the word."""
    text = sentence
    for k in sorted(pronounce or {}, key=len, reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(k)}(?!\w)", lambda m: pronounce[k].replace(" ", " "), text, flags=re.I)
    return [(raw.strip(",.:;!?").replace(" ", " "), raw[-1] in ",.:;!?") for raw in text.split()]


def weights(words, lang):
    """Phoneme count of each word in the voice's language (at least 2)."""
    from kokoro_onnx.tokenizer import Tokenizer
    tk = Tokenizer()
    return [max(2, len(tk.phonemize(w, lang))) for w in words]


def measure(y, sr):
    """(speech onset, speech end, [(silence start, silence end)] longer than 90 ms inside the speech), in seconds."""
    w = int(sr * 0.01)
    e = np.array([np.sqrt(np.mean(y[i:i + w] ** 2) + 1e-12) for i in range(0, len(y) - w, w)])
    db = 20 * np.log10(e)
    act = db > db.max() - 38
    idx = np.where(act)[0]
    gaps, i = [], idx[0]
    while i < idx[-1]:
        if not act[i]:
            j = i
            while not act[j]:
                j += 1
            if (j - i) * 0.01 >= 0.09:
                gaps.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return idx[0] * 0.01, (idx[-1] + 1) * 0.01, gaps


def align(comma_after, wts, a0, a1, gaps):
    """(start, end) of every word between a0 and a1. Each measured silence is attached to the comma nearest to it
    (by phoneme position); words are spread proportionally between those anchors."""
    n, total = len(wts), float(sum(wts))
    cum = np.cumsum([0] + list(wts)) / total
    anchors = {}
    commas = [i for i in range(n - 1) if comma_after[i]]
    for g0, g1 in gaps:
        frac = ((g0 + g1) / 2 - a0) / (a1 - a0)
        free = [c for c in commas if c not in anchors]
        if free:
            c = min(free, key=lambda c: abs(cum[c + 1] - frac))
            if abs(cum[c + 1] - frac) < 0.2:
                anchors[c] = (g0, g1)
    segs, lo = [], 0
    for c in sorted(anchors) + [n - 1]:
        segs.append((lo, c))
        lo = c + 1
    times, t_start = [], a0
    for lo, hi in segs:
        t_end = anchors[hi][0] if hi in anchors else a1
        w = wts[lo:hi + 1]
        edge = np.cumsum([0] + list(w)) / sum(w)
        for j in range(len(w)):
            times.append((t_start + (t_end - t_start) * edge[j], t_start + (t_end - t_start) * edge[j + 1]))
        if hi in anchors:
            t_start = anchors[hi][1]
    return times


def build(sentences, work_dir="work", voice=None, speed=None, lang=None, pronounce=None, pause=0.5, pauses=None,
          lead_in=0.4, hold=3.5):
    """Assemble the narration and measure it. `pauses` maps a sentence number (1-based) to the pause after it,
    in seconds; `pause` is the default (0.45 to 0.85 s sounds natural); `hold` is how long the last frame stays
    after the last word. Returns the timing dict (also written to work_dir/timing.json)."""
    import cutroom_voice as cv
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    v = cv.resolve(voice, lang, speed, pronounce)
    ph_lang = cv.kokoro_lang(v) if v.engine == "kokoro" else cv.lang_key(v.lang)
    t, out, T = lead_in, np.zeros(int(60 * SR), dtype=np.float32), []
    for n, sentence in enumerate(sentences, 1):
        clip = work / f"v{n}.wav"
        if not clip.exists():
            clip.write_bytes(cv.synth_voice(v, sentence))
        y, sr = sf.read(clip)
        y = y if y.ndim == 1 else y.mean(1)
        assert sr == SR, f"{clip} is {sr} Hz, expected {SR}"
        a0, a1, gaps = measure(y, sr)
        shift = t - a0                                    # the speech onset lands on t
        i = max(0, int(round(shift * sr)))
        if i + len(y) > len(out):
            out = np.pad(out, (0, i + len(y) - len(out)))
        out[i:i + len(y)] += y.astype(np.float32)
        toks = tokens(sentence, v.pronounce)
        words = [w for w, _ in toks]
        wt = align([p for _, p in toks], weights(words, ph_lang), a0, a1, gaps)
        T.append({"start": round(t, 3), "end": round(shift + a1, 3),
                  "words": [{"w": w, "t0": round(shift + s, 3), "t1": round(shift + e, 3)} for w, (s, e) in zip(words, wt)]})
        t = shift + a1 + (pauses or {}).get(n, pause)
    end = T[-1]["end"]
    dur = round(end + hold, 1)
    sf.write(work / "narr_raw.wav", np.pad(out, (0, max(0, int(dur * SR) - len(out))))[:int(dur * SR)], SR)
    data = {"sentences": T, "speech_end": end, "duration": dur}
    (work / "timing.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return data


def load(work_dir="work"):
    return json.loads((Path(work_dir) / "timing.json").read_text())


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("speech", help="text file, one sentence per paragraph (blank line between)")
    ap.add_argument("-o", "--work", default="work")
    ap.add_argument("--voice"); ap.add_argument("--speed", type=float); ap.add_argument("--lang")
    ap.add_argument("--pronounce", help="JSON {written: spoken}")
    ap.add_argument("--pause", type=float, default=0.5); ap.add_argument("--hold", type=float, default=3.5)
    a = ap.parse_args()
    sents = [p.strip() for p in Path(a.speech).read_text(encoding="utf-8").split("\n\n") if p.strip()]
    pron = json.loads(Path(a.pronounce).read_text(encoding="utf-8")) if a.pronounce else None
    d = build(sents, a.work, a.voice, a.speed, a.lang, pron, a.pause, hold=a.hold)
    for n, s in enumerate(d["sentences"], 1):
        print(n, s["start"], s["end"], " ".join(f"{w['w']}@{w['t0']:.2f}" for w in s["words"]))
    print("speech ends", d["speech_end"], "video", d["duration"])
