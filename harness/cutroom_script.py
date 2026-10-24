#!/usr/bin/env python3
"""Check and take apart the script of the cutroom-* skills (src/SCRIPT.md of a piece).

The format is in skills/cutroom-script/references/format.md: title, briefing table, ## Facts (id, fact, value,
source, period), ## Scenes (### N. Name · 0:00–0:08, or · slide N, with the fields Goal, On screen, Speech, Visual,
Facts and Sync) and ## Pronunciation (written, spoken). Other sections are free and skipped. Portuguese headings and
fields (## Fatos, ## Cenas, ## Pronúncia, Objetivo, Na tela, Fala, Sincronia) are accepted as aliases.
Standard library only (Python >= 3.10). Also `cutroom script ...`.

Commands:
  check <SCRIPT.md> [--wpm N]      check; exit 1 on errors (warnings don't change the exit code)
  speech <SCRIPT.md> [-o speech.txt] [--pronounce pronounce.json]
                                   join the speech in order, without the [sync brackets], one paragraph per scene,
                                   and write the {"written": "spoken"} JSON of the pronunciation table
  timing <SCRIPT.md> [--wpm N]     words, estimated speech and window per scene, and the total

Errors: scene without Goal, On screen or Visual; scene without Speech in video or narration; cited fact missing from
the table; fact without a source.
Warnings: number on screen or in speech that matches no fact's value; "On screen" over ~110 characters; superlative
or alarm word (English and Portuguese lists); estimated speech longer than the scene window by more than 20% (or
filling less than half of it); total duration off target by more than 15%.

Speech is estimated as words / wpm x 60, counting words as written. The total duration is the larger of the end
of the last window and the sum of speech. For speed other than 1.0, use --wpm 155 x speed.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field

WPM = 155  # words per minute, pauses included: Kokoro at 1.0 (references/arcs.md of the cutroom-script skill)
SCREEN_MAX = 110  # characters: two title lines at 32 px
SCENE_SLACK = 0.20
SILENCE_SLACK = 0.50  # silence warning only when speech fills less than half the window
TOTAL_SLACK = 0.15

SUPERLATIVES = re.compile(r"(?<!\w)(" + "|".join([
    r"very", r"extremely", r"huge", r"enormous", r"incredible", r"amazing", r"revolutionary", r"game[- ]changing",
    r"the\s+(?:biggest|best|greatest|largest)", r"drastic(?:ally)?", r"dramatic(?:ally)?", r"critical", r"alarming",
    r"shocking", r"massive", r"(?<!strength )(?<!strengths )powerful", r"unprecedented",
    r"muit[oa]s?", r"extremamente", r"enormes?", r"incr[ií]ve(?:l|is)", r"revolucion[aá]ri[oa]s?",
    r"(?:o|a|os|as)\s+(?:maior|melhor)(?:es)?", r"dr[aá]stic(?:[oa]s?|amente)", r"graves?", r"alarmantes?",
    r"assustador(?:a|es|as)?", r"(?<!ponto )(?<!pontos )fortes?", r"fort[ií]ssim[oa]s?",
]) + r")(?!\w)", re.IGNORECASE)
FIELD = re.compile(r"^\s*[-*+]\s+\*\*([^*]+?)\s*(?::\*\*|\*\*\s*:)\s*(.*)$")
TIME = r"\d+(?::\d{2})+(?:[.,]\d+)?"
NUM = re.compile(r"\d+(?:[.,]\d+)*")
DATE = re.compile(r"(?<!\d)\d{1,2}/\d{1,2}(?:/\d{2,4})?(?!\d)")
WORD = re.compile(r"[^\W_]+(?:[-'’.,][^\W_]+)*")

# Canonical names, with the Portuguese aliases of earlier versions.
SECTIONS = {"facts": "facts", "fatos": "facts", "scenes": "scenes", "slides": "scenes", "cenas": "scenes",
            "pronunciation": "pronunciation", "pronuncia": "pronunciation"}
FIELDS = {"goal": "goal", "objetivo": "goal", "on screen": "on screen", "na tela": "on screen", "speech": "speech",
          "voiceover": "speech", "fala": "speech", "visual": "visual", "facts": "facts", "fatos": "facts",
          "sync": "sync", "sincronia": "sync"}
BRIEF = {"format": "format", "formato": "format", "audience": "audience", "publico": "audience", "goal": "goal",
         "objetivo": "goal", "key message": "key message", "mensagem central": "key message",
         "target duration": "target duration", "duracao alvo": "target duration", "voice": "voice", "voz": "voice",
         "brand": "brand", "marca": "brand", "language": "language", "idioma": "language"}
FACT_COLS = {"id": "id", "fact": "fact", "fato": "fact", "value": "value", "valor": "value", "source": "source",
             "fonte": "source", "period": "period", "periodo": "period"}


@dataclass
class Field:
    line: int
    value: str


@dataclass
class Scene:
    line: int
    number: str
    name: str
    window: str = ""
    start: float | None = None
    end: float | None = None
    fields: dict = field(default_factory=dict)

    def label(self):
        return f"scene {self.number} ({self.name})"

    def value(self, name):
        f = self.fields.get(name)
        return f.value if f else None


@dataclass
class Script:
    title: str = ""
    brief: dict = field(default_factory=dict)
    facts: list = field(default_factory=list)
    scenes: list = field(default_factory=list)
    pronunciation: dict = field(default_factory=dict)


# --- reading -------------------------------------------------------------------------------------

def key(s):
    """Comparable field name: no accents, no bold, lowercase."""
    s = unicodedata.normalize("NFKD", s.replace("*", "").strip().rstrip(":").lower())
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).split())


def cells(line):
    s = line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def seconds(t):
    total = 0.0
    for part in t.replace(",", ".").split(":"):
        total = total * 60 + float(part)
    return total


def new_scene(title, line):
    m = re.match(r"(\d+)\s*[.)]?\s*(.*)", title)
    number, rest = (m.group(1), m.group(2)) if m else ("?", title)
    name, window = (rest.rsplit("·", 1) + [""])[:2] if "·" in rest else (rest, "")
    sc = Scene(line, number, name.strip(), window.strip())
    t = re.fullmatch(rf"({TIME})\s*(?:–|—|-|to|a|até)\s*({TIME})", sc.window)
    if t:
        sc.start, sc.end = seconds(t.group(1)), seconds(t.group(2))
    return sc


def read(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        raise SystemExit(f"could not read {path}: {e.strerror}")
    r = Script()
    section, scene, fld, header = "brief", None, None, None
    for n, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if re.match(r"#\s", s) and not r.title:
            r.title = s[1:].strip()
            continue
        if re.match(r"##\s", s):
            section = SECTIONS.get(key(s[2:]), "other")
            scene = fld = header = None
            continue
        if not s.startswith("|"):
            header = None  # the table ended
        if section == "scenes":
            if re.match(r"###\s", s):
                scene, fld = new_scene(s[3:].strip(), n), None
                r.scenes.append(scene)
            elif scene is not None:
                m = FIELD.match(raw)
                if m:
                    fld = FIELDS.get(key(m.group(1)), key(m.group(1)))
                    scene.fields[fld] = Field(n, m.group(2).strip())
                elif fld and s and raw[:1].isspace():  # indented continuation of the field
                    scene.fields[fld].value = (scene.fields[fld].value + " " + s).strip()
                else:
                    fld = None
            continue
        if not s.startswith("|"):
            continue
        cl = cells(s)
        if all(re.fullmatch(r":?-+:?", c) for c in cl):
            continue
        if section == "brief" and len(cl) >= 2:
            r.brief.setdefault(BRIEF.get(key(cl[0]), key(cl[0])), Field(n, cl[1]))
        elif section == "facts":
            if header is None:
                header = [FACT_COLS.get(key(c), key(c)) for c in cl]
            else:
                r.facts.append(dict(zip(header, cl), line=n))
        elif section == "pronunciation":
            if header is None:
                header = cl
            elif len(cl) >= 2 and cl[0]:
                r.pronunciation[cl[0].strip("`")] = cl[1].strip("`")
    return r


# --- rules ---------------------------------------------------------------------------------------

def empty(v):
    return v is None or not v.strip()


def dash(v):
    """'—' in a field: nothing, on purpose (silent scene, scene without facts)."""
    return v is not None and v.strip() in ("—", "–", "-", "--")


def medium(fmt):
    f = key(fmt or "")
    if "video" in f:
        return "video"
    if any(w in f for w in ("narration", "podcast", "audio", "voice-over", "voiceover", "audiobook", "narracao", "locucao")):
        return "narration"
    if any(w in f for w in ("deck", "slide", "presentation", "pdf", "apresentacao")):
        return "deck"
    return None


def clean_speech(v):
    v = re.sub(r"\[\s*\]", "", v or "").replace("[", "").replace("]", "").replace("**", "").replace("`", "")
    v = " ".join(v.split())
    if len(v) >= 2 and v[0] in "\"“" and v[-1] in "\"”":
        v = v[1:-1].strip()
    return v


def words(speech):
    return len(WORD.findall(speech))


def readings(tok):
    """Possible values of a written number, with decimals. 1,234 may be one thousand two hundred or 1.234."""
    if "," in tok and "." in tok:
        dec = "," if tok.rfind(",") > tok.rfind(".") else "."
        integer, _, frac = tok.rpartition(dec)
        return [(float(integer.replace("." if dec == "," else ",", "") + "." + frac), len(frac))]
    for sep in ",.":
        if sep in tok:
            parts, r = tok.split(sep), []
            if len(parts) == 2:
                r.append((float(parts[0] + "." + parts[1]), len(parts[1])))
            if all(len(p) == 3 for p in parts[1:]):
                r.append((float("".join(parts)), 0))
            return r  # empty for versions (0.27.2)
    return [(float(tok), 0)]


def numbers(text):
    """Numbers on screen or in speech, excluding years, dates, times, versions, code and scene/slide references."""
    text = DATE.sub(" ", re.sub(r"`[^`]*`", " ", text))
    found = []
    for m in NUM.finditer(text):
        tok, i, j = m.group(), m.start(), m.end()
        before, before2 = (text[i - 1] if i else " "), (text[i - 2] if i > 1 else " ")
        after = text[j] if j < len(text) else " "
        if not (before in "x×" and before2.isdigit()) and (before.isalpha() or before in "_.,"):
            continue  # F1, MP3, v0.8 (the 8 of 8x8 stays)
        if (before == "-" and before2.isalnum()) or (after.isalpha() and after not in "x×") or ":" in (before, after):
            continue  # UTF-8, 4K, 3D, 0:08
        if re.fullmatch(r"(19|20)\d\d", tok) or re.search(r"(?:scene|slide|cena)s?\s*$", text[:i], re.IGNORECASE):
            continue
        rd = readings(tok)
        if rd:
            found.append((tok + ("%" if text[j:].lstrip().startswith("%") else ""), rd))
    return found


def matches(text_rd, value_rd):
    """The number in the text is the fact's value, rounded to the text's decimals (and in %: 0.094 matches 9.4%)."""
    return any(abs(v * k - t) <= 0.5 * 10 ** -d + 1e-9 and (t != 0 or v == 0)
               for t, d in text_rd for v, _ in value_rd for k in (1, 100, 0.01))


def target(text):
    """Target duration in seconds (min, max): 60 s, 1:30, 60 to 70 s, 1 min 30 s, 15 min."""
    t = key(text).replace(",", ".")
    times = re.findall(TIME, t)
    if times:
        v = [seconds(x) for x in times[:2]]
        return min(v), max(v)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|a|ate|–|—|-)\s*(\d+(?:\.\d+)?)\s*(min\w*|m|sec\w*|seg\w*|s)(?!\w)", t)
    if m:
        k = 60 if m.group(3).startswith("m") else 1
        return float(m.group(1)) * k, float(m.group(2)) * k
    units = re.findall(r"(\d+(?:\.\d+)?)\s*(h|min\w*|m|sec\w*|seg\w*|s)(?!\w)", t)
    total = sum(float(v) * (3600 if u == "h" else 60 if u.startswith("m") else 1) for v, u in units)
    return (total, total) if units else None


def secs(x):
    s = f"{x:.1f} s"
    return s + f" ({mmss(x)})" if x >= 90 else s


def mmss(x):
    t = round(x)
    return f"{t // 60}:{t % 60:02d}"


def estimated_speech(scene, wpm):
    f = scene.value("speech")
    n = 0 if empty(f) or dash(f) else words(clean_speech(f))
    return n, n / wpm * 60


def check(r, wpm):
    errors, warnings = [], []
    b = r.brief
    for k, name in (("format", "Format"), ("audience", "Audience"), ("goal", "Goal"), ("key message", "Key message")):
        if empty(b[k].value if k in b else None):
            warnings.append((1, f"brief without {name}"))
    fmt = b["format"].value if "format" in b else ""
    kind = medium(fmt)
    if fmt and not kind:
        warnings.append((b["format"].line, f'Format "{fmt}" does not say the medium (deck, video or narration), '
                                           'so Speech was not required'))

    ids = {}
    for f in r.facts:
        i = f.get("id", "").strip()
        if i in ids:
            errors.append((f["line"], f"fact {i} repeated (the first is on line {ids[i]})"))
        ids.setdefault(i, f["line"])
        if empty(f.get("source")) or dash(f.get("source")):
            errors.append((f["line"], f"fact {i or '(no id)'} has no source"))
    values = [readings(m.group()) for f in r.facts for m in NUM.finditer(f.get("value", ""))]

    if not r.scenes:
        errors.append((1, "no scenes: write ## Scenes with ### 1. Name · 0:00–0:08"))
    msg = b.get("key message")
    if msg and SUPERLATIVES.search(msg.value):
        found = ", ".join(f'"{m.group()}"' for m in SUPERLATIVES.finditer(msg.value))
        warnings.append((msg.line, f"superlative or alarm word in the Key message: {found}"))

    speech_sum, end = 0.0, None
    for c in r.scenes:
        if empty(c.value("goal")) or dash(c.value("goal")):
            errors.append((c.line, f"{c.label()} has no **Goal:**"))
        for k, name in (("on screen", "On screen"), ("visual", "Visual")):
            if empty(c.value(k)):
                errors.append((c.line, f"{c.label()} has no **{name}:** (use — if there is nothing, on purpose)"))
        screen, speech = c.fields.get("on screen"), c.fields.get("speech")
        if kind == "deck" and screen and dash(screen.value):
            errors.append((screen.line, f"{c.label()}: slide without a title in **On screen:**"))
        if kind in ("video", "narration") and (speech is None or empty(speech.value)):
            errors.append((c.line, f"{c.label()} has no **Speech:** (the format needs speech; for a silent video "
                                   "scene, use —)"))
        if kind == "narration" and speech and dash(speech.value):
            errors.append((speech.line, f"{c.label()}: narration with a silent scene"))
        cited = c.fields.get("facts")
        for i in re.findall(r"\bF\d+\b", cited.value if cited else ""):
            if i not in ids:
                errors.append((cited.line, f"{c.label()} cites {i}, which is not in ## Facts"))

        for x, where in ((screen, "on screen"), (speech, "in speech")):
            if not x or empty(x.value) or dash(x.value):
                continue
            loose = list(dict.fromkeys(tok for tok, rd in numbers(x.value) if not any(matches(rd, v) for v in values)))
            if loose:
                warnings.append((x.line, f"{c.label()}: number {where} with no fact of that value: {', '.join(loose)}"))
            found = [m.group() for m in SUPERLATIVES.finditer(x.value)]
            if found:
                lst = ", ".join(f'"{w}"' for w in found)
                warnings.append((x.line, f"{c.label()}: superlative or alarm word {where}: {lst} (references/tone.md)"))
        if screen and not dash(screen.value):
            n = len(re.sub(r"[*`]", "", screen.value).strip())
            if n > SCREEN_MAX:
                warnings.append((screen.line, f"{c.label()}: **On screen:** has {n} characters (max. ~{SCREEN_MAX}, "
                                              "2 lines at 32 px)"))
        sync = c.fields.get("sync")
        if sync and speech:
            marked = {key(m) for m in re.findall(r"\[([^\]]+)\]", speech.value)}
            for m in re.findall(r"\[([^\]]+)\]", sync.value):
                if key(m) not in marked:
                    warnings.append((sync.line, f"{c.label()}: [{m}] is in Sync but not in brackets in Speech"))

        if c.window and c.start is None and not re.fullmatch(r"slide\s+\d+", key(c.window)):
            warnings.append((c.line, f'{c.label()}: unreadable window "{c.window}" (use 0:00–0:08 or slide N)'))
        elif kind == "video" and not c.window:
            warnings.append((c.line, f"{c.label()} has no time window (### N. Name · 0:00–0:08)"))
        n, est = estimated_speech(c, wpm)
        speech_sum += est
        if c.start is not None:
            dur = c.end - c.start
            end = max(end or 0.0, c.end)
            if dur <= 0:
                warnings.append((c.line, f"{c.label()}: the window ends before it starts"))
            elif n and (est / dur - 1 > SCENE_SLACK or est / dur - 1 < -SILENCE_SLACK):
                # speech that doesn't fit always warns; silence only past half (animation after speech is common)
                diff = est / dur - 1
                why = "does not fit" if diff > 0 else "leaves silence; check it is on purpose"
                warnings.append((c.line, f"{c.label()}: speech estimated at {secs(est)} ({n} words) for a "
                                         f"{secs(dur)} window ({diff:+.0%}): {why}"))

    d = b.get("target duration")
    text = "" if d is None or dash(d.value) else d.value.strip()
    rng = target(text) if text else None
    total = max(end or 0.0, speech_sum)
    if text and rng is None and "slide" not in key(text):  # "12 slides": a deck that is read
        warnings.append((d.line, f'unreadable Target duration "{d.value}" (e.g. 60 s, 1:30, 60 to 70 s, 15 min)'))
    elif not text and kind in ("video", "narration"):
        warnings.append((1, "brief without Target duration"))
    elif rng and total and not rng[0] * (1 - TOTAL_SLACK) <= total <= rng[1] * (1 + TOTAL_SLACK):
        warnings.append((d.line, f"total duration estimated at {secs(total)}, off the target of {d.value} "
                                 f"(±{TOTAL_SLACK:.0%})"))
    return sorted(errors, key=lambda e: e[0]), sorted(warnings, key=lambda e: e[0])


# --- commands ------------------------------------------------------------------------------------

def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def cmd_check(a):
    errors, warnings = check(read(a.script), a.wpm)
    for n, m in errors:
        print(f"{a.script}:{n}: error: {m}")
    for n, m in warnings:
        print(f"{a.script}:{n}: warning: {m}")
    if errors:
        print(f"{plural(len(errors), 'error')}, {plural(len(warnings), 'warning')}")
        return 1
    print(f"ok: no errors, {plural(len(warnings), 'warning')}")
    return 0


def cmd_speech(a):
    r = read(a.script)
    parts = [clean_speech(c.value("speech")) for c in r.scenes if not empty(c.value("speech")) and not dash(c.value("speech"))]
    if not parts:
        print("no speech in the script", file=sys.stderr)
        return 1
    text = "\n\n".join(parts) + "\n"
    if a.output:
        open(a.output, "w", encoding="utf-8").write(text)
        print(a.output)
    else:
        sys.stdout.write(text)
    if a.pronounce:
        open(a.pronounce, "w", encoding="utf-8").write(json.dumps(r.pronunciation, ensure_ascii=False, indent=2) + "\n")
        print(a.pronounce, file=sys.stdout if a.output else sys.stderr)
        if not r.pronunciation:
            print("the ## Pronunciation table is empty: the JSON is {}", file=sys.stderr)
    voice = r.brief.get("voice")
    if voice and not dash(voice.value) and not empty(voice.value):
        spec = re.split(r"\s+\(|,", voice.value)[0].strip()
        print(f"voice from the brief: {voice.value}  (tts ... --voice \"{spec}\")",
              file=sys.stderr)
    return 0


def cmd_timing(a):
    r = read(a.script)
    rows = [("scene", "words", "speech", "window", "speech/window")]
    total_w, total_s, end = 0, 0.0, None
    for c in r.scenes:
        n, est = estimated_speech(c, a.wpm)
        total_w, total_s = total_w + n, total_s + est
        window, diff = c.window or "—", ""
        if c.start is not None:
            dur = c.end - c.start
            end = max(end or 0.0, c.end)
            window = f"{mmss(c.start)}–{mmss(c.end)} ({secs(dur)})"
            if n and dur > 0:
                diff = f"{est / dur - 1:+.0%}" + (" off" if abs(est / dur - 1) > SCENE_SLACK else "")
        rows.append((f"{c.number}. {c.name}", str(n), secs(est) if n else "—", window, diff))
    rows.append(("total", str(total_w), secs(total_s), f"until {mmss(end)}" if end is not None else "—", ""))
    width = [max(len(r_[i]) for r_ in rows) for i in range(5)]
    for r_ in rows:
        print("  ".join(v.rjust(w) if i in (1, 2) else v.ljust(w) for i, (v, w) in enumerate(zip(r_, width))).rstrip())
    d = r.brief.get("target duration")
    total = max(end or 0.0, total_s)
    print(f"\nestimated duration: {secs(total)}, the larger of the last window's end and the sum of speech")
    print(f"target: {d.value if d and not empty(d.value) else '—'} · {a.wpm:g} words per minute")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cutroom script", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, alias, fn, hlp in (("check", "conferir", cmd_check, "check the script; exit 1 on errors"),
                                 ("speech", "fala", cmd_speech, "join the speech for tts and write the pronunciation JSON"),
                                 ("timing", "tempo", cmd_timing, "words, estimated speech and window per scene")):
        s = sub.add_parser(name, aliases=[alias], help=hlp)
        s.add_argument("script")
        if name == "speech":
            s.add_argument("-o", "--output", help="text file (default: standard output)")
            s.add_argument("--pronounce", "--pronuncia", dest="pronounce", help='{"written": "spoken"} JSON file to write')
        else:
            s.add_argument("--wpm", "--ppm", dest="wpm", type=float, default=WPM, help=f"words per minute (default {WPM})")
        s.set_defaults(func=fn)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
