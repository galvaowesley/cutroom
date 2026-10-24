#!/usr/bin/env python3
"""Narration for cutroom: voice profiles, a one-line voice spec, Kokoro (local, default) and Chatterbox (local cloning).

Speak (shortcut `tts`):
  tts "Hello, team." -o hello.wav [--voice SPEC] [--speed 1.0] [--lang en] [--pronounce p.json]
  tts -f script.txt -o narration.mp3 --voice narrator          .wav, .mp3 or .m4a (mp3/m4a need ffmpeg)

Manage voices (shortcut `voice`, also `cutroom voice ...`):
  voice list                               saved profiles and the default for each language
  voice presets [--lang pt-BR]             Kokoro preset voices, with notes
  voice audition [--lang en] ["text"] [-o folder] [--voices a,b]
                                           one sample per preset voice of a language, to choose by ear
  voice add NAME SPEC [--speed] [--lang] [--pronounce file.json] [--note "..."] [--default]
                                           save a spec under a name (e.g. `voice add narrator af_heart@0.95`)
  voice clone NAME --ref sample.wav --speaker "Who" --consent "how consent was given" [--lang pt]
            [--ref-text "what the sample says"] [--exaggeration 0.5] [--cfg 0.5] [--default]
                                           clone a voice from 10 to 20 s of clean speech (Chatterbox, local)
  voice test NAME|SPEC ["text"] [-o file]  speak a test sentence with a voice
  voice phonemes NAME|SPEC "text" [--lang]  how the voice's own phonemizer reads each word (check a respelling)
  voice show NAME | voice default NAME [--lang pt-BR] | voice remove NAME

Voice spec, accepted anywhere a voice is asked (--voice, the "Voice" row of SCRIPT.md, manimgx_voice(voice=...)):
  narrator                    a saved profile
  af_heart                    a Kokoro preset; the first letter is the language (a/b English, p Brazilian
                              Portuguese, e Spanish, f French, i Italian, h Hindi, j Japanese, z Mandarin)
  af_heart@1.1                the same, at speed 1.1
  af_heart*0.6+am_adam*0.4    a Kokoro blend (weights normalized): a new voice without cloning
  clone:ana                   a cloned profile (same as `ana`; the prefix only documents intent)
  default (or nothing)        config `voice.default` -> brand narration for the language -> language default

Library (the `manimgx` and `cutroom-python` shortcuts put this folder on PYTHONPATH):
  from cutroom_voice import synth, manimgx_voice
  open("x.wav", "wb").write(synth("Hello", voice="narrator"))
  class Scene(m.Scene):
      voice = manimgx_voice("narrator", pronounce={"ManimGX": "manim G X"})

Pronunciation: {"written": "spoken"} replaces whole words (case-insensitive) in the audio only; captions keep the
written text. Profiles can carry their own dictionary; the one given in the call is applied on top.

Everything runs on this machine. Cloning stores the reference audio and the consent record in the profile folder
(<cutroom home>/voices/NAME/) and never uploads it. Chatterbox adds an inaudible Perth watermark to every
cloned output.
"""
import argparse
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutroom_home  # noqa: E402

HOME = cutroom_home.home()
VOICES = HOME / "voices"
KOKORO_DIR = HOME / "models" / "kokoro"
CLONE_PY = cutroom_home.env_bin(HOME, "clone", "python")
HF_HOME = HOME / "models" / "hf"

KOKORO_LANG = {"a": "en-us", "b": "en-gb", "e": "es", "f": "fr-fr", "h": "hi", "i": "it", "j": "ja", "p": "pt-br",
               "z": "cmn"}
LANG_DEFAULT = {"en": "af_heart", "en-us": "af_heart", "en-gb": "bf_emma", "pt": "pf_dora", "pt-br": "pf_dora",
                "es": "ef_dora", "fr": "ff_siwis", "it": "if_sara", "hi": "hf_alpha", "ja": "jf_alpha",
                "zh": "zf_xiaobei"}
