#!/usr/bin/env python3
"""Crew: run the parts of a piece in parallel on coding agents from different providers.

One agent orchestrates (any of them: Claude Code, Codex, Antigravity, Gemini CLI, Kiro); `cutroom crew run` hands each
part to a headless agent CLI, each following a cutroom-* skill, each writing only to its own files. Example:
Claude plans the video, Antigravity draws the diagram, Codex writes the deck, Claude narrates, all at once.

  cutroom crew runtimes                    agent CLIs found on this machine and the command each one runs
  cutroom crew example [-o crew.json]      a commented batch to start from
  cutroom crew run <crew.json> [--dry-run] [--max 4] [--only id,id]
  cutroom crew materialize <crew.json>     write the code blocks a task returned as text (from its log)

Batch (JSON, the paths relative to "root", by default the folder of the batch file):
  {"root": "/path/to/piece",                   the piece folder ($J); agents run there
   "defaults": {"runtime": "claude", "profile": "balanced"},
   "tasks": [{"id": "diagram", "runtime": "agy", "skill": "cutroom-diagram", "model": "...", "profile": "fast",
              "prompt": "Draw the architecture of ... into out/architecture.html",
              "writes": ["src/diagram/**", "out/architecture.*"],
              "timeout": 1800, "mode": "...", "skip_permissions": false}]}

  runtime    claude | codex | agy (Antigravity CLI) | gemini (Gemini CLI) | kiro (Kiro CLI)
  skill      cutroom-* skill the agent must follow (its SKILL.md path is put in the prompt)
  model      exact model id; or `profile` (fast | balanced | quality, or your own) looked up in config.json
             crew.profiles.<profile>.<runtime>; no model = the CLI's default
  writes     glob patterns this task may create or edit; two tasks may not overlap (checked before running)

Every task gets the cutroom conventions, its skill, the piece folder and an isolation rule in its prompt. Full
output goes to <batch folder>/logs/<id>.log. If an agent answers with code in text instead of writing files,
the code blocks are written to the files named before them, inside `writes` only.
"""
import argparse
import concurrent.futures
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutroom_home  # noqa: E402

HOME = cutroom_home.home()
SKILL_DIRS = {
    "claude": Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "skills",
    "codex": Path.home() / ".agents" / "skills",
    "agy": Path.home() / ".gemini" / "antigravity" / "skills",
    "gemini": Path.home() / ".gemini" / "antigravity" / "skills",
    "kiro": Path.home() / ".kiro" / "skills",
}
BINARIES = {"claude": ["claude"], "codex": ["codex"], "agy": ["agy", "antigravity"], "gemini": ["gemini"],
            "kiro": ["kiro-cli", "kiro"]}
DEFAULT_PROFILES = {  # model ids change often: override in config.json crew.profiles
    "fast": {"claude": "haiku", "agy": None, "gemini": None, "codex": None, "kiro": None},
    "balanced": {"claude": "sonnet", "agy": None, "gemini": None, "codex": None, "kiro": None},
    "quality": {"claude": "opus", "agy": None, "gemini": None, "codex": None, "kiro": None},
}

EXAMPLE = {
    "root": ".",
    "defaults": {"runtime": "claude", "profile": "balanced"},
    "tasks": [
        {"id": "narration", "runtime": "claude", "skill": "cutroom-voice",
         "prompt": "Generate the narration from src/SCRIPT.md (cutroom script speech, then tts) into work/narration.wav.",
         "writes": ["work/narration.*", "src/speech.txt", "src/pronounce.json"]},
        {"id": "diagram", "runtime": "agy", "skill": "cutroom-diagram",
         "prompt": "Draw the system described in src/SCRIPT.md, scene 3, as out/architecture.html and a PNG.",
         "writes": ["src/diagram/**", "work/diagram/**", "out/architecture.*"]},
        {"id": "deck", "runtime": "codex", "skill": "cutroom-deck",
         "prompt": "Build the deck for scenes marked 'slide N' in src/SCRIPT.md; data in src/results.json.",
         "writes": ["src/deck.py", "out/deck*", "work/preview/**"]},
    ],
}


