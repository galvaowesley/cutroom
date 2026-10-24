#!/usr/bin/env python3
"""cutroom: catalog, opt-in installation and diagnostics for the cutroom-* media skills.

Nothing is installed without a choice. `catalog` shows each skill, the tool behind it and what it downloads;
`setup <component>` without --yes only prints the plan; with --yes it downloads what the component needs and
copies its skill into the skill folder of each agent chosen in install.py (Claude Code, Cursor, Codex, Antigravity, Kiro).

Everything lives in the cutroom home, outside agent and project folders: ~/.local/share/cutroom on Linux and macOS,
%LOCALAPPDATA%\\cutroom on Windows, or any folder chosen with `install.py --home <dir>` (see cutroom_home.py):
  harness/      this script, cutroom_brand.py, cutroom_voice.py, cutroom_script.py, cutroom_deck/, record_html.mjs,
                conventions.md, the environment locks and brands/ (built-in brands), copied by install.py
  brands/       brands you create or import (`cutroom brand new|add`); they survive reinstalls
  voices/       voice profiles and cloned voices (`voice add|clone`)
  env.sh        defaults (PATH, Chrome, telemetry off, cloud keys unset); skills run `. env.sh`
  env.ps1       the same for Windows PowerShell (`. env.ps1`)
  bin/          shortcuts (.cmd on Windows): cutroom, tts, voice, deck, docling, docling-python, manimgx,
                cutroom-python, hyperframes, archify, record-html, earshot
  envs/<name>   Python environments (uv), locked by harness/envs/<name>/uv.lock
  node/         HyperFrames CLI at the pinned version
  upstream/     official skills of each tool, cloned at the pinned tag (read by the cutroom-* skills)
  models/       weights downloaded by the harness (Kokoro; Chatterbox under models/hf; earshot under models/earshot)
  config.json   output folder, language, brand and default voice
  source        path of the repository clone (written by install.py), where skills are copied from
  agents        skill folders of the chosen agents, one per line (written by install.py)

Commands:
  catalog [--json]           skills, capabilities, tools, downloads and prerequisites
  doctor [--json]            prerequisites and installed components
  setup <comp...> [--yes]    install components and their skills (without --yes: plan only)
  remove <comp...> [--yes]   remove components (and the skill, when no other component of it is left)
  job <title> [--reuse]      create a piece folder (<output_dir>/<YYYY-MM-DD>-<slug>/{src,work,out}) and print it
  paths [--json]             paths the skills use
  config [key [value]]       read or change config.json (output_dir, language)
  brand ...                  brands and design systems (see `cutroom brand --help`)
  voice ...                  voice profiles and cloning (see `cutroom voice --help`)
  script ...                 check and export SCRIPT.md (see `cutroom script --help`)
  deck ...                   build, check and preview slide decks (see `cutroom deck --help`)
  render ...                 HTML to PNG/JPG/PDF/SVG at platform sizes (see `cutroom render --help`)
  edit ...                   ffmpeg post-production recipes (see `cutroom edit --help`)
  crew ...                   run parts of a piece in parallel on Claude, Cursor, Codex, Antigravity, Gemini or Kiro CLIs
  refresh                    regenerate env.sh and bin/ (install.py runs it)
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request

HARNESS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HARNESS)
import cutroom_home  # noqa: E402

HOME = str(cutroom_home.home())
WINDOWS = cutroom_home.WINDOWS
ENVS_SRC = os.path.join(HARNESS, "envs")
PYTHON = {"extract": "3.13", "media": "3.13", "clone": "3.12", "sound": "3.13"}

# Pinned versions. To upgrade: change them here (and the locks in envs/), test, open a PR.
UPSTREAM = {
    "manimgx": ("academa-labs/manimgx", "v0.1.1", ["skills/manimgx"]),
    "archify": ("tt-a1i/archify", "v3.2.0", ["archify"]),
    "hyperframes": ("heygen-com/hyperframes", "v0.8.183", ["skills"]),
    "anatomy": ("wheresryan22/anatomy", "v1.1.0", None),
    "hairline": ("lucasmarkes/hairline", "v0.5.1", ["skills"]),
    "logo": ("kaankiziltug/logo-design-skill", "v1.4.5", ["skills/logo-design"]),
    "earshot": ("Leonxlnx/earshot", "v0.4.0", ["skills", "docs"]),
}
HYPERFRAMES_NPM = "0.8.183"
PLAYWRIGHT_NPM = "1.64.1"  # record-html and Hairline's checks; drives the system Chrome
KOKORO_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
KOKORO_FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
DOCLING_MODELS = ["layout", "tableformer", "picture_classifier", "rapidocr"]  # the rest downloads on demand

SKILLS = {
    "cutroom-extract": "PDF, DOCX, PPTX, XLSX, HTML and images to clean Markdown/JSON before the LLM reads them "
                       "(tables, reading order, OCR). The base for reports built from documents.",
    "cutroom-diagram": "Interactive, self-contained HTML diagrams: architecture, flow, sequence, data flow, ERD, "
                       "timeline. Ready to publish or export as PNG/SVG.",
    "cutroom-math": "Scripted math and code videos in Python (3Blue1Brown style): formulas, plots, 3D, code typed "
                    "line by line, narration in sync and captions.",
    "cutroom-motion": "Video and motion graphics from HTML/CSS/GSAP: explainers, launches, PR videos, animated "
                      "slides, captions. Renders mp4, webm, gif.",
    "cutroom-voice": "Local narration in many languages: Kokoro presets, voice blends and saved profiles; local "
                     "voice cloning with consent (Chatterbox).",
    "cutroom-iso3d": "Animated, interactive isometric figures that explain a concept as a machine (Anatomy) or as "
                     "a single line (Hairline). SVG/HTML.",
    "cutroom-deck": "16:9 PDF decks in the active brand, on any subject: the message in the title and "
                    "illustrations computed from the data. Also self-contained HTML.",
    "cutroom-graphic": "Static graphics in the brand: social posts and stories, thumbnails, OG images, posters, "
                       "banners, infographics, certificates. HTML rendered to PNG, JPG, WebP or PDF at platform sizes.",
    "cutroom-logo": "Logo design from brief to production files: concepts, SVG craft, 16 px and one-color tests, "
                    "presentation boards and export variants, then installed into a cutroom brand.",
    "cutroom-sound": "Sound effects and audio ears for coding agents: 252-sound procedural/fitted bank and film kits "
                     "(sfx/kit), cue-timed video mixing, sound synthesis in code (forge/fit), and listening/sync "
                     "critique for existing videos (timeline, sheet, critique, measure).",
    "cutroom-edit": "Post-production toolbox on ffmpeg: trim, concat, narration and music mix with ducking, loudness, "
                    "burned captions, reframe to 9:16 or 1:1, watermark, GIF, contact sheets, web compression.",
}
# Always installed by install.py: they download nothing and the others depend on them.
BASE = {
    "cutroom-init": "Catalog, opt-in installation, diagnostics and removal of the components.",
    "cutroom-studio": "Orchestrates the other skills to produce a complete piece.",
    "cutroom-script": "Standard script (facts with sources, arc, scenes, speech, pronunciation) for video, "
                      "narration and decks; checked by `cutroom script`.",
    "cutroom-brand": "Builds a brand and design system from the material you give it (logos, images, fonts, "
                     "statements, documents) and switches between brands.",
}

COMPONENTS = {
    "extract": {
        "skill": "cutroom-extract", "tool": "Docling 2.141 (MIT)",
        "downloads": "Python environment with CPU torch (1.5 GB) + layout, table, figure and OCR models (0.8 GB)",
        "size": "~2.3 GB", "needs": ["uv"],
    },
    "docling-mcp": {
        "skill": "cutroom-extract", "tool": "docling-mcp 3.3 (MIT)", "optional": True,
        "downloads": "nothing: registers the 'docling' MCP server in Claude Code, using the extract environment",
        "size": "0", "needs": ["claude"], "after": ["extract"],
    },
    "math": {
        "skill": "cutroom-math", "tool": "ManimGX 0.1.1 (MIT; wheels bundle x264, GPL)",
        "downloads": "Python environment 'media' (ManimGX ships ffmpeg, fonts and Typst)",
        "size": "~400 MB", "needs": ["uv"],
    },
    "voice": {
        "skill": "cutroom-voice", "tool": "Kokoro-82M via kokoro-onnx (Apache-2.0)",
        "downloads": "Python environment 'media' (shared with math) + Kokoro v1.0 model",
        "size": "~400 MB + 340 MB", "needs": ["uv"],
    },
    "voice-clone": {
        "skill": "cutroom-voice", "tool": "Chatterbox Multilingual 0.1.7 (MIT), 23 languages", "optional": True,
        "downloads": "Python environment 'clone' with torch (~1 GB) + Chatterbox weights from Hugging Face (~3 GB)",
        "size": "~4.5 GB", "needs": ["uv", "ffmpeg"], "after": ["voice"],
    },
    "motion": {
        "skill": "cutroom-motion", "tool": "HyperFrames 0.8.183 (Apache-2.0)",
        "downloads": "HyperFrames CLI (npm) + 21 official skills; uses the system Chrome and ffmpeg",
        "size": "~150 MB", "needs": ["node22", "chrome", "ffmpeg"],
    },
    "diagram": {
        "skill": "cutroom-diagram", "tool": "Archify 3.2 (MIT)",
        "downloads": "official skill and dependency-free Node CLI + playwright-core (to record GIF/video)",
        "size": "~40 MB", "needs": ["node", "chrome", "ffmpeg"],
    },
    "deck": {
        "skill": "cutroom-deck", "tool": "cutroom_deck (this repository, standard library only)",
        "downloads": "nothing: the library ships with the harness; prints PDF and previews with Chrome",
        "size": "0", "needs": ["chrome"],
    },
    "graphic": {
        "skill": "cutroom-graphic", "tool": "cutroom render (this repository) on the system Chrome",
        "downloads": "nothing: HTML templates and the renderer ship with the harness",
        "size": "0", "needs": ["chrome"],
    },
    "edit": {
        "skill": "cutroom-edit", "tool": "cutroom edit (this repository) on the system ffmpeg",
        "downloads": "nothing: recipes ship with the harness",
        "size": "0", "needs": ["ffmpeg"],
    },
    "logo": {
        "skill": "cutroom-logo", "tool": "logo-design skill 1.4.5 (MIT), 1,400+ reference logos",
        "downloads": "official skill, dependency-free Python scripts and the reference library",
        "size": "~13 MB", "needs": ["git", "chrome"],
    },
    "iso3d": {
        "skill": "cutroom-iso3d", "tool": "Anatomy 1.1 + Hairline 0.5.1 (MIT)",
        "downloads": "official skills and dependency-free Node kits + playwright-core (checks and GIF/video)",
        "size": "~30 MB", "needs": ["node", "chrome", "ffmpeg"],
    },
    "sound": {
        "skill": "cutroom-sound", "tool": "earshot 0.4.0 (MIT, by Leon Lin)",
        "downloads": "Python environment 'sound' with earshot (252 procedural/fitted sounds, 0 models needed for sfx/kit/measure; "
                     "optional CLAP + AST listening models ~1.1 GB via `earshot doctor --fetch`)",
        "size": "~1.5 GB (+ ~1.1 GB listening models on demand)", "needs": ["uv", "ffmpeg"],
    },
    "earshot-mcp": {
        "skill": "cutroom-sound", "tool": "earshot MCP server 0.4.0 (MIT)", "optional": True,
        "downloads": "nothing: registers the 'earshot' MCP server in Claude Code, using the sound environment",
        "size": "0", "needs": ["claude"], "after": ["sound"],
    },
}


def run(cmd, check=True, env=None):
    print("$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, text=True, env=env)
    if check and r.returncode != 0:
        raise SystemExit(f"failed ({r.returncode}): {' '.join(cmd)}")
    return r


def out(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def version_tuple(s):
    return tuple(int(x) for x in re.findall(r"\d+", s or "")[:3])


# --- prerequisites -------------------------------------------------------------------------------

def node_bins():
    """Folders with a `node`, newest first: the one on PATH and nvm's (nvm-windows: NVM_HOME)."""
    found = []
    p = shutil.which("node")
    if p:
        found.append((version_tuple(out([p, "--version"])), os.path.dirname(p)))
    if WINDOWS and os.environ.get("NVM_HOME"):
        for v in os.listdir(os.environ["NVM_HOME"]):
            if os.path.exists(os.path.join(os.environ["NVM_HOME"], v, "node.exe")):
                found.append((version_tuple(v), os.path.join(os.environ["NVM_HOME"], v)))
    nvm = os.path.expanduser("~/.nvm/versions/node")
    if os.path.isdir(nvm):
        for v in os.listdir(nvm):
            b = os.path.join(nvm, v, "bin")
            if os.path.exists(os.path.join(b, "node")):
                found.append((version_tuple(v), b))
    return sorted(set(found), reverse=True)


