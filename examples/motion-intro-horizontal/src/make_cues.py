"""Writes src/cues.json: sound cues tied to the beats of the composition, from the same times as build.py."""
import json
from pathlib import Path

import build

TM = build.times()
cues = []


def c(t, sound, gain, note, align="onset", **kw):
    cues.append({"time": round(t, 3), "sound": sound, "align": align, "gain_db": gain, "note": note, **kw})


# 1. the name, the knife, the 15 skills
c(TM["wm0"] + 0.02, "ui_pop/soft", -14, "wordmark reveals")
c(TM["ring0"] - 0.3, "swish/soft", -17, "wordmark moves up", align="peak")
c(TM["ring0"], "whoosh_fast/crisp", -16, "icons burst into a ring", align="peak")
for k in range(4):
    c(TM["ring0"] + 0.2 + 0.2 * k, "fit/tick/domino", -20, f"ring chip {k + 1}", seed=k)
c(TM["count0"] - 0.05, "notify/mid_tine", -15, "the 15 counter enters")
for k in range(6):
    c(TM["count0"] + 0.13 * k, "hover_tick/mid", -21 + 0.4 * k, f"counter tick {k + 1}", seed=k)
c(TM["zoom0"], "whoosh_big/thump_airy", -14, "zoom-through into the feed", align="peak")
c(TM["r2"], "swipe/velvet", -17, "circle mask opens", align="peak")

# 2. the capability feed
A = TM["A"]
for i, a in enumerate(A):
    c(a, "ui_pop/soft", -17, f"card {i + 1} takes focus", seed=i % 5)
c(A[0] + 0.1, "fit/tick/domino", -17, "slide bars rise", seed=1)
c(A[1] + 0.25, "swish/soft", -18, "diagram line draws", align="peak")
c(A[2] + 0.2, "knock/wood", -16, "3D drawer slides out")
c(A[3] + 0.25, "fit/whoosh.short/bamboo_swish", -16, "laser scans the PDF", align="peak")
c(A[4] + 0.3, "swipe/velvet", -16, "tangent glides along the curve", align="peak")
c(A[5] + 0.25, "fit/land.light/fingertip_book", -16, "playhead and clips")
for k in range(3):
    c(A[6] + 0.1 + 0.1 * k, "ui_pop/step", -18, f"swatch {k + 1}", seed=k + 2)
for k in range(7):
    c(TM["n23"] + 0.12 * k, "hover_tick/mid", -21 + 0.4 * k, f"23 languages tick {k + 1}", seed=k)
c(A[8] + 0.15, "pluck/kalimba_soft", -13, "spectrum wakes up", pitch="E5")
c(TM["k9scroll"], "swish/soft", -18, "feed scrolls on", align="peak")
for k in range(6):
    c(TM["names0"] + 0.05 * 4 + 0.1 * k, "hover_tick/mid", -22, f"skill name {k + 1}", seed=k)

# 3. six agents
c(TM["r3"], "whoosh_big/thump_airy", -14, "whip pan to the agents", align="peak")
c(TM["six0"], "cut_hit/sub", -13, "the 6")
for k in range(6):
    c(TM["slot0"] + 0.17 * k, "hover_tick/mid", -22, f"slot {k + 1} lights", seed=k)
for k, t in enumerate(TM["ag"]):
    c(t - 0.3, "swish/soft", -21, f"camera to agent {k + 1}", align="peak")
    c(t, "ui_pop/step", -16, f"agent {k + 1}", seed=k)
c(TM["camEnd"], "pluck/kalimba_soft", -13, "all six on screen", pitch="G5")

# 4. install
c(TM["r4"], "whoosh_fast/crisp", -15, "push up to the install scene", align="peak")
c(TM["s6"] + 0.2, "swipe/velvet", -17, "chat window tilts into place", align="peak")
span = TM["send"] - 0.1 - TM["type0"]
for k in range(10):
    c(TM["type0"] + 0.1 + span * k / 10, "fit/key/thock", -21, f"typing {k + 1}", seed=k)
c(TM["send"], "fit/key.space/thock_space", -14, "send")
c(TM["send"] + 0.25, "swish/soft", -18, "progress bar", align="peak")
for k, t in enumerate((TM["send"] + 0.4, TM["rp2"], TM["rp3"])):
    c(t, "notify/mid_tine", -16 if k < 2 else -13, f"reply {k + 1}")

# 5. close
c(TM["r5"], "whoosh_big/thump_airy", -14, "circle mask to the end card", align="peak")
c(TM["s7"] + 0.04, "pluck/kalimba_ring", -11, "logo", pitch="C5")
c(TM["s7"] + 0.08, "shimmer/m0", -18, "logo shimmer")
for k, t in enumerate((TM["t1"][0], TM["t1"][1], TM["t2"][0], TM["t3"][0])):
    c(t, "ui_pop/soft", -19, f"tagline {k + 1}", seed=k)
c(TM["url0"], "ui_pop/step", -15, "repository url", seed=3)
c(TM["url0"] + 0.9, "swipe/velvet", -19, "sheen on the url", align="peak")

cues.sort(key=lambda x: x["time"])
Path(__file__).with_name("cues.json").write_text(json.dumps({"cues": cues}, indent=1))
print(len(cues), "cues")