def config():
    p = HOME / "config.json"
    return json.loads(p.read_text()) if p.exists() else {}


def binary(runtime):
    for b in BINARIES.get(runtime, []):
        if shutil.which(b):
            return shutil.which(b)
    return None


def model_for(task, defaults):
    if task.get("model"):
        return task["model"]
    profile = task.get("profile") or defaults.get("profile")
    if not profile:
        return None
    profiles = dict(DEFAULT_PROFILES)
    profiles.update(config().get("crew", {}).get("profiles", {}))
    return (profiles.get(profile) or {}).get(task["runtime"])


def skill_path(runtime, skill):
    for d in [SKILL_DIRS.get(runtime)] + list(SKILL_DIRS.values()):
        if d and (d / skill / "SKILL.md").exists():
            return d / skill / "SKILL.md"
    return None


def prompt_for(task, root):
    parts = [f"You are one agent of a cutroom crew working in parallel on the piece folder {root}.",
             f"Read the conventions first: {HOME / 'harness' / 'conventions.md'}."]
    if task.get("skill"):
        sp = skill_path(task["runtime"], task["skill"])
        parts.append(f"Follow the skill {task['skill']}: {sp}." if sp else
                     f"Follow the skill {task['skill']} (install it with install.py if your agent does not list it).")
    parts.append("Use this piece folder; do not create a new one with `cutroom job`. Do not ask questions: decide, "
                 "state your assumptions at the end, and finish the task.")
    parts.append(task["prompt"])
    if task.get("writes"):
        parts.append("PARALLEL ISOLATION RULE: create or edit files only inside: " + ", ".join(task["writes"]) +
                     ". Other agents are writing the rest at the same time. Read anything; write only there.")
    return "\n\n".join(parts)


def command(task, defaults, root):
    rt = task["runtime"]
    exe = binary(rt) or BINARIES.get(rt, [rt])[0]
    prompt = prompt_for(task, root)
    model = model_for(task, defaults)
    skip = task.get("skip_permissions", defaults.get("skip_permissions", False))
    if rt == "claude":
        cmd = [exe, "-p", prompt, "--permission-mode", task.get("mode", "acceptEdits"), "--add-dir", str(HOME)]
        if model:
            cmd += ["--model", model]
        if skip:
            cmd.append("--dangerously-skip-permissions")
    elif rt == "codex":
        cmd = [exe, "exec", "-C", str(root), "--skip-git-repo-check",
               "--dangerously-bypass-approvals-and-sandbox" if skip else "--full-auto"]
        if model:
            cmd += ["-m", model]
        cmd.append(prompt)
    elif rt == "agy":
        cmd = [exe, "-p", prompt, "--print-timeout", f"{task.get('timeout', 0)}s", "--add-dir", str(HOME)]
        if task.get("mode"):
            cmd += ["--mode", task["mode"]]
        if model:
            cmd += ["--model", model]
        if skip:
            cmd.append("--dangerously-skip-permissions")
    elif rt == "gemini":
        cmd = [exe, "-p", prompt, "--approval-mode", "yolo" if skip else task.get("mode", "auto_edit"),
               "--include-directories", str(HOME)]
        if model:
            cmd += ["-m", model]
    elif rt == "kiro":
        cmd = [exe, "chat", "--no-interactive"] + (["--trust-all-tools"] if skip or task.get("mode") == "trust" else []) + [prompt]
        if model:
            cmd[2:2] = ["--model", model]
    else:
        raise SystemExit(f"unknown runtime in [{task['id']}]: {rt} (claude, codex, agy, gemini, kiro)")
    return cmd