def node_bin(min_major):
    for v, b in node_bins():
        if v and v[0] >= min_major:
            return b, ".".join(map(str, v))
    return None, None


def chrome_path():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    import cutroom_brand
    return next((c for c in cutroom_brand.chrome_candidates() if os.path.exists(c)), None)


WINGET = {"ffmpeg": "Gyan.FFmpeg", "git": "Git.Git", "node": "OpenJS.NodeJS.LTS", "chrome": "Google.Chrome"}


def install_hint(pkg):
    if WINDOWS:
        return f"winget install {WINGET.get(pkg, pkg)}"
    if sys.platform == "darwin":
        return f"brew install {pkg}"
    return f"sudo apt install {pkg}  (or your distribution's package manager)"


def prereqs():
    n22, n22v = node_bin(22)
    n18, n18v = node_bin(18)
    chrome = chrome_path()
    return {
        "uv": {"ok": bool(shutil.which("uv")), "info": out(["uv", "--version"]),
               "fix": 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"' if WINDOWS
               else "curl -LsSf https://astral.sh/uv/install.py | sh"},
        "git": {"ok": bool(shutil.which("git")), "info": out(["git", "--version"]), "fix": install_hint("git")},
        "node": {"ok": bool(n18), "info": n18v and f"v{n18v} in {n18}", "fix": install_hint("node") if WINDOWS
                 else "install Node 22 (nvm install 22)"},
        "node22": {"ok": bool(n22), "info": n22v and f"v{n22v} in {n22}",
                   "fix": install_hint("node") if WINDOWS
                   else "nvm install 22  (your default node stays; the harness finds 22 by itself)"},
        "chrome": {"ok": bool(chrome), "info": chrome, "fix": install_hint("chrome") if WINDOWS
                   else "install Google Chrome or Chromium"},
        "ffmpeg": {"ok": bool(shutil.which("ffmpeg")), "info": (out(["ffmpeg", "-version"]) or "").split("\n")[0] or None,
                   "fix": install_hint("ffmpeg")},
        "claude": {"ok": bool(shutil.which("claude")), "info": shutil.which("claude"), "fix": "install the Claude Code CLI"},
        "gpu": {"ok": bool(shutil.which("nvidia-smi")) or sys.platform == "darwin",
                "info": "Apple Silicon (MPS)" if sys.platform == "darwin" else
                out(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]),
                "fix": "optional: without a GPU everything runs on CPU, slower"},
    }