# Kokoro v1.0 presets. Notes summarize the model card grades (A best) and character.
PRESETS = {
    "af_heart": "US female, warm, A grade: the default English narrator",
    "af_bella": "US female, bright and expressive, A-",
    "af_nicole": "US female, soft, close-mic, B-",
    "af_aoede": "US female, calm, C+",
    "af_kore": "US female, even, C+",
    "af_sarah": "US female, clear, C+",
    "af_nova": "US female, C", "af_sky": "US female, C-", "af_alloy": "US female, C", "af_jessica": "US female, D",
    "af_river": "US female, D",
    "am_michael": "US male, steady, C+: good explainer voice",
    "am_fenrir": "US male, deeper, C+",
    "am_puck": "US male, lively, C+",
    "am_echo": "US male, D", "am_eric": "US male, D", "am_liam": "US male, D", "am_onyx": "US male, deep, D",
    "am_santa": "US male, D-", "am_adam": "US male, F+ (useful in blends)",
    "bf_emma": "UK female, composed, B-: the default British narrator",
    "bf_isabella": "UK female, C", "bf_alice": "UK female, D", "bf_lily": "UK female, D",
    "bm_george": "UK male, C", "bm_fable": "UK male, C", "bm_lewis": "UK male, D+", "bm_daniel": "UK male, D",
    "pf_dora": "Brazilian Portuguese female: the default pt-BR narrator",
    "pm_alex": "Brazilian Portuguese male",
    "pm_santa": "Brazilian Portuguese male, lower",
    "ef_dora": "Spanish female", "em_alex": "Spanish male", "em_santa": "Spanish male",
    "ff_siwis": "French female, B-",
    "if_sara": "Italian female, C", "im_nicola": "Italian male, C",
    "hf_alpha": "Hindi female, C", "hf_beta": "Hindi female, C", "hm_omega": "Hindi male, C", "hm_psi": "Hindi male, C",
    "jf_alpha": "Japanese female, C+", "jf_gongitsune": "Japanese female, C", "jf_nezumi": "Japanese female, C-",
    "jf_tebukuro": "Japanese female, C", "jm_kumo": "Japanese male, C-",
    "zf_xiaobei": "Mandarin female, D", "zf_xiaoni": "Mandarin female, D", "zf_xiaoxiao": "Mandarin female, D",
    "zf_xiaoyi": "Mandarin female, D", "zm_yunjian": "Mandarin male, D", "zm_yunxi": "Mandarin male, D",
    "zm_yunxia": "Mandarin male, D", "zm_yunyang": "Mandarin male, D",
}
CLONE_LANGS = {"ar", "da", "de", "el", "en", "es", "fi", "fr", "he", "hi", "it", "ja", "ko", "ms", "nl", "no", "pl",
               "pt", "ru", "sv", "sw", "tr", "zh"}
SAMPLE = {"en": "This is how I sound when I read your script. Numbers like 85.5 percent come out clearly.",
          "pt": "É assim que eu leio o seu roteiro. Números como oitenta e cinco vírgula cinco por cento saem claros.",
          "es": "Así suena tu guion cuando lo leo. Los números, como ochenta y cinco coma cinco por ciento, se entienden.",
          "fr": "Voici comment je lis votre script. Les nombres, comme quatre-vingt-cinq virgule cinq pour cent, restent clairs."}
_kokoro = None
_clone = None


# --- config --------------------------------------------------------------------------------------

def config():
    p = HOME / "config.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_config(cfg):
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")


def lang_key(lang):
    return (lang or "en").lower().replace("_", "-")


def base_lang(lang):
    return lang_key(lang).split("-")[0]


def brand_narration(lang):
    try:
        import cutroom_brand
        n = cutroom_brand.load().get("narration", {})
    except (SystemExit, ImportError, OSError, ValueError):
        return None
    for k, v in n.items():
        if lang_key(k) == lang_key(lang):
            return v
    for k, v in n.items():
        if base_lang(k) == base_lang(lang):
            return v
    return None


# --- voice resolution ----------------------------------------------------------------------------

@dataclass
class Voice:
    engine: str = "kokoro"                 # kokoro | chatterbox
    voice: object = "af_heart"             # kokoro: preset name or [(name, weight)]; chatterbox: reference path
    speed: float = 1.0
    lang: str = "en"
    pronounce: dict = field(default_factory=dict)
    name: str = ""                         # profile name, if any
    exaggeration: float = 0.5
    cfg_weight: float = 0.5

    def key(self):
        """Hashable description, for caches (ManimGX puts the voice in its cache key)."""
        v = self.voice if isinstance(self.voice, str) else tuple(map(tuple, self.voice))
        return (self.engine, v, self.speed, self.lang, tuple(sorted(self.pronounce.items())), self.exaggeration,
                self.cfg_weight)

    def describe(self):
        if self.engine == "chatterbox":
            return f"clone:{self.name} (Chatterbox, {self.lang}, exaggeration {self.exaggeration})"
        v = self.voice if isinstance(self.voice, str) else "+".join(f"{n}*{w:g}" for n, w in self.voice)
        return f"{v}@{self.speed:g} (Kokoro, {self.lang})"