def overlaps(tasks):
    """Pairs of tasks whose `writes` patterns may cover the same file."""
    def covers(a, b):
        ba, bb = a.split("*")[0], b.split("*")[0]
        return (a == b or fnmatch.fnmatch(b, a) or fnmatch.fnmatch(a, b)
                or ("*" in a and bb.startswith(ba)) or ("*" in b and ba.startswith(bb)))
    found = []
    for i, t1 in enumerate(tasks):
        for t2 in tasks[i + 1:]:
            for a in t1.get("writes", []):
                for b in t2.get("writes", []):
                    if covers(a, b):
                        found.append(f"[{t1['id']}] {a}  ×  [{t2['id']}] {b}")
    return found


CITED = re.compile(r"[`\[(]?((?:[\w.\-]+/)*[\w.\-]+\.(?:svg|py|html|json|md|css|js|mjs|txt|srt|csv))")
FENCE = re.compile(r"^```[\w-]*\s*$")


def _allowed(path, writes, root):
    for pat in writes:
        cands = [path] if "/" in path else [str(Path(pat.split("*")[0]).parent / path), str(Path(pat).parent / path)]
        for c in cands:
            c = c.replace("\\", "/")
            if fnmatch.fnmatch(c, pat) or c == pat:
                return root / c
    return None


def materialize(text, writes, root):
    """Write the code blocks an agent returned as text: each block goes to the last allowed path cited before it."""
    written, last, inside, lines, lang = [], None, False, [], ""
    for line in text.splitlines():
        if FENCE.match(line.strip()) and not inside:
            inside, lines, lang = True, [], line.strip()[3:].strip().lower()
            continue
        if inside and line.strip() == "```":
            inside = False
            if lang in ("bash", "sh", "shell", "console", "zsh", "text", "powershell") and last and last.suffix != ".sh":
                continue
            if last and lines:
                last.parent.mkdir(parents=True, exist_ok=True)
                last.write_text("\n".join(lines) + "\n", encoding="utf-8")
                written.append(last)
                last = None
            continue
        if inside:
            lines.append(line)
            continue
        for hit in CITED.findall(line):
            dest = _allowed(hit.lstrip("./"), writes, root)
            if dest:
                last = dest
    return written


def wrote_something(task, root, since):
    for pat in task.get("writes", []):
        for p in root.glob(pat):
            if p.is_file() and p.stat().st_mtime >= since:
                return True
    return False


def run_task(task, defaults, root, logs):
    log = logs / f"{task['id']}.log"
    t0 = time.time()
    try:
        res = subprocess.run(command(task, defaults, root), capture_output=True, text=True, cwd=root,
                             timeout=task.get("timeout") or None)
        code, out, err = res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired as e:
        code, out, err = 124, e.stdout or "", f"timeout after {task.get('timeout')} s"
    except FileNotFoundError as e:
        code, out, err = 127, "", str(e)
    log.write_text(f"$ runtime={task['runtime']} exit={code} seconds={time.time() - t0:.0f}\n\n--- stdout ---\n{out}\n"
                   f"--- stderr ---\n{err}", encoding="utf-8")
    note = ""
    if code == 0 and task.get("writes") and not wrote_something(task, root, t0):
        got = materialize(out if isinstance(out, str) else out.decode(), task["writes"], root)
        note = f" · materialized {len(got)} file(s) from the reply" if got else " · wrote nothing"
    return task["id"], code, log, time.time() - t0, note


def load(path):
    p = Path(path).resolve()
    batch = json.loads(p.read_text(encoding="utf-8"))
    root = (p.parent / batch.get("root", ".")).resolve()
    defaults = batch.get("defaults", {})
    tasks = batch.get("tasks") or batch.get("tarefas") or []
    for t in tasks:
        t.setdefault("runtime", defaults.get("runtime", "claude"))
        t.setdefault("writes", t.pop("pode_escrever", []) if "pode_escrever" in t else [])
        if "id" not in t or "prompt" not in t:
            raise SystemExit("every task needs an id and a prompt")
    ids = [t["id"] for t in tasks]
    if len(set(ids)) != len(ids):
        raise SystemExit("task ids must be unique")
    return p, root, defaults, tasks