# --- component state -----------------------------------------------------------------------------

def up_dir(name):
    return os.path.join(HOME, "upstream", name)


def up_tag(name):
    return out(["git", "-C", up_dir(name), "describe", "--tags", "--exact-match", "HEAD"])


def env_bin(env, tool):
    return str(cutroom_home.env_bin(HOME, env, tool))


def env_has(env, module):
    py = env_bin(env, "python")
    probe = f"import importlib.util,sys; sys.exit(importlib.util.find_spec('{module}') is None)"
    return os.path.exists(py) and out([py, "-c", probe]) is not None


def hf_model_dir():
    return os.path.join(HOME, "models", "hf", "hub", "models--ResembleAI--chatterbox")


def status(comp):
    """(installed, detail)"""
    if comp == "extract":
        models = os.path.expanduser("~/.cache/docling/models")
        return os.path.exists(env_bin("extract", "docling")), "models in ~/.cache/docling" if os.path.isdir(models) else "no models"
    if comp == "docling-mcp":
        conf = out(["claude", "mcp", "get", "docling"], timeout=30)
        return bool(conf and "docling-mcp-server" in conf), "MCP server 'docling' (user scope)"
    if comp == "math":
        return os.path.exists(env_bin("media", "manimgx")) and up_tag("manimgx") == UPSTREAM["manimgx"][1], UPSTREAM["manimgx"][1]
    if comp == "voice":
        models = all(os.path.exists(os.path.join(HOME, "models", "kokoro", f)) for f in KOKORO_FILES)
        return env_has("media", "kokoro_onnx") and models, "Kokoro v1.0"
    if comp == "voice-clone":
        return env_has("clone", "chatterbox") and os.path.isdir(hf_model_dir()), "Chatterbox Multilingual"
    if comp == "motion":
        pkg = os.path.join(HOME, "node", "node_modules", "hyperframes", "package.json")
        v = json.load(open(pkg))["version"] if os.path.exists(pkg) else None
        return v == HYPERFRAMES_NPM and up_tag("hyperframes") == UPSTREAM["hyperframes"][1], f"hyperframes {v or '-'}"
    if comp == "diagram":
        return up_tag("archify") == UPSTREAM["archify"][1], UPSTREAM["archify"][1]
    if comp == "deck":
        return any(os.path.exists(os.path.join(d, "cutroom-deck", "SKILL.md")) for d in agent_dirs()), "cutroom_deck library"
    if comp == "logo":
        return up_tag("logo") == UPSTREAM["logo"][1], UPSTREAM["logo"][1]
    if comp in ("graphic", "edit"):
        return any(os.path.exists(os.path.join(d, COMPONENTS[comp]["skill"], "SKILL.md")) for d in agent_dirs()), "harness"
    if comp == "iso3d":
        ok = up_tag("anatomy") == UPSTREAM["anatomy"][1] and up_tag("hairline") == UPSTREAM["hairline"][1]
        return ok, f"anatomy {UPSTREAM['anatomy'][1]}, hairline {UPSTREAM['hairline'][1]}"
    if comp == "sound":
        ok = os.path.exists(env_bin("sound", "earshot")) and up_tag("earshot") == UPSTREAM["earshot"][1]
        models = os.path.isdir(os.path.join(HOME, "models", "earshot", "clap"))
        return ok, f"earshot {UPSTREAM['earshot'][1]}" + (" + listening models" if models else " (sfx/kit/measure ready)")
    if comp == "earshot-mcp":
        conf = out(["claude", "mcp", "get", "earshot"], timeout=30)
        return bool(conf and "earshot" in conf), "MCP server 'earshot' (user scope)"
    raise KeyError(comp)