def profile_path(name):
    return VOICES / name / "voice.json"


def load_profile(name):
    p = profile_path(name)
    return json.loads(p.read_text()) if p.exists() else None


def parse_spec(spec, lang=None):
    """Kokoro spec (preset, blend, @speed) -> Voice."""
    speed = None
    if "@" in spec:
        spec, s = spec.rsplit("@", 1)
        speed = float(s)
    parts = [p.strip() for p in spec.split("+") if p.strip()]
    blend = []
    for p in parts:
        n, _, w = p.partition("*")
        n = n.strip()
        if n not in PRESETS and not re.fullmatch(r"[abefhijpz][fm]_[a-z]+", n):
            raise SystemExit(f"unknown voice {n!r}: not a profile (`voice list`) nor a Kokoro preset (`voice presets`)")
        blend.append((n, float(w) if w else 1.0))
    first = blend[0][0]
    v = Voice("kokoro", first if len(blend) == 1 else blend, speed or 1.0, lang or KOKORO_LANG.get(first[0], "en-us"))
    if len(blend) > 1:
        langs = {n[0] for n, _ in blend}
        if len(langs) > 1 and not lang:
            print(f"! blend mixes languages ({', '.join(sorted(langs))}): using {v.lang}; pass --lang to choose",
                  file=sys.stderr)
    return v, speed


def resolve(spec=None, lang=None, speed=None, pronounce=None):
    """Any voice spec -> Voice. Explicit arguments win over the profile, the profile over defaults."""
    cfg_voice = config().get("voice", {})
    explicit_lang = lang
    lang = lang or config().get("language")
    if not spec or spec == "default":
        by_lang = {lang_key(k): v for k, v in (cfg_voice.get("by_language") or {}).items()}
        cand = by_lang.get(lang_key(lang)) or next((v for k, v in by_lang.items() if base_lang(k) == base_lang(lang)), None)
        if not cand and cfg_voice.get("default"):
            cand = cfg_voice["default"]
            if explicit_lang and base_lang(resolve(cand).lang) != base_lang(explicit_lang):
                cand = None  # the default voice speaks another language: use this language's default
        spec = cand or brand_narration(lang or "en") or LANG_DEFAULT.get(lang_key(lang), None) \
            or LANG_DEFAULT.get(base_lang(lang), "af_heart")
    name = spec[6:] if spec.startswith("clone:") else spec.split("@")[0]
    prof = load_profile(name)
    if prof:
        if prof["engine"] == "chatterbox":
            v = Voice("chatterbox", str(VOICES / name / prof["reference"]), prof.get("speed", 1.0),
                      prof.get("lang", "en"), dict(prof.get("pronounce", {})), name,
                      prof.get("exaggeration", 0.5), prof.get("cfg_weight", 0.5))
        else:
            v, _ = parse_spec(prof["spec"], prof.get("lang"))
            v.speed = prof.get("speed", v.speed)
            v.pronounce, v.name = dict(prof.get("pronounce", {})), name
        if "@" in spec:
            v.speed = float(spec.rsplit("@", 1)[1])
    elif spec.startswith("clone:"):
        raise SystemExit(f"no cloned voice named {name!r}: create it with `voice clone {name} --ref ...`")
    else:
        # a preset speaks its own language (pf_dora is Brazilian Portuguese) unless --lang says otherwise; the config
        # language only picks the default voice above, it must not turn a pt-BR voice into an English phonemizer
        v, spec_speed = parse_spec(spec, explicit_lang)
        if spec_speed is None and cfg_voice.get("speed"):
            v.speed = cfg_voice["speed"]
    if speed:
        v.speed = speed
    if explicit_lang and v.engine == "chatterbox":
        v.lang = explicit_lang
    v.pronounce.update(pronounce or {})
    return v


# --- synthesis -----------------------------------------------------------------------------------

def spoken(text, pronounce=None):
    """Apply the pronunciation dictionary (whole words, case-insensitive)."""
    for written, said in (pronounce or {}).items():
        text = re.sub(rf"(?<!\w){re.escape(written)}(?!\w)", said, text, flags=re.IGNORECASE)
    return text


