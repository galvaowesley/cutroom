"""Fills src/intro.template.html with the narration times and writes src/intro/index.html.

Every time in the composition (scene starts, card focus, camera moves, typing, tagline words) is derived from
work/v4/timing.json (see timing.py), so the picture follows the voice. Run: python3 src/build.py
"""
import json
import re
from pathlib import Path

import timing

HERE = Path(__file__).resolve().parent


def times():
    d = timing.load()
    sent = d["sentences"]
    S = lambda n: sent[n - 1]["start"]
    En = lambda n: sent[n - 1]["end"]
    W = lambda n, i: sent[n - 1]["words"][i]["t0"]
    DUR = d["duration"]
    t23 = W(3, 0)
    A = [W(3, 0), W(3, 1), W(3, 2), W(3, 7), W(4, 0), W(4, 4), W(4, 5), W(4, 6), W(4, 14)]
    for i in range(1, len(A)):                      # a card needs 0.6 s to take focus: never closer than that
        A[i] = max(A[i], A[i - 1] + 0.6)
    TM = {
        "DUR": DUR, "wm0": S(1), "ring0": W(2, 0),
        "l1": [W(2, i) for i in (0, 1, 2)], "l2": [W(2, i) for i in (3, 4, 5)], "l3": [W(2, i) for i in (6, 7, 8, 9)],
        "count0": W(2, 4), "zoom0": t23 - 0.75, "r2": t23 - 0.62,
        "A": A, "n23": W(4, 9) - 0.1, "k9scroll": En(4) - 0.34, "names0": En(4) - 0.5,
        "r3": S(5) - 0.54, "six0": W(5, 2), "slot0": W(5, 3),
        "ag": [W(5, i) for i in (6, 8, 9, 10, 11, 13)], "camEnd": En(5),
        "r4": S(6) - 0.44, "s6": S(6), "type0": W(6, 4), "send": W(6, 12) - 0.33, "rp2": W(6, 15), "rp3": W(6, 16),
        "r5": S(7) - 0.55, "s7": S(7),
        "t1": [W(7, 1), W(7, 2)], "t2": [W(7, 3), W(7, 4), W(7, 5)], "t3": [W(7, 6)],
        "url0": En(7) + 0.05,
    }
    TM["s1_dur"] = TM["r2"] + 0.8
    TM["s2_dur"] = TM["r3"] + 1.05 - TM["r2"]
    TM["s3_dur"] = TM["r4"] + 1.05 - TM["r3"]
    TM["s4_dur"] = TM["r5"] + 0.9 - TM["r4"]
    TM["s5_dur"] = DUR - TM["r5"]
    TM["prog_dur"] = (En(6) - 0.2) - (TM["send"] + 0.25)
    TM["narr_dur"] = En(7) + 0.9
    TM["sfx_dur"] = DUR - 0.1
    return TM


def r(x):
    return [r(v) for v in x] if isinstance(x, list) else round(x, 3)


if __name__ == "__main__":
    TM = {k: r(v) for k, v in times().items()}
    html = (HERE / "intro.template.html").read_text()
    html = html.replace("{{TM_JSON}}", json.dumps(TM))
    html = re.sub(r"\{\{(\w+)\}\}", lambda m: str(TM[m.group(1)]), html)
    (HERE / "intro" / "index.html").write_text(html)
    print(json.dumps(TM, indent=0)[:1500])
