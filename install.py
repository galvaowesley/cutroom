#!/usr/bin/env python3
"""Install cutroom's entry point for Claude Code, Codex, Antigravity and Kiro, on Linux, macOS or Windows.

Nothing heavy is downloaded here: only the harness (a few MB, with the built-in brands) and the base skills
(cutroom-init, cutroom-studio, cutroom-script, cutroom-brand). Everything else is chosen later, inside the agent,
with the cutroom-init skill.

  python3 install.py                              detect agents, default home, default output folder
  python3 install.py --agent claude,codex         choose agents (claude, codex, antigravity, kiro)
  python3 install.py --home ~/Documents/cutroom   keep the harness (envs, models, brands, voices) in that folder
  python3 install.py --output ~/Videos/pieces     where pieces are created (`cutroom job`)
  python3 install.py --language pt-BR             default content and narration language
  python3 install.py --uninstall                  remove the cutroom-* skills from the agents (the home stays)

Running it again updates: it recopies the harness and every cutroom-* skill already installed (use after git pull).
The home is remembered (pointer file, see harness/cutroom_home.py), so later runs need no --home.
On Windows run it with `py -3 install.py` or `.\\install.ps1`; on Linux and macOS, `./install.sh` works too.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
import cutroom_home  # noqa: E402

BASE_SKILLS = ["cutroom-init", "cutroom-studio", "cutroom-script", "cutroom-brand"]


def agent_dir(name):
    home = Path.home()
    dirs = {
        "claude": Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")) / "skills",
        "codex": home / ".agents" / "skills",                       # the Codex user skill folder
        "antigravity": home / ".gemini" / "antigravity" / "skills",
        "kiro": home / ".kiro" / "skills",                          # Kiro global skills (IDE and CLI)
    }
    if name not in dirs:
        raise SystemExit(f"unknown agent: {name} (use claude, codex, antigravity or kiro)")
    return dirs[name]


def detect_agents():
    home = Path.home()
    found = []
    if Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")).is_dir() or shutil.which("claude"):
        found.append("claude")
    if (home / ".codex").is_dir() or shutil.which("codex"):
        found.append("codex")
    if (home / ".gemini" / "antigravity").is_dir() or shutil.which("antigravity"):
        found.append("antigravity")
    if (home / ".kiro").is_dir() or shutil.which("kiro") or shutil.which("kiro-cli"):
        found.append("kiro")
    return found


ALL_AGENTS = ["claude", "codex", "antigravity", "kiro"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", help="comma-separated: claude,codex,antigravity,kiro (default: detect)")
    ap.add_argument("--home", help="folder for the harness, environments, models, brands and voices")
    ap.add_argument("--output", help="folder where pieces are created")
    ap.add_argument("--language", help="default content language (en, pt-BR, es...)")
    ap.add_argument("--uninstall", action="store_true")
    a = ap.parse_args()

    if a.uninstall:
        for name in ALL_AGENTS:
            d = agent_dir(name)
            for s in sorted(d.glob("cutroom-*")) if d.is_dir() else []:
                shutil.rmtree(s)
                print(f"• removed {s}")
        h = cutroom_home.home()
        print(f"Downloaded components stay in {h}.")
        print(f"To free the disk: cutroom remove <component> --yes (before uninstalling), then delete {h}.")
        return 0

    if a.home:
        target = Path(a.home).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        old = cutroom_home.home()
        ptr = cutroom_home.pointer_file()
        ptr.parent.mkdir(parents=True, exist_ok=True)
        ptr.write_text(str(target), encoding="utf-8")
        os.environ["CUTROOM_HOME"] = str(target)
        if old.resolve() != target and (old / "harness").is_dir():
            print(f"! the previous home {old} still exists. Components installed there are not moved: run "
                  f"`cutroom setup <component> --yes` again, or move its envs/, models/, brands/ and voices/ by hand.")
    home = cutroom_home.home()
    os.environ["CUTROOM_HOME"] = str(home)

    agents = [x.strip() for x in a.agent.split(",")] if a.agent else detect_agents()
    if not agents:
        raise SystemExit("no agent found; use --agent claude,codex,antigravity,kiro")
    dirs = [agent_dir(x) for x in agents]

    # Neutral engine: scripts, brands, conventions and locks, outside the agent folders.
    home.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(home / "harness", ignore_errors=True)
    shutil.copytree(REPO / "harness", home / "harness",
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "specimen.*", ".venv"))
    (home / "source").write_text(str(REPO), encoding="utf-8")
    (home / "agents").write_text("".join(f"{d}\n" for d in dirs), encoding="utf-8")

    sys.path.insert(0, str(home / "harness"))
    import cutroom  # the copy in the home, so paths point there

    cfg = cutroom.load_config()
    if a.output:
        cfg["output_dir"] = str(Path(a.output).expanduser().resolve())
    if a.language:
        cfg["language"] = a.language
    cutroom.save_config(cfg)

    # Skills: the base ones always; any other cutroom-* already present in some agent, in all of them.
    skills = list(BASE_SKILLS)
    for name in ALL_AGENTS:
        d = agent_dir(name)
        for s in sorted(d.glob("cutroom-*")) if d.is_dir() else []:
            if (REPO / "skills" / s.name).is_dir() and s.name not in skills:
                skills.append(s.name)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    for s in skills:
        cutroom.copy_skill(s)

    cutroom.write_generated()

    shell = (f'. "{home}\\env.ps1"' if cutroom_home.WINDOWS else f". {home}/env.sh")
    print(f"\nHome: {home}\nPieces: {cfg['output_dir']} · language {cfg['language']} · brand {cfg['brand']}")
    print("\nReady. In the agent, call the cutroom-init skill to see the catalog and choose what to install:")
    print("  Claude Code and Kiro: /cutroom-init    Codex: $cutroom-init    Antigravity: ask \"use the cutroom-init skill\"")
    print(f"Or in a terminal: {shell} ; cutroom catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