def kokoro():
    global _kokoro
    if _kokoro is None:
        try:
            from kokoro_onnx import Kokoro
        except ImportError:
            raise SystemExit("Kokoro is not installed: run `cutroom setup voice` (or the cutroom-init skill)")
        _kokoro = Kokoro(str(KOKORO_DIR / "kokoro-v1.0.onnx"), str(KOKORO_DIR / "voices-v1.0.bin"))
    return _kokoro


def wav_bytes(samples, rate):
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, samples, rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def kokoro_lang(v):
    """The phonemizer language Kokoro uses for this voice (what `voice phonemes` shows)."""
    return v.lang if v.lang in KOKORO_LANG.values() else {"en": "en-us", "pt": "pt-br", "fr": "fr-fr",
                                                          "zh": "cmn"}.get(base_lang(v.lang), lang_key(v.lang))


def describe_voice(v):
    return v.describe().split(" (")[0]


def kokoro_synth(v, text):
    k = kokoro()
    if isinstance(v.voice, str):
        style = v.voice
    else:
        import numpy as np
        total = sum(w for _, w in v.voice) or 1
        style = sum(k.get_voice_style(n) * (w / total) for n, w in v.voice).astype(np.float32)
    lang = kokoro_lang(v)
    own = KOKORO_LANG.get((v.voice if isinstance(v.voice, str) else v.voice[0][0])[0])
    if own and own.split("-")[0] != lang.split("-")[0]:
        print(f"! {describe_voice(v)} is a {own} voice but the text is read as {lang}: expect a foreign accent. "
              f"Drop --lang, or pass --lang {own}", file=sys.stderr)
    samples, rate = k.create(text, voice=style, speed=v.speed, lang=lang)
    return wav_bytes(samples, rate)


def chunks(text, limit=280):
    """Sentences grouped up to `limit` characters: Chatterbox speaks ~40 s per call at most."""
    sentences = re.split(r"(?<=[.!?…])\s+|\n{2,}", text.strip())
    out, cur = [], ""
    for s in (x.strip() for x in sentences if x.strip()):
        if cur and len(cur) + len(s) + 1 > limit:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    return out + ([cur] if cur else [])


QUIET = {"TRANSFORMERS_VERBOSITY": "error", "HF_HUB_DISABLE_PROGRESS_BARS": "1", "TQDM_DISABLE": "1",
         "PYTHONWARNINGS": "ignore", "TOKENIZERS_PARALLELISM": "false"}


def clone_env():
    env = dict(QUIET, HF_HOME=str(HF_HOME))
    if (HF_HOME / "hub" / "models--ResembleAI--chatterbox").is_dir():
        env["HF_HUB_OFFLINE"] = "1"  # weights are local: no call to the Hub on every line
    return env


def clone_model():
    global _clone
    if _clone is None:
        os.environ.update({k: v for k, v in clone_env().items() if k not in os.environ})
        import warnings
        warnings.filterwarnings("ignore")
        import logging
        logging.disable(logging.WARNING)
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        device = os.environ.get("CUTROOM_CLONE_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
        try:
            _clone = ChatterboxMultilingualTTS.from_pretrained(device=device)
        except Exception:  # some ops are missing on MPS for older torch: fall back to CPU
            _clone = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    return _clone


def chatterbox_synth_local(v, text):
    import numpy as np
    model = clone_model()
    lang = base_lang(v.lang)
    if lang not in CLONE_LANGS:
        raise SystemExit(f"Chatterbox does not speak {v.lang!r}. Languages: {', '.join(sorted(CLONE_LANGS))}")
    pieces, gap = [], np.zeros(int(model.sr * 0.18), dtype=np.float32)
    for i, part in enumerate(chunks(text)):
        wav = model.generate(part, language_id=lang, audio_prompt_path=v.voice if i == 0 else None,
                             exaggeration=v.exaggeration, cfg_weight=v.cfg_weight)
        pieces += [wav.squeeze(0).numpy().astype(np.float32), gap]
    audio = np.concatenate(pieces[:-1]) if pieces else np.zeros(1, dtype=np.float32)
    if abs(v.speed - 1.0) > 1e-3:
        import librosa
        audio = librosa.effects.time_stretch(audio, rate=v.speed)
    return wav_bytes(audio, model.sr)


def chatterbox_synth(v, text):
    try:
        import chatterbox  # noqa: F401  already in the clone environment
        return chatterbox_synth_local(v, text)
    except ImportError:
        pass
    if not CLONE_PY.exists():
        raise SystemExit("voice cloning is not installed: run `cutroom setup voice-clone` (~4.5 GB)")
    with tempfile.TemporaryDirectory() as t:
        req = Path(t) / "req.json"
        req.write_text(json.dumps({"voice": v.__dict__, "text": text}))
        out = Path(t) / "out.wav"
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent), **clone_env())
        r = subprocess.run([str(CLONE_PY), str(Path(__file__).resolve()), "_clone-synth", str(req), str(out)], env=env)
        if r.returncode != 0 or not out.exists():
            raise SystemExit("cloned voice synthesis failed (see the error above)")
        return out.read_bytes()


