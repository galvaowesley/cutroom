"""Where cutroom lives, on Linux, macOS and Windows.

The home folder holds the harness copy, environments, models, brands, voices and config.json. It is resolved in
this order:
  1. the CUTROOM_HOME environment variable (the shortcuts in bin/ always set it);
  2. the pointer file written by `install.py --home <dir>`: ~/.config/cutroom/home (Linux, macOS) or
     %APPDATA%\\cutroom\\home (Windows), so the harness can live anywhere, e.g. ~/Documents/cutroom;
  3. the default: ~/.local/share/cutroom (Linux, macOS) or %LOCALAPPDATA%\\cutroom (Windows).
Pieces (the output of every skill) go to `output_dir` in config.json, chosen separately.
"""
import os
import sys
from pathlib import Path

WINDOWS = os.name == "nt"
MAC = sys.platform == "darwin"


def default_home():
    if WINDOWS:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "cutroom"
    return Path.home() / ".local" / "share" / "cutroom"


def pointer_file():
    if WINDOWS:
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "cutroom" / "home"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "cutroom" / "home"


def home():
    env = os.environ.get("CUTROOM_HOME")
    if env:
        return Path(env).expanduser()
    p = pointer_file()
    if p.exists():
        text = p.read_text(encoding="utf-8").strip()
        if text:
            return Path(text).expanduser()
    return default_home()


def env_bin(home_dir, env, tool):
    """Executable inside a uv environment: bin/<tool> on Unix, Scripts\\<tool>.exe on Windows."""
    base = Path(home_dir) / "envs" / env
    if WINDOWS:
        return base / "Scripts" / (tool if tool.endswith(".exe") else tool + ".exe")
    return base / "bin" / tool


def documents():
    if WINDOWS:
        return Path.home() / "Documents"
    try:
        import subprocess
        r = subprocess.run(["xdg-user-dir", "DOCUMENTS"], capture_output=True, text=True, timeout=5)
        d = r.stdout.strip()
        if r.returncode == 0 and d and Path(d) != Path.home():
            return Path(d)
    except (OSError, ValueError):
        pass
    return Path.home() / "Documents"