# --- generated files -----------------------------------------------------------------------------

def default_config():
    return {
        "output_dir": str(cutroom_home.documents() / "cutroom"),
        "language": "en",
        "brand": "cutroom",
        "voice": {"default": None},
    }


def load_config():
    path = os.path.join(HOME, "config.json")
    cfg = default_config()
    if os.path.exists(path):
        cfg.update(json.load(open(path)))
    return cfg


def save_config(cfg):
    os.makedirs(HOME, exist_ok=True)
    json.dump(cfg, open(os.path.join(HOME, "config.json"), "w"), indent=2, ensure_ascii=False)


def write_generated():
    """env.sh, bin/, config.json and the active brand's fonts. Idempotent: runs on every setup and remove."""
    os.makedirs(os.path.join(HOME, "bin"), exist_ok=True)
    cfg = load_config()
    save_config(cfg)
    import cutroom_brand
    try:
        m = cutroom_brand.load(cfg["brand"])
    except SystemExit:  # the configured brand was removed: fall back to the default one
        cfg["brand"] = cutroom_brand.DEFAULT_BRAND
        save_config(cfg)
        m = cutroom_brand.load(cfg["brand"])
    cutroom_brand.build(m)
    cutroom_brand.install_fonts(m)
    node = node_bin(22)[0] or node_bin(18)[0]
    chrome = chrome_path()
    write_env_sh(node, chrome)
    write_env_ps1(node, chrome)
    write_shims()


ENV_VARS = [  # (name, value relative to the home, comment)
    ("HF_HOME", "models/hf", "Chatterbox weights stay inside cutroom"),
    ("EARSHOT_HOME", "models/earshot", "earshot CLAP and AST weights stay inside cutroom"),
    ("HAIRLINE_LOOK_CACHE", "cache/playwright", "Hairline and record-html share playwright-core"),
    ("ANATOMY_HOME", "upstream/anatomy", "figure build.mjs scripts import the kit from here"),
]
FLAGS = ["HYPERFRAMES_NO_TELEMETRY", "HYPERFRAMES_SKIP_SKILLS", "ARCHIFY_UPDATE_CHECK_DISABLED"]
CLOUD_KEYS = ["FAL_KEY", "ELEVENLABS_API_KEY", "HEYGEN_API_KEY", "HEYGEN_ACCESS_TOKEN", "GEMINI_API_KEY", "GOOGLE_API_KEY"]


def write_env_sh(node, chrome):
    lines = [
        "# Generated by harness/cutroom.py. Do not edit: run `cutroom refresh` (or install.py) again.",
        f'export CUTROOM_HOME="{HOME}"',
        f'export PATH="$CUTROOM_HOME/bin{":" + node if node else ""}:$PATH"',
        f'export PYTHONPATH="$CUTROOM_HOME/harness${{PYTHONPATH:+:$PYTHONPATH}}"',
    ]
    lines += [f'export {k}="$CUTROOM_HOME/{v}"  # {c}' for k, v, c in ENV_VARS]
    lines += [f"export {k}=1" for k in FLAGS]
    lines += ["# Nothing goes to the cloud unasked: without these keys, tools fall back to their local paths.",
              "# To use a service on purpose, run the command without env.sh, with the person aware of it.",
              "unset " + " ".join(CLOUD_KEYS)]
    if os.path.exists(env_bin("media", "python")):
        lines.append('export HYPERFRAMES_PYTHON="' + env_bin("media", "python") + '"')
    if chrome:
        lines += [f'export CHROME_PATH="{chrome}"', f'export ARCHIFY_CHROME="{chrome}"']
    open(os.path.join(HOME, "env.sh"), "w", newline="\n").write("\n".join(lines) + "\n")