def synth_voice(v, text):
    text = spoken(text, v.pronounce)
    return chatterbox_synth(v, text) if v.engine == "chatterbox" else kokoro_synth(v, text)


def synth(text, voice=None, speed=None, pronounce=None, lang=None):
    """Text -> WAV bytes. `voice` is any voice spec (see the module docstring)."""
    return synth_voice(resolve(voice, lang, speed, pronounce), text)


def manimgx_voice(voice=None, speed=None, pronounce=None, lang=None):
    """Voice for `voice = ...` in a ManimGX scene. ManimGX caches each line in voice/ and only synthesizes new ones.

    The voice is resolved here, once, so its full description enters ManimGX's cache key: changing the profile or
    the default voice re-synthesizes instead of reusing old audio.
    """
    import manimgx as m

    v = resolve(voice, lang, speed, pronounce)
    key = v.key()  # immutable: ManimGX only puts hashable values in its cache key

    def speak(text, _key=key):
        return m.Speech(synth_voice(v, text), text=text)

    return speak


def write_audio(data, output):
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".wav":
        out.write_bytes(data)
        return out
    if not shutil.which("ffmpeg"):
        raise SystemExit(f"ffmpeg is needed for {out.suffix}: install it, or write .wav")
    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        t.write(data)
        t.flush()
        codec = ["-codec:a", "libmp3lame", "-q:a", "4"] if out.suffix.lower() == ".mp3" else ["-codec:a", "aac", "-b:a", "128k"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", t.name, *codec, str(out)], check=True)
    return out


def duration(path):
    try:
        import soundfile as sf
        info = sf.info(str(path))
        return info.frames / info.samplerate
    except Exception:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True)
        return float(r.stdout.strip() or 0)


# --- profiles ------------------------------------------------------------------------------------

def save_profile(name, data):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
        raise SystemExit("profile name: lowercase letters, digits, - and _")
    if name in PRESETS:
        raise SystemExit(f"{name} is a Kokoro preset name: choose another profile name")
    d = VOICES / name
    d.mkdir(parents=True, exist_ok=True)
    data = dict(data, name=name, updated=dt.date.today().isoformat())
    (d / "voice.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return d


def set_default(name, lang=None):
    cfg = config()
    v = cfg.setdefault("voice", {})
    if lang:
        v.setdefault("by_language", {})[lang_key(lang)] = name
    else:
        v["default"] = name
    save_config(cfg)


def profiles():
    return [json.loads(p.read_text()) for p in sorted(VOICES.glob("*/voice.json"))] if VOICES.is_dir() else []


def convert_reference(src, dst):
    """Any audio -> 24 kHz mono WAV, trimmed to 30 s."""
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "24000", "-t", "30",
                        str(dst)], check=True)
    elif str(src).lower().endswith(".wav"):
        shutil.copy2(src, dst)
    else:
        raise SystemExit("ffmpeg is needed to read this audio format: install it, or pass a .wav")


# --- cli -----------------------------------------------------------------------------------------

