"""Turn work/events.json (written by scene.py) into src/cues.json for `cutroom edit sfx`.

Every sentence, tab, readout, zoom tick, camera move, step and landing gets a sound, in a small palette:
soft pops for text, ticks for discrete steps, swishes for camera moves, knocks for the bouncing run,
a kalimba note for each arrival. Gains stay 12 to 22 dB under the voice.

Run: python3 src/make_cues.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
events = json.loads((HERE.parent / "work" / "events.json").read_text())

T = {e["key"]: e["t"] for e in events if e["name"] == "cap"}
E = {}
for e in events:
    E.setdefault(e["name"], []).append(e)
run_t = {e["which"]: e["t"] for e in E["run"]}
scene_t = {e["which"]: e["t"] for e in E["scene"]}

cues = []


def cue(t, sound, gain, note, align="onset", **kw):
    cues.append({"time": round(t, 3), "sound": sound, "align": align, "gain_db": gain, "note": note, **kw})


# a soft pop under every caption sentence
for i, (k, t) in enumerate(T.items()):
    cue(t + 0.04, "ui_pop/soft", -22, f"caption {k}", seed=i % 5)

# 1. the landscape and its slice
cue(T["a1"] + 0.9, "swish/soft", -16, "surface fades in, camera swings", align="peak")
cue(T["a2"] + 0.25, "fit/tick/domino", -15, "the weight lands on the surface", seed=0)
cue(T["a2"] + 0.7, "swipe/velvet", -17, "the slice curve lights up", align="peak")
cue(T["a3"] + 0.7, "fit/whoosh.short/bamboo_swish", -14, "camera goes side-on, the surface fades", align="peak")
cue(T["a3"] + 1.5, "cut_hit/sub", -14, "the 2D view locks")
cue(T["a3"] + 1.7, "ui_pop/step", -17, "tabs enter")

# 2. zoom until it is a line (the readout doubles about every 0.41 s)
t0 = T["b1"]
cue(t0 + 0.1, "ui_pop/step", -16, "tangent and readouts enter", seed=1)
for k in range(1, 11):
    cue(t0 + 0.15 + 0.41 * k, "hover_tick/mid", -17 + 0.25 * k, f"zoom x{2 ** k}", seed=k)
cue(t0 + 2.4, "whoosh_fast/crisp", -17, "the zoom accelerates", align="peak")
cue(E["zoom_end"][0]["t"] - 0.05, "pluck/kalimba_soft", -12, "zoom locks: a straight line", pitch="B5")
cue(T["b2"] + 0.5, "notify/mid_tine", -16, "slope readout")
slide = E["slide"][0]["t"]
cue(slide - 1.0, "fit/whoosh.short/bamboo_swish", -16, "zoom back out", align="peak")
cue(slide + 0.8, "swipe/velvet", -16, "the point slides, the slope changes sign", align="peak")
cue(slide + 1.6, "fit/tick/domino", -17, "slope crosses zero", seed=9)

# 3. step against the slope, then the rule explained part by part
cue(scene_t["step"] + 0.1, "ui_pop/step", -16, "topic: step", seed=2)
cue(T["c1"] + 0.3, "ui_pop/step", -16, "step arrow", seed=3)
cue(T["r1"] + 0.05, "fit/land.light/fingertip_book", -15, "w(t+1) =  (new weight)")
cue(T["r1"] + 0.8, "ui_pop/soft", -16, "w(t)  (old weight)", seed=1)
cue(T["r2"] + 0.1, "ui_pop/soft", -17, "minus", seed=2)
cue(T["r2"] + 0.5, "ui_pop/step", -15, "eta  (learning rate)", seed=4)
cue(T["r2"] + 1.2, "ui_pop/step", -15, "f'(w)  (slope)", seed=5)
cue(T["r2"] + 1.7, "notify/mid_tine", -15, "the rule is complete")
for k in range(8):
    cue(T["c2"] + 0.425 * (k + 1) - 0.05, "knock/wood", -15 - 0.6 * k, f"hop {k + 1}", seed=k)
cue(T["c2"] + 3.45, "pluck/kalimba_soft", -14, "near the bottom", pitch="E5")

# 4. learning rate
cue(T["d1"] + 0.1, "ui_pop/step", -16, "tab: rate", seed=4)
cue(T["d1"] + 0.5, "fit/land.light/fingertip_book", -16, "rate readouts")
for tag, n, dur, sound, gain in (("crawl", 10, 2.3, "tap/knuckle", -19), ("good", 6, 1.8, "fit/tick/domino", -16), ("bounce", 10, 2.5, "knock/desk", -14)):
    t = run_t[tag]
    cue(t + 0.1, "pro_pop_in/round", -17, f"{tag} label")
    for k in range(n):
        kw = {"pan": -0.55 if k % 2 == 0 else 0.55} if tag == "bounce" else {}
        cue(t + 0.1 + dur * (k + 1) / n - 0.05, sound, gain, f"{tag} hop {k + 1}", seed=k, **kw)
cue(run_t["good"] + 0.1 + 1.8, "pluck/kalimba_soft", -12, "it settles", pitch="G5")
cue(run_t["bounce"] + 0.1 + 0.3, "cut_hit/kick", -17, "the first jump across the valley")

# 5. one more weight
cue(scene_t["surface"] + 0.1, "ui_pop/step", -16, "tab: 3D", seed=5)
cue(T["e1"] + 1.0, "whoosh_big/thump_airy", -15, "the curve sweeps into a surface", align="peak")
cue(T["e1"] + 2.0, "swish/soft", -17, "camera tilts", align="peak")
cue(T["e2"] + 0.5, "swipe/velvet", -16, "second weight: the point slides along y", align="peak")
cue(T["e2"] + 0.9, "ui_pop/step", -16, "slope along x", seed=6)
cue(T["e2"] + 1.1, "ui_pop/step", -17, "slope along y", seed=7)
cue(T["e2"] + 1.1, "swish/soft", -17, "the camera orbits and closes in", align="peak")
cue(T["e3"] + 0.5, "whoosh_fast/crisp", -17, "close-up on the point", align="peak")
cue(T["e3"] + 0.2, "fit/land.light/fingertip_book", -15, "the rule becomes the gradient")
cue(T["e3"] + 0.3, "notify/mid_tine", -14, "gradient arrow")
cue(T["e4"] + 0.45, "swipe/velvet", -15, "the arrow flips", align="peak")
cue(T["e4"] + 1.4, "swish/soft", -18, "guides fade", align="peak")
cue(T["e4"] + 2.2, "swipe/velvet", -16, "the figure turns to show the descent", align="peak")
d3 = E["descent3d"][0]["t"]
cue(d3, "ui_pop/soft", -17, "3D readouts")
cue(d3 + 1.2, "whoosh_fast/crisp", -18, "orbit while following", align="peak")
for k in range(12):
    cue(d3 + 3.3 * (k + 1) / 12 - 0.05, "fit/tick/domino", -16 - 0.2 * k, f"3D hop {k + 1}", seed=k + 10)
cue(E["min3d"][0]["t"] - 0.1, "pluck/kalimba_soft", -12, "the minimum", pitch="C6")

# 6. close
cue(T["f1"] + 0.5, "mallet/celesta", -15, "one rule", pitch="E5")
end = E["close"][0]["t"]
cue(end - 0.6, "pluck/kalimba_ring", -12, "logo", pitch="C5")
cue(end - 0.55, "shimmer/m0", -18, "logo shimmer")

cues.sort(key=lambda c: c["time"])
(HERE / "cues.json").write_text(json.dumps({"cues": cues}, indent=1))
print(f"{len(cues)} cues, {cues[0]['time']:.2f}s to {cues[-1]['time']:.2f}s")