def write_env_ps1(node, chrome):
    """PowerShell twin of env.sh. Written on every OS, so a shared home works from Windows and Unix alike."""
    sep = ";" if WINDOWS else ":"
    lines = [
        "# Generated by harness/cutroom.py. Do not edit: run `cutroom refresh` (or install.py) again.",
        f'$env:CUTROOM_HOME = "{HOME}"',
        f'$env:PATH = "{os.path.join(HOME, "bin")}{sep + node if node else ""}{sep}$env:PATH"',
        f'$env:PYTHONPATH = "{os.path.join(HOME, "harness")}{sep}$env:PYTHONPATH"',
    ]
    lines += [f'$env:{k} = "{os.path.join(HOME, *v.split("/"))}"  # {c}' for k, v, c in ENV_VARS]
    lines += [f'$env:{k} = "1"' for k in FLAGS]
    lines += ["# Nothing goes to the cloud unasked.", *[f"Remove-Item Env:{k} -ErrorAction SilentlyContinue" for k in CLOUD_KEYS]]
    if os.path.exists(env_bin("media", "python")):
        lines.append(f'$env:HYPERFRAMES_PYTHON = "{env_bin("media", "python")}"')
    if chrome:
        lines += [f'$env:CHROME_PATH = "{chrome}"', f'$env:ARCHIFY_CHROME = "{chrome}"']
    open(os.path.join(HOME, "env.ps1"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def shim_table():
    """name: (component or None, file that must exist, command as an argv list)."""
    lib = os.path.join(HOME, "harness")
    py3 = sys.executable or "python3"
    media_py = env_bin("media", "python")
    hf_bin = os.path.join(HOME, "node", "node_modules", ".bin", "hyperframes" + (".cmd" if WINDOWS else ""))
    archify = os.path.join(up_dir("archify"), "archify", "bin", "archify.mjs")
    pw = os.path.join(HOME, "cache", "playwright", "node_modules", "playwright-core")
    return {
        "cutroom": (None, os.path.join(lib, "cutroom.py"), [py3, os.path.join(lib, "cutroom.py")]),
        "deck": (None, os.path.join(lib, "cutroom_deck", "__main__.py"), [py3, "-m", "cutroom_deck"]),
        "docling": ("extract", env_bin("extract", "docling"), [env_bin("extract", "docling")]),
        "docling-tools": ("extract", env_bin("extract", "docling-tools"), [env_bin("extract", "docling-tools")]),
        "docling-python": ("extract", env_bin("extract", "python"), [env_bin("extract", "python")]),
        "docling-mcp-server": ("docling-mcp", env_bin("extract", "docling-mcp-server"), [env_bin("extract", "docling-mcp-server")]),
        "manimgx": ("math", env_bin("media", "manimgx"), [env_bin("media", "manimgx")]),
        "cutroom-python": ("voice", media_py, [media_py]),
        "tts": ("voice", media_py, [media_py, os.path.join(lib, "cutroom_voice.py"), "speak"]),
        "voice": ("voice", media_py, [media_py, os.path.join(lib, "cutroom_voice.py")]),
        "hyperframes": ("motion", hf_bin, [hf_bin]),
        "archify": ("diagram", archify, ["node", archify]),
        "record-html": ("diagram", pw, ["node", os.path.join(lib, "record_html.mjs")]),
        "earshot": ("sound", env_bin("sound", "earshot"), [env_bin("sound", "earshot")]),
    }


def write_shims():
    bindir = os.path.join(HOME, "bin")
    for f in os.listdir(bindir):  # drop shortcuts from older layouts
        if os.path.splitext(f)[0] not in shim_table():
            os.remove(os.path.join(bindir, f))
    for name, (comp, target, argv) in shim_table().items():
        missing = (f'cutroom: {name} is not installed. Use the cutroom-init skill or run: cutroom setup {comp}'
                   if comp else "")
        if WINDOWS:
            body = ["@echo off", f'call :env 2>nul', f'set "CUTROOM_HOME={HOME}"',
                    f'set "PYTHONPATH={os.path.join(HOME, "harness")};%PYTHONPATH%"',
                    *[f'set "{k}={os.path.join(HOME, *v.split("/"))}"' for k, v, _ in ENV_VARS],
                    *[f'set "{k}=1"' for k in FLAGS], *[f'set "{k}="' for k in CLOUD_KEYS],
                    f'set "PATH={bindir};%PATH%"']
            if chrome_path():
                body.append(f'set "CHROME_PATH={chrome_path()}"')
            if comp:
                body.append(f'if not exist "{target}" (echo {missing} 1>&2 & exit /b 127)')
            body.append(" ".join(f'"{x}"' for x in argv) + " %*")
            body = [l for l in body if not l.startswith("call :env")]
            open(os.path.join(bindir, name + ".cmd"), "w", newline="\r\n").write("\n".join(body) + "\n")
            continue
        body = ["#!/bin/sh", f'. "{HOME}/env.sh"']
        if comp:
            body.append(f'[ -e "{target}" ] || {{ echo "{missing}" >&2; exit 127; }}')
        body.append("exec " + " ".join(f'"{x}"' if " " in x or "$" in x else x for x in argv) + ' "$@"')
        p = os.path.join(bindir, name)
        open(p, "w", newline="\n").write("\n".join(body) + "\n")
        os.chmod(p, 0o755)


# --- skills --------------------------------------------------------------------------------------

def agent_dirs():
    """Skill folders of the agents chosen in install.py (default: Claude Code only)."""
    p = os.path.join(HOME, "agents")
    dirs = [l.strip() for l in open(p) if l.strip()] if os.path.exists(p) else []
    return dirs or [os.path.expanduser("~/.claude/skills")]


def source_skills():
    """skills/ of the repository clone: next to this script when running from the clone, or the one install.py wrote."""
    repo = os.path.dirname(HARNESS)
    if os.path.exists(os.path.join(repo, "install.py")):
        return os.path.join(repo, "skills")
    p = os.path.join(HOME, "source")
    if os.path.exists(p):
        s = os.path.join(open(p).read().strip(), "skills")
        if os.path.isdir(s):
            return s
    raise SystemExit("cutroom clone not found. Run ./install.py in the clone and try again.")


DEFAULT_HOME_TEXT = "~/.local/share/cutroom"


def render_skill_text(text):
    """Skills are written for the default Unix home; point them at the real home (and PowerShell on Windows)."""
    home = HOME.replace("\\", "/")
    if WINDOWS:
        text = text.replace(f". {DEFAULT_HOME_TEXT}/env.sh && ", f'. "{home}/env.ps1"; ')
        text = text.replace(f"{DEFAULT_HOME_TEXT}/env.sh", f"{home}/env.ps1")
    if os.path.normpath(os.path.expanduser(DEFAULT_HOME_TEXT)) != os.path.normpath(HOME):
        text = text.replace(DEFAULT_HOME_TEXT, home)
    return text


def copy_skill(name):
    src = os.path.join(source_skills(), name)
    for d in agent_dirs():
        dst = os.path.join(d, name)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        for root, _, files in os.walk(dst):
            for f in files:
                if f.endswith(".md"):
                    p = os.path.join(root, f)
                    t = open(p, encoding="utf-8").read()
                    r = render_skill_text(t)
                    if r != t:
                        open(p, "w", encoding="utf-8").write(r)
        print(f"✓ skill {name} → {dst}")


def drop_skill_if_unused(name, removing=None):
    if any(COMPONENTS[c]["skill"] == name and c != removing and status(c)[0] for c in COMPONENTS):
        return
    for d in agent_dirs():
        if os.path.isdir(os.path.join(d, name)):
            shutil.rmtree(os.path.join(d, name))
            print(f"• skill {name} removed from {d}")


# --- installation --------------------------------------------------------------------------------

def fetch_upstream(name):
    repo, tag, sparse = UPSTREAM[name]
    dest = up_dir(name)
    if up_tag(name) == tag:
        print(f"• {name} {tag} already in {dest}")
        return
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    cmd = ["git", "-c", "advice.detachedHead=false", "clone", "-q", "--depth", "1", "--branch", tag]
    if sparse:
        cmd += ["--filter=blob:none", "--sparse"]
    run(cmd + [f"https://github.com/{repo}.git", dest])
    if sparse:
        run(["git", "-C", dest, "sparse-checkout", "set"] + sparse)


def uv_sync(env):
    e = dict(os.environ, UV_PROJECT_ENVIRONMENT=os.path.join(HOME, "envs", env))
    run(["uv", "sync", "--frozen", "--project", os.path.join(ENVS_SRC, env), "--python", PYTHON[env]], env=e)


def download(url, dest):
    if os.path.exists(dest):
        print(f"• {os.path.basename(dest)} already downloaded")
        return
    print(f"↓ {url}", flush=True)
    tmp = dest + ".part"
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    os.replace(tmp, dest)


def install(comp):
    if comp == "extract":
        uv_sync("extract")
        run([env_bin("extract", "docling-tools"), "models", "download"] + DOCLING_MODELS)
    elif comp == "docling-mcp":
        out(["claude", "mcp", "remove", "docling", "-s", "user"])
        run(["claude", "mcp", "add", "--scope", "user", "docling", "-e", "DOCLING_MCP_CONVERSION_MODE=local",
             "--", os.path.join(HOME, "bin", "docling-mcp-server"), "--transport", "stdio"])
    elif comp == "math":
        uv_sync("media")
        fetch_upstream("manimgx")
    elif comp == "voice":
        uv_sync("media")
        d = os.path.join(HOME, "models", "kokoro")
        os.makedirs(d, exist_ok=True)
        for f in KOKORO_FILES:
            download(KOKORO_URL + f, os.path.join(d, f))
    elif comp == "voice-clone":
        uv_sync("clone")
        e = dict(os.environ, HF_HOME=os.path.join(HOME, "models", "hf"))
        run([env_bin("clone", "python"), "-c",
             "from chatterbox.mtl_tts import ChatterboxMultilingualTTS as T; T.from_pretrained(device='cpu'); print('weights ok')"],
            env=e)
    elif comp == "motion":
        e = dict(os.environ, PATH=node_bin(22)[0] + os.pathsep + os.environ["PATH"], HYPERFRAMES_NO_TELEMETRY="1")
        d = os.path.join(HOME, "node")
        os.makedirs(d, exist_ok=True)
        run([npm(), "install", "--prefix", d, "--no-audit", "--no-fund", "--loglevel=error",
             f"hyperframes@{HYPERFRAMES_NPM}"], env=e)
        fetch_upstream("hyperframes")
    elif comp == "diagram":
        fetch_upstream("archify")
        install_playwright()
    elif comp == "iso3d":
        fetch_upstream("anatomy")
        fetch_upstream("hairline")
        install_playwright()
    elif comp == "logo":
        fetch_upstream("logo")
    elif comp == "sound":
        uv_sync("sound")
        fetch_upstream("earshot")
        os.makedirs(os.path.join(HOME, "models", "earshot"), exist_ok=True)
    elif comp == "earshot-mcp":
        out(["claude", "mcp", "remove", "earshot", "-s", "user"])
        run(["claude", "mcp", "add", "--scope", "user", "earshot", "-e",
             f"EARSHOT_HOME={os.path.join(HOME, 'models', 'earshot')}", "--",
             os.path.join(HOME, "bin", "earshot"), "mcp"])
    copy_skill(COMPONENTS[comp]["skill"])


def npm():
    return "npm.cmd" if WINDOWS else "npm"


def install_playwright():
    d = os.path.join(HOME, "cache", "playwright")
    pkg = os.path.join(d, "node_modules", "playwright-core", "package.json")
    if os.path.exists(pkg) and json.load(open(pkg))["version"] == PLAYWRIGHT_NPM:
        return
    os.makedirs(d, exist_ok=True)
    if not os.path.exists(os.path.join(d, "package.json")):
        open(os.path.join(d, "package.json"), "w").write('{ "private": true }\n')
    node = node_bin(22)[0] or node_bin(18)[0]
    e = dict(os.environ, PATH=node + os.pathsep + os.environ["PATH"])
    run([npm(), "install", "--prefix", d, "--no-audit", "--no-fund", "--loglevel=error", f"playwright-core@{PLAYWRIGHT_NPM}"], env=e)


def uninstall(comp):
    others_on_media = [c for c in ("math", "voice") if c != comp and status(c)[0]]
    if comp == "extract":
        shutil.rmtree(os.path.join(HOME, "envs", "extract"), ignore_errors=True)
        print("• docling models stay in ~/.cache/docling (delete by hand if nothing else uses them)")
    elif comp == "docling-mcp":
        run(["claude", "mcp", "remove", "docling", "-s", "user"], check=False)
    elif comp in ("math", "voice"):
        shutil.rmtree(up_dir("manimgx") if comp == "math" else os.path.join(HOME, "models", "kokoro"), ignore_errors=True)
        if not others_on_media:
            shutil.rmtree(os.path.join(HOME, "envs", "media"), ignore_errors=True)
    elif comp == "voice-clone":
        shutil.rmtree(os.path.join(HOME, "envs", "clone"), ignore_errors=True)
        shutil.rmtree(os.path.join(HOME, "models", "hf"), ignore_errors=True)
        print("• cloned voice profiles stay in voices/ (remove them with `voice remove <name>`)")
    elif comp == "motion":
        shutil.rmtree(os.path.join(HOME, "node"), ignore_errors=True)
        shutil.rmtree(up_dir("hyperframes"), ignore_errors=True)
    elif comp == "diagram":
        shutil.rmtree(up_dir("archify"), ignore_errors=True)
    elif comp == "iso3d":
        for d in (up_dir("anatomy"), up_dir("hairline")):
            shutil.rmtree(d, ignore_errors=True)
    elif comp == "logo":
        shutil.rmtree(up_dir("logo"), ignore_errors=True)
    elif comp == "sound":
        shutil.rmtree(os.path.join(HOME, "envs", "sound"), ignore_errors=True)
        shutil.rmtree(up_dir("earshot"), ignore_errors=True)
        shutil.rmtree(os.path.join(HOME, "models", "earshot"), ignore_errors=True)
    elif comp == "earshot-mcp":
        run(["claude", "mcp", "remove", "earshot", "-s", "user"], check=False)
    if comp in ("diagram", "iso3d") and not status("iso3d" if comp == "diagram" else "diagram")[0]:
        shutil.rmtree(os.path.join(HOME, "cache", "playwright"), ignore_errors=True)
    drop_skill_if_unused(COMPONENTS[comp]["skill"], removing=comp)


# --- commands ------------------------------------------------------------------------------------

def check_names(names):
    bad = [n for n in names if n not in COMPONENTS]
    if bad:
        raise SystemExit(f"unknown component: {', '.join(bad)}. Options: {', '.join(COMPONENTS)}")


def free_gb():
    return shutil.disk_usage(HOME if os.path.exists(HOME) else os.path.expanduser("~")).free // (1 << 30)


def skill_installed(skill):
    return any(os.path.exists(os.path.join(d, skill, "SKILL.md")) for d in agent_dirs())


def catalog_rows(pre):
    rows = []
    for skill, what in SKILLS.items():
        comps = []
        for c, info in COMPONENTS.items():
            if info["skill"] != skill:
                continue
            missing = [n for n in info["needs"] if not pre[n]["ok"]]
            comps.append(dict(info, component=c, installed=status(c)[0], missing=missing,
                              missing_fix=[pre[n]["fix"] for n in missing]))
        rows.append({"skill": skill, "what": what, "components": comps, "skill_installed": skill_installed(skill)})
    return rows


def cmd_catalog(a):
    pre = prereqs()
    rows = catalog_rows(pre)
    if a.json:
        base = [{"skill": k, "what": v, "skill_installed": skill_installed(k)} for k, v in BASE.items()]
        print(json.dumps({"free_gb": free_gb(), "base": base, "skills": rows}, indent=2, ensure_ascii=False))
        return
    print(f"cutroom skills (free disk: {free_gb()} GB)\n\nBase (always installed, no download)")
    for skill, what in BASE.items():
        print(f"  {'✓' if skill_installed(skill) else '·'} /{skill}: {what}")
    print("\nBy choice")
    for r in rows:
        print(f"/{r['skill']}  {'(installed)' if r['skill_installed'] else ''}\n  {r['what']}")
        for c in r["components"]:
            mark = "✓" if c["installed"] else ("✗" if c["missing"] else "·")
            opt = " [optional]" if c.get("optional") else ""
            print(f"  {mark} {c['component']}{opt}: {c['tool']}\n      downloads: {c['downloads']} ({c['size']})")
            for m, fix in zip(c["missing"], c["missing_fix"]):
                print(f"      missing {m}: {fix}")
        print()
    print("✓ installed · available ✗ missing prerequisite. Install with: cutroom setup <component...> --yes")


def cmd_doctor(a):
    pre = prereqs()
    comps = {c: dict(zip(("installed", "detail"), status(c)), skill=COMPONENTS[c]["skill"]) for c in COMPONENTS}
    cfg = load_config()
    if a.json:
        print(json.dumps({"home": HOME, "free_gb": free_gb(), "brand": cfg["brand"], "language": cfg["language"],
                          "prereqs": pre, "components": comps}, indent=2, ensure_ascii=False))
        return
    print(f"cutroom in {HOME}  (free disk: {free_gb()} GB) · brand {cfg['brand']} · language {cfg['language']}\n\nPrerequisites")
    for k, v in pre.items():
        print(f"  {'✓' if v['ok'] else '✗'} {k:<8} {v['info'] or ''}" + ("" if v["ok"] else f"   → {v['fix']}"))
    print("\nComponents")
    for c, v in comps.items():
        print(f"  {'✓' if v['installed'] else '·'} {c:<12} {v['detail'] if v['installed'] else 'not installed'}  (/{v['skill']})")


def cmd_setup(a):
    check_names(a.components)
    pre = prereqs()
    order = sorted(set(a.components), key=list(COMPONENTS).index)
    blocked = False
    for c in order:
        info = COMPONENTS[c]
        missing = [(n, pre[n]["fix"]) for n in info["needs"] if not pre[n]["ok"]]
        missing += [(d, f"install component {d} too") for d in info.get("after", []) if d not in order and not status(d)[0]]
        print(f"• {c} → /{info['skill']}: {info['tool']}\n    downloads: {info['downloads']} ({info['size']})")
        for n, fix in missing:
            blocked = True
            print(f"    ✗ missing {n}: {fix}")
    if blocked:
        raise SystemExit(2)
    if not a.yes:
        print(f"\nFree disk: {free_gb()} GB. Plan only: run again with --yes to install.")
        return
    os.makedirs(HOME, exist_ok=True)
    for c in order:
        print(f"\n=== {c} ===", flush=True)
        install(c)
        write_generated()
    print(f"\nDone. Before tool commands: . {HOME}/env.sh")


def cmd_remove(a):
    check_names(a.components)
    for c in a.components:
        print(f"• {c}: {COMPONENTS[c]['tool']} ({COMPONENTS[c]['size']})")
    if not a.yes:
        print("\nPlan only. Run again with --yes to remove.")
        return
    for c in a.components:
        uninstall(c)
    write_generated()


def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60] or "piece"


def cmd_job(a):
    base = os.path.join(os.path.expanduser(load_config()["output_dir"]), f"{dt.date.today():%Y-%m-%d}-{slug(a.title)}")
    path, n = base, 2
    while os.path.exists(path) and not a.reuse:
        path, n = f"{base}-{n}", n + 1
    for sub in ("src", "work", "out"):
        os.makedirs(os.path.join(path, sub), exist_ok=True)
    print(path)


def cmd_paths(a):
    import cutroom_brand
    cfg = load_config()
    p = {
        "home": HOME, "env_sh": os.path.join(HOME, "env.sh"), "bin": os.path.join(HOME, "bin"),
        "config": os.path.join(HOME, "config.json"), "output_dir": os.path.expanduser(cfg["output_dir"]),
        "conventions": os.path.join(HOME, "harness", "conventions.md"),
        "brand": str(cutroom_brand.find(cfg["brand"])), "brands_user": str(cutroom_brand.USER),
        "voices": os.path.join(HOME, "voices"), "agent_skill_dirs": agent_dirs(),
        "kokoro_models": os.path.join(HOME, "models", "kokoro"), "hf_models": os.path.join(HOME, "models", "hf"),
        "earshot_models": os.path.join(HOME, "models", "earshot"),
        "upstream": {n: up_dir(n) for n in UPSTREAM},
    }
    if a.json:
        print(json.dumps(p, indent=2, ensure_ascii=False))
        return
    for k, v in p.items():
        for n, d in (v.items() if isinstance(v, dict) else [(None, ", ".join(v) if isinstance(v, list) else v)]):
            print(f"{k + ('.' + n if n else ''):<22} {d}")


def cmd_config(a):
    cfg = load_config()
    if not a.key:
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return
    if a.value is None:
        v = cfg
        for part in a.key.split("."):
            v = v.get(part) if isinstance(v, dict) else None
        print(json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v)
        return
    if a.key == "brand":
        raise SystemExit("use `cutroom brand use <name>` (it also registers the fonts)")
    if a.key == "voice.default":
        raise SystemExit("use `voice default <name>`")
    if a.key not in ("output_dir", "language"):
        raise SystemExit("settable keys: output_dir, language")
    cfg[a.key] = os.path.expanduser(a.value) if a.key == "output_dir" else a.value
    save_config(cfg)
    print(f"✓ {a.key} = {cfg[a.key]}")


def delegate(module, argv):
    if module == "cutroom_deck":
        env = dict(os.environ, PYTHONPATH=HARNESS + os.pathsep + os.environ.get("PYTHONPATH", ""))
        return subprocess.call([sys.executable, "-m", "cutroom_deck", *argv], env=env)
    if module == "cutroom_voice":
        py = env_bin("media", "python")
        if not os.path.exists(py):
            raise SystemExit("voices need the voice component: cutroom setup voice --yes")
        env = dict(os.environ, PYTHONPATH=HARNESS + os.pathsep + os.environ.get("PYTHONPATH", ""))
        return subprocess.call([py, os.path.join(HARNESS, "cutroom_voice.py"), *argv], env=env)
    mod = __import__(module)
    return mod.main(argv)


DELEGATES = {"brand": "cutroom_brand", "script": "cutroom_script", "deck": "cutroom_deck", "voice": "cutroom_voice",
             "render": "cutroom_render", "edit": "cutroom_edit", "crew": "cutroom_crew"}


def main():
    if len(sys.argv) > 1 and sys.argv[1] in DELEGATES:
        name = DELEGATES
        sys.exit(delegate(name[sys.argv[1]], sys.argv[2:]))
    ap = argparse.ArgumentParser(prog="cutroom", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("catalog", cmd_catalog), ("doctor", cmd_doctor), ("paths", cmd_paths)):
        s = sub.add_parser(name)
        s.add_argument("--json", action="store_true")
        s.set_defaults(fn=fn)
    for name, fn in (("setup", cmd_setup), ("remove", cmd_remove)):
        s = sub.add_parser(name)
        s.add_argument("components", nargs="+")
        s.add_argument("--yes", action="store_true")
        s.set_defaults(fn=fn)
    s = sub.add_parser("refresh")
    s.set_defaults(fn=lambda a: write_generated())
    s = sub.add_parser("job")
    s.add_argument("title")
    s.add_argument("--reuse", action="store_true", help="reuse today's folder if it exists")
    s.set_defaults(fn=cmd_job)
    s = sub.add_parser("config")
    s.add_argument("key", nargs="?")
    s.add_argument("value", nargs="?")
    s.set_defaults(fn=cmd_config)
    for name in DELEGATES:
        sub.add_parser(name, help=f"see `cutroom {name} --help`")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