def cmd_runtimes(_):
    for rt in BINARIES:
        b = binary(rt)
        skills = SKILL_DIRS[rt]
        n = len(list(skills.glob("cutroom-*"))) if skills.is_dir() else 0
        print(f"{'✓' if b else '·'} {rt:<7} {b or 'not found':<45} cutroom skills in {skills}: {n}")
    print("\nModel profiles (config.json crew.profiles overrides):")
    profiles = dict(DEFAULT_PROFILES)
    profiles.update(config().get("crew", {}).get("profiles", {}))
    for name, p in profiles.items():
        print(f"  {name:<10} " + ", ".join(f"{k}={v}" for k, v in p.items() if v))


def cmd_example(a):
    text = json.dumps(EXAMPLE, indent=2) + "\n"
    if a.output:
        Path(a.output).write_text(text)
        print(a.output)
    else:
        sys.stdout.write(text)


def cmd_run(a):
    path, root, defaults, tasks = load(a.batch)
    if a.only:
        keep = set(a.only.split(","))
        tasks = [t for t in tasks if t["id"] in keep]
    print(f"=== cutroom crew: {len(tasks)} task(s) in {root} ===")
    for t in tasks:
        print(f"  • [{t['id']}] {t['runtime']} · skill={t.get('skill', '-')} · model={model_for(t, defaults) or 'default'}"
              f" · writes={t.get('writes', [])}")
    missing = sorted({t["runtime"] for t in tasks if not binary(t["runtime"])})
    clash = overlaps(tasks)
    if clash:
        print("✗ write partitions overlap (two tasks could edit the same file):\n  " + "\n  ".join(clash))
        return 2
    if a.dry_run:
        for t in tasks:
            cmd = command(t, defaults, root)
            print("  $ " + " ".join("<prompt>" if len(c) > 120 else c for c in cmd))
        if missing:
            print(f"! not installed: {', '.join(missing)}")
        return 0
    if missing:
        print(f"✗ agent CLI not found for: {', '.join(missing)} (see `cutroom crew runtimes`)")
        return 2
    logs = path.parent / "logs"
    logs.mkdir(exist_ok=True)
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(a.max, len(tasks)))) as ex:
        futs = [ex.submit(run_task, t, defaults, root, logs) for t in tasks]
        for f in concurrent.futures.as_completed(futs):
            tid, code, log, secs, note = f.result()
            failures += code != 0
            print(f"{'✓' if code == 0 else '✗'} [{tid}] exit={code} in {secs:.0f} s{note} · log: {log}", flush=True)
    print("Now review every part: open the outputs, run each skill's checks, and fix what the agents left.")
    return 1 if failures else 0


def cmd_materialize(a):
    path, root, _, tasks = load(a.batch)
    logs = path.parent / "logs"
    for t in tasks:
        log = logs / f"{t['id']}.log"
        if not log.exists():
            print(f"  · [{t['id']}] no log")
            continue
        got = materialize(log.read_text(encoding="utf-8"), t.get("writes", []), root)
        print(f"  {'✓' if got else '·'} [{t['id']}] {len(got)} file(s): " + ", ".join(str(p.relative_to(root)) for p in got))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cutroom crew", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("runtimes").set_defaults(fn=cmd_runtimes)
    s = sub.add_parser("example"); s.add_argument("-o", "--output"); s.set_defaults(fn=cmd_example)
    s = sub.add_parser("run"); s.add_argument("batch"); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--max", type=int, default=4); s.add_argument("--only"); s.set_defaults(fn=cmd_run)
    s = sub.add_parser("materialize"); s.add_argument("batch"); s.set_defaults(fn=cmd_materialize)
    a = ap.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