def cmd_speak(argv):
    ap = argparse.ArgumentParser(prog="tts", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?")
    ap.add_argument("-f", "--file", help="text file with the script")
    ap.add_argument("-o", "--output", help="output file: .wav, .mp3 or .m4a")
    ap.add_argument("--voice", help="voice spec: profile, preset, preset@speed, blend, clone:name")
    ap.add_argument("--speed", type=float)
    ap.add_argument("--lang", help="language (en, en-gb, pt-BR, es...); default: config, then the voice's own")
    ap.add_argument("--pronounce", "--pronuncia", dest="pronounce", help='JSON {"written": "spoken"} applied before synthesis')
    a = ap.parse_args(argv)
    text = Path(a.file).read_text(encoding="utf-8") if a.file else a.text
    if not text or not a.output:
        ap.error("give the text (or -f file) and -o output")
    pron = json.loads(Path(a.pronounce).read_text(encoding="utf-8")) if a.pronounce else None
    v = resolve(a.voice, a.lang, a.speed, pron)
    out = write_audio(synth_voice(v, text.strip()), a.output)
    print(f"{out} · {duration(out):.2f} s · {v.describe()}")
    return 0


def cmd_manage(argv):
    ap = argparse.ArgumentParser(prog="voice", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("presets"); s.add_argument("--lang")
    s = sub.add_parser("audition"); s.add_argument("text", nargs="?"); s.add_argument("--lang", default=None)
    s.add_argument("-o", "--output", default="voice-audition"); s.add_argument("--voices")
    s = sub.add_parser("add"); s.add_argument("name"); s.add_argument("spec"); s.add_argument("--speed", type=float)
    s.add_argument("--lang"); s.add_argument("--pronounce"); s.add_argument("--note", default=""); s.add_argument("--default", action="store_true")
    s = sub.add_parser("clone"); s.add_argument("name"); s.add_argument("--ref", required=True)
    s.add_argument("--speaker", required=True, help="whose voice this is")
    s.add_argument("--consent", required=True, help="how and when the speaker agreed (stored in the profile)")
    s.add_argument("--ref-text", default="", help="transcript of the reference (kept for the record)")
    s.add_argument("--lang", default=None); s.add_argument("--exaggeration", type=float, default=0.5)
    s.add_argument("--cfg", type=float, default=0.5); s.add_argument("--speed", type=float, default=1.0)
    s.add_argument("--pronounce"); s.add_argument("--default", action="store_true")
    s = sub.add_parser("test"); s.add_argument("name"); s.add_argument("text", nargs="?"); s.add_argument("-o", "--output")
    s.add_argument("--lang")
    s = sub.add_parser("phonemes"); s.add_argument("voice"); s.add_argument("text"); s.add_argument("--lang")
    s = sub.add_parser("show"); s.add_argument("name")
    s = sub.add_parser("default"); s.add_argument("name"); s.add_argument("--lang", help="default for this language only")
    s = sub.add_parser("remove"); s.add_argument("name")
    a = ap.parse_args(argv)
    lang_cfg = config().get("language", "en")

    if a.cmd == "list":
        ps = profiles()
        default = config().get("voice", {}).get("default")
        if a.json:
            print(json.dumps({"default": default, "profiles": ps, "resolved_default": resolve(None).describe()}, indent=2,
                             ensure_ascii=False))
            return 0
        by_lang = config().get("voice", {}).get("by_language") or {}
        print(f"default voice: {default or '(none set)'} → {resolve(None).describe()}")
        for k, v in by_lang.items():
            print(f"  for {k}: {v} → {resolve(v).describe()}")
        print()
        for p in ps:
            what = f"clone of {p['consent']['speaker']}" if p["engine"] == "chatterbox" else p["spec"]
            print(f"{'●' if p['name'] == default else '·'} {p['name']:<16} {what:<28} {p.get('lang', '')}  {p.get('note', '')}")
        if not ps:
            print("no saved profiles. Try `voice presets`, `voice audition`, then `voice add narrator af_heart`.")
    elif a.cmd == "presets":
        for n, note in PRESETS.items():
            if a.lang and KOKORO_LANG.get(n[0], "") .split("-")[0] != base_lang(a.lang):
                continue
            print(f"{n:<14} {KOKORO_LANG[n[0]]:<6} {note}")
        print("\nBlend presets with weights to design a voice: `voice add host af_heart*0.7+bf_emma*0.3`.")
    elif a.cmd == "audition":
        lang = a.lang or lang_cfg
        names = a.voices.split(",") if a.voices else [n for n in PRESETS if KOKORO_LANG[n[0]].split("-")[0] == base_lang(lang)]
        text = a.text or SAMPLE.get(base_lang(lang), SAMPLE["en"])
        out = Path(a.output)
        out.mkdir(parents=True, exist_ok=True)
        for n in names:
            v = resolve(n)
            f = write_audio(synth_voice(v, text), out / f"{n.replace('*', 'x').replace('+', '_')}.wav")
            print(f"{f}  {PRESETS.get(n.split('@')[0], '')}")
        print(f"\nListen, then save the one you like: voice add narrator <voice> --default")
    elif a.cmd == "add":
        v, _ = parse_spec(a.spec, a.lang)
        data = {"engine": "kokoro", "spec": a.spec.split("@")[0], "speed": a.speed or v.speed, "lang": a.lang or v.lang,
                "note": a.note}
        if a.pronounce:
            data["pronounce"] = json.loads(Path(a.pronounce).read_text(encoding="utf-8"))
        d = save_profile(a.name, data)
        if a.default:
            set_default(a.name, a.lang if a.lang and base_lang(a.lang) != base_lang(lang_cfg) else None)
        print(f"✓ {a.name} → {resolve(a.name).describe()}  ({d})")
    elif a.cmd == "clone":
        ref = Path(a.ref).expanduser()
        if not ref.exists():
            raise SystemExit(f"reference not found: {ref}")
        d = VOICES / a.name
        d.mkdir(parents=True, exist_ok=True)
        convert_reference(ref, d / "reference.wav")
        secs = duration(d / "reference.wav")
        if secs < 5:
            print(f"! the reference has {secs:.1f} s: use 10 to 20 s of clean speech for a stable clone", file=sys.stderr)
        lang = base_lang(a.lang or lang_cfg)
        if lang not in CLONE_LANGS:
            raise SystemExit(f"Chatterbox does not speak {lang!r}. Languages: {', '.join(sorted(CLONE_LANGS))}")
        data = {"engine": "chatterbox", "reference": "reference.wav", "reference_seconds": round(secs, 2),
                "reference_text": a.ref_text, "lang": lang, "speed": a.speed, "exaggeration": a.exaggeration,
                "cfg_weight": a.cfg, "consent": {"speaker": a.speaker, "statement": a.consent,
                                                 "recorded": dt.date.today().isoformat()},
                "note": f"cloned from {ref.name}"}
        if a.pronounce:
            data["pronounce"] = json.loads(Path(a.pronounce).read_text(encoding="utf-8"))
        save_profile(a.name, data)
        if a.default:
            set_default(a.name)
        print(f"✓ clone:{a.name} saved in {d} ({secs:.1f} s reference, {lang}). Test it: voice test {a.name}")
    elif a.cmd == "test":
        v = resolve(a.name, a.lang)
        text = a.text or SAMPLE.get(base_lang(v.lang), SAMPLE["en"])
        out = write_audio(synth_voice(v, text), a.output or f"voice-test-{a.name.replace('*', 'x').replace('+', '_')}.wav")
        print(f"{out} · {duration(out):.2f} s · {v.describe()}")
    elif a.cmd == "phonemes":
        v = resolve(a.voice, a.lang)
        if v.engine != "kokoro":
            raise SystemExit("phonemes are shown for Kokoro voices; a cloned voice is not phonemized here")
        from kokoro_onnx.tokenizer import Tokenizer
        lang = kokoro_lang(v)
        tk = Tokenizer()
        print(f"{describe_voice(v)} · phonemizer {lang}")
        for w in a.text.split():
            print(f"  {w:<22} {tk.phonemize(w, lang)}")
    elif a.cmd == "show":
        p = load_profile(a.name)
        print(json.dumps(p, indent=2, ensure_ascii=False) if p else resolve(a.name).describe())
    elif a.cmd == "default":
        resolve(a.name)
        set_default(a.name, a.lang)
        print(f"✓ default voice{' for ' + a.lang if a.lang else ''}: {a.name} → {resolve(None, a.lang).describe()}")
    elif a.cmd == "remove":
        d = VOICES / a.name
        if not d.is_dir():
            raise SystemExit(f"no profile named {a.name}")
        shutil.rmtree(d)
        if config().get("voice", {}).get("default") == a.name:
            set_default(None)
        print(f"✓ removed {a.name} (reference audio included)")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["_clone-synth"]:  # internal: runs inside the clone environment
        req = json.loads(Path(argv[1]).read_text())
        Path(argv[2]).write_bytes(chatterbox_synth_local(Voice(**req["voice"]), req["text"]))
        return 0
    if argv[:1] == ["speak"]:
        return cmd_speak(argv[1:])
    return cmd_manage(argv)


if __name__ == "__main__":
    sys.exit(main())
