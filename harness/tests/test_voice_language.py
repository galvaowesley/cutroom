"""A preset voice speaks its own language, whatever the configured language is. Run: cutroom-python harness/tests/test_voice_language.py

This is the bug that gave pf_dora an American accent: the config language (en) was used to phonemize Portuguese text.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cutroom_voice as v  # noqa: E402

EXPECT = {"a": "en-us", "b": "en-gb", "e": "es", "f": "fr-fr", "h": "hi", "i": "it", "j": "ja", "p": "pt-br", "z": "cmn"}
failures = []
for cfg_lang in ("en", "pt-BR", "ja"):
    v.config = lambda cfg_lang=cfg_lang: {"language": cfg_lang}      # the configured language must not matter
    for name in v.PRESETS:
        got = v.kokoro_lang(v.resolve(name))
        if got != EXPECT[name[0]]:
            failures.append(f"config language {cfg_lang}: {name} -> {got}, expected {EXPECT[name[0]]}")
    if v.kokoro_lang(v.resolve("pf_dora@1.05")) != "pt-br":
        failures.append(f"config language {cfg_lang}: pf_dora@1.05 not pt-br")
    if v.kokoro_lang(v.resolve("af_heart*0.6+bf_emma*0.4")) != "en-us":
        failures.append(f"config language {cfg_lang}: blend of English voices not en-us")
    if v.kokoro_lang(v.resolve("pf_dora", "es")) != "es":
        failures.append("explicit --lang must still win")
print("\n".join(failures) or f"ok: {len(v.PRESETS)} presets x 3 configured languages")
sys.exit(1 if failures else 0)
