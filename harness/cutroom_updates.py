#!/usr/bin/env python3
"""Listen to upstream skill and tool repositories for updates, with manual or pre-approved automatic application.

 Cutroom tracks two groups of upstream repositories:
   1. Official skill/tool repos cloned into <HOME>/upstream/<name> (defined in cutroom.UPSTREAM):
      manimgx, archify, hyperframes, anatomy, hairline, logo, earshot
   2. Core tool and harness repositories (defined in EXTRA_SOURCES):
      cutroom, docling, docling-mcp, kokoro-onnx, chatterbox

Update modes (saved in <HOME>/config.json under "updates"):
  ask   (default) Check upstream releases/commits and suggest updates; applying requires `--yes`
        unless a specific source is listed in `updates.preapproved`.
  auto  Pre-approve automatic updates for all tracked sources when `check --apply-auto` or `watch` runs.
  off   Disable background update checks unless explicitly run with `cutroom updates check`.

Commands:
  cutroom updates check [--source <name...>] [--channel tags|commits] [--cached] [--apply-auto] [--json]
  cutroom updates apply [<source...>] [--all] [--to <ref>] [--update-pins] [--yes] [--json]
  cutroom updates policy [--mode ask|auto|off] [--channel tags|commits] [--interval <hours>]
                         [--approve <source...>] [--revoke <source...>] [--json]
  cutroom updates watch [--interval <minutes>] [--once] [--apply-auto] [--json]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Any

HARNESS = os.path.dirname(os.path.abspath(__file__))
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)

import cutroom  # noqa: E402
import cutroom_home  # noqa: E402

EXTRA_SOURCES: dict[str, tuple[str, str, list[str] | None]] = {
    "cutroom": ("galvaowesley/cutroom", "HEAD", None),
    "docling": ("docling-project/docling", "v2.88.0", None),
    "docling-mcp": ("docling-project/docling-mcp", "v1.5.0", None),
    "kokoro-onnx": ("thewh1teagle/kokoro-onnx", "v0.5.0", None),
    "chatterbox": ("resemble-ai/chatterbox", "v0.1.7", None),
}

SOURCE_META: dict[str, dict[str, str]] = {
    "manimgx": {"skill": "cutroom-math", "component": "math", "kind": "upstream"},
    "archify": {"skill": "cutroom-diagram", "component": "diagram", "kind": "upstream"},
    "hyperframes": {"skill": "cutroom-motion", "component": "motion", "kind": "upstream"},
    "anatomy": {"skill": "cutroom-iso3d", "component": "iso3d", "kind": "upstream"},
    "hairline": {"skill": "cutroom-iso3d", "component": "iso3d", "kind": "upstream"},
    "logo": {"skill": "cutroom-logo", "component": "logo", "kind": "upstream"},
    "earshot": {"skill": "cutroom-sound", "component": "sound", "kind": "upstream"},
    "cutroom": {"skill": "cutroom-init", "component": "harness", "kind": "self"},
    "docling": {"skill": "cutroom-extract", "component": "extract", "kind": "package"},
    "docling-mcp": {"skill": "cutroom-extract", "component": "docling-mcp", "kind": "package"},
    "kokoro-onnx": {"skill": "cutroom-voice", "component": "voice", "kind": "package"},
    "chatterbox": {"skill": "cutroom-voice", "component": "voice-clone", "kind": "package"},
}

DEFAULT_POLICY: dict[str, Any] = {
    "mode": "ask",
    "channel": "tags",
    "interval_hours": 12,
    "preapproved": [],
}

SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def home_dir() -> str:
    return str(cutroom_home.home())


def all_sources() -> dict[str, tuple[str, str, list[str] | None]]:
    merged: dict[str, tuple[str, str, list[str] | None]] = {}
    for name, spec in getattr(cutroom, "UPSTREAM", {}).items():
        merged[name] = (spec[0], spec[1], spec[2])
    for name, spec in EXTRA_SOURCES.items():
        merged.setdefault(name, spec)
    return merged


SOURCES = all_sources()


def source_meta(name: str) -> dict[str, str]:
    if name in SOURCE_META:
        return dict(SOURCE_META[name])
    kind = "upstream" if name in getattr(cutroom, "UPSTREAM", {}) else "package"
    return {"skill": f"cutroom-{name}", "component": name, "kind": kind}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(ts: str | None) -> dt.datetime | None:
    if not ts or not isinstance(ts, str):
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(ts)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except ValueError:
        return None


# --- policy & cache state ------------------------------------------------------------------------

def normalize_policy(raw: dict[str, Any] | None) -> dict[str, Any]:
    pol = dict(DEFAULT_POLICY)
    if isinstance(raw, dict):
        mode = raw.get("mode")
        if mode in ("ask", "auto", "off"):
            pol["mode"] = mode
        channel = raw.get("channel")
        if channel in ("tags", "commits"):
            pol["channel"] = channel
        interval = raw.get("interval_hours")
        if isinstance(interval, (int, float)) and interval > 0:
            pol["interval_hours"] = int(interval) if float(interval).is_integer() else float(interval)
        pre = raw.get("preapproved")
        if isinstance(pre, list):
            seen: list[str] = []
            for item in pre:
                if isinstance(item, str) and item.strip() and item.strip() not in seen:
                    seen.append(item.strip())
            pol["preapproved"] = seen
    return pol


def load_config_full() -> dict[str, Any]:
    path = os.path.join(home_dir(), "config.json")
    cfg = cutroom.default_config()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (OSError, json.JSONDecodeError):
            pass
    return cfg


def save_config_full(cfg: dict[str, Any]) -> None:
    h = home_dir()
    os.makedirs(h, exist_ok=True)
    with open(os.path.join(h, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_policy() -> dict[str, Any]:
    cfg = load_config_full()
    return normalize_policy(cfg.get("updates"))


def save_policy(policy: dict[str, Any]) -> dict[str, Any]:
    norm = normalize_policy(policy)
    cfg = load_config_full()
    cfg["updates"] = norm
    save_config_full(cfg)
    cache_path = updates_cache_path()
    if os.path.exists(cache_path):
        cache = load_updates_cache()
        cache["policy"] = norm
        for sname, srec in cache.get("sources", {}).items():
            if isinstance(srec, dict):
                srec["auto_approved"] = is_preapproved(sname, norm)
        for item in cache.get("pending_updates", []):
            if isinstance(item, dict) and "source" in item:
                item["auto_approved"] = is_preapproved(item["source"], norm)
                item["auto"] = item["auto_approved"]
        save_updates_cache(cache)
    return norm


def is_preapproved(source: str, policy: dict[str, Any] | None = None) -> bool:
    pol = normalize_policy(policy if policy is not None else load_policy())
    if pol["mode"] == "auto":
        return True
    pre = pol.get("preapproved") or []
    return "*" in pre or "all" in pre or source in pre


def updates_cache_path() -> str:
    return os.path.join(home_dir(), "updates.json")


def load_updates_cache() -> dict[str, Any]:
    path = updates_cache_path()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "checked_at": None,
        "policy": load_policy(),
        "sources": {},
        "pending_updates": [],
        "history": [],
    }


def save_updates_cache(cache: dict[str, Any]) -> None:
    h = home_dir()
    os.makedirs(h, exist_ok=True)
    with open(updates_cache_path(), "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def cache_is_fresh(cache: dict[str, Any], interval_hours: float) -> bool:
    checked = parse_iso(cache.get("checked_at"))
    if not checked or not cache.get("sources"):
        return False
    age_hours = (dt.datetime.now(dt.timezone.utc) - checked).total_seconds() / 3600.0
    return age_hours < max(0.01, float(interval_hours))


def cached_summary() -> dict[str, Any]:
    """Lightweight summary from <HOME>/updates.json (no network calls) for `cutroom doctor`."""
    pol = load_policy()
    cache = load_updates_cache()
    available: list[dict[str, Any]] = []
    for item in cache.get("pending_updates") or []:
        if not isinstance(item, dict):
            continue
        src = item.get("source")
        if not src:
            continue
        auto = is_preapproved(src, pol)
        available.append({
            "source": src,
            "skill": item.get("skill") or source_meta(src)["skill"],
            "component": item.get("component") or source_meta(src)["component"],
            "current": item.get("current") or item.get("current_ref"),
            "latest": item.get("latest") or item.get("latest_ref"),
            "auto": auto,
        })
    return {
        "mode": pol["mode"],
        "channel": pol["channel"],
        "interval_hours": pol["interval_hours"],
        "preapproved": list(pol["preapproved"]),
        "checked_at": cache.get("checked_at"),
        "available": available,
    }


# --- version & git helpers -----------------------------------------------------------------------

def parse_semver(tag: str | None) -> tuple[int, int, int, int, str] | None:
    """Return (major, minor, patch, is_stable_flag, prerelease) or None if not semver."""
    if not tag or not isinstance(tag, str):
        return None
    m = SEMVER_RE.match(tag.strip())
    if not m:
        return None
    major = int(m.group(1))
    minor = int(m.group(2))
    patch = int(m.group(3) or 0)
    prerelease = m.group(4) or ""
    # Stable releases sort higher than pre-releases of the same X.Y.Z
    is_stable = 1 if not prerelease else 0
    return (major, minor, patch, is_stable, prerelease)


def is_prerelease_tag(tag: str | None) -> bool:
    parsed = parse_semver(tag)
    return bool(parsed and parsed[3] == 0)


def git_out(cmd: list[str], timeout: int = 15) -> str | None:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, env=env)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def upstream_dir(name: str) -> str:
    return os.path.join(home_dir(), "upstream", name)


def cutroom_repo_dir() -> str | None:
    source_ptr = os.path.join(home_dir(), "source")
    if os.path.exists(source_ptr):
        try:
            candidate = open(source_ptr, encoding="utf-8").read().strip()
            if candidate and os.path.isdir(candidate):
                return candidate
        except OSError:
            pass
    repo = os.path.dirname(HARNESS)
    if os.path.exists(os.path.join(repo, "install.py")) or os.path.isdir(os.path.join(repo, ".git")):
        return repo
    return None


def read_ref_marker(dest: str) -> dict[str, str] | None:
    marker = os.path.join(dest, ".cutroom-ref")
    if not os.path.exists(marker):
        return None
    try:
        raw = open(marker, encoding="utf-8").read().strip()
        if not raw:
            return None
        if raw.startswith("{"):
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if v is not None}
        return {"ref": raw}
    except (OSError, json.JSONDecodeError):
        return None


def write_ref_marker(dest: str, ref: str, sha: str | None = None, repo: str | None = None) -> None:
    os.makedirs(dest, exist_ok=True)
    payload = {
        "ref": ref,
        "sha": sha or "",
        "repo": repo or "",
        "updated_at": utc_now_iso(),
    }
    with open(os.path.join(dest, ".cutroom-ref"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def local_source_state(name: str, pinned_ref: str) -> dict[str, Any]:
    """Inspect local installation state for a tracked source."""
    meta = source_meta(name)
    kind = meta["kind"]
    installed = False
    installed_ref: str | None = None
    installed_sha: str | None = None

    if kind == "self":
        repo_dir = cutroom_repo_dir()
        if repo_dir and os.path.isdir(os.path.join(repo_dir, ".git")):
            installed = True
            installed_sha = git_out(["git", "-C", repo_dir, "rev-parse", "HEAD"], timeout=5)
            exact_tag = git_out(["git", "-C", repo_dir, "describe", "--tags", "--exact-match", "HEAD"], timeout=5)
            installed_ref = exact_tag or (installed_sha[:7] if installed_sha else "HEAD")
    else:
        dest = upstream_dir(name)
        marker = read_ref_marker(dest)
        if os.path.isdir(dest):
            installed = True
            installed_sha = git_out(["git", "-C", dest, "rev-parse", "HEAD"], timeout=5)
            exact_tag = git_out(["git", "-C", dest, "describe", "--tags", "--exact-match", "HEAD"], timeout=5)
            desc = exact_tag or git_out(["git", "-C", dest, "describe", "--tags", "--always"], timeout=5)
            if marker and marker.get("ref"):
                installed_ref = marker["ref"]
                if not installed_sha and marker.get("sha"):
                    installed_sha = marker["sha"]
            else:
                installed_ref = exact_tag or desc or (installed_sha[:7] if installed_sha else None)

    current_ref = installed_ref or pinned_ref
    return {
        "installed": installed,
        "installed_ref": installed_ref,
        "installed_sha": installed_sha,
        "pinned_ref": pinned_ref,
        "current_ref": current_ref,
    }


def query_remote(name: str, repo: str, pinned_ref: str, timeout: int = 15) -> dict[str, Any]:
    """Run `git ls-remote` for tags and HEAD against GitHub."""
    url = f"https://github.com/{repo}.git"
    allow_prerelease = is_prerelease_tag(pinned_ref)

    tags_out = git_out(["git", "ls-remote", "--tags", "--refs", url], timeout=timeout)
    head_out = git_out(["git", "ls-remote", url, "HEAD"], timeout=timeout)

    if tags_out is None and head_out is None:
        return {
            "latest_tag": None,
            "latest_tag_sha": None,
            "head_sha": None,
            "error": f"unreachable: {url}",
        }

    best_tuple: tuple[int, int, int, int, str] | None = None
    best_tag: str | None = None
    best_sha: str | None = None
    tag_shas: dict[str, str] = {}

    for line in (tags_out or "").splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        sha, ref = parts[0], parts[1]
        if not ref.startswith("refs/tags/"):
            continue
        tag = ref[len("refs/tags/"):]
        tag_shas[tag] = sha
        parsed = parse_semver(tag)
        if not parsed:
            continue
        if parsed[3] == 0 and not allow_prerelease:
            continue
        if best_tuple is None or parsed > best_tuple:
            best_tuple = parsed
            best_tag = tag
            best_sha = sha

    head_sha: str | None = None
    for line in (head_out or "").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "HEAD":
            head_sha = parts[0]
            break
    if not head_sha and head_out:
        first = head_out.strip().split()
        if first:
            head_sha = first[0]

    return {
        "latest_tag": best_tag,
        "latest_tag_sha": best_sha,
        "head_sha": head_sha,
        "tag_shas": tag_shas,
        "error": None,
    }


def compare_refs(
    current_ref: str,
    installed_sha: str | None,
    pinned_ref: str,
    remote: dict[str, Any],
    channel: str,
) -> tuple[str | None, str | None, bool, str]:
    """Return (latest_ref, latest_sha, update_available, status_label)."""
    if remote.get("error"):
        return (None, None, False, "offline")

    latest_tag = remote.get("latest_tag")
    latest_tag_sha = remote.get("latest_tag_sha")
    head_sha = remote.get("head_sha")
    tag_shas = remote.get("tag_shas") or {}

    effective_channel = channel
    if effective_channel == "tags" and not latest_tag and head_sha:
        effective_channel = "commits"

    if effective_channel == "commits":
        latest_ref = head_sha[:7] if head_sha else None
        latest_sha = head_sha
        if not head_sha:
            return (None, None, False, "unknown")
        local_sha = installed_sha or tag_shas.get(current_ref) or tag_shas.get(pinned_ref)
        if local_sha:
            up = not head_sha.startswith(local_sha[:7]) and not local_sha.startswith(head_sha[:7])
            return (latest_ref, latest_sha, up, "update-available" if up else "up-to-date")
        if SHA_RE.match(current_ref):
            up = not head_sha.startswith(current_ref[:7])
            return (latest_ref, latest_sha, up, "update-available" if up else "up-to-date")
        return (latest_ref, latest_sha, True, "update-available")

    # channel == "tags"
    if not latest_tag:
        return (None, None, False, "up-to-date")

    cur_ver = parse_semver(current_ref)
    lat_ver = parse_semver(latest_tag)
    if cur_ver and lat_ver:
        if lat_ver[:4] > cur_ver[:4]:
            return (latest_tag, latest_tag_sha, True, "update-available")
        if lat_ver[:4] < cur_ver[:4]:
            return (latest_tag, latest_tag_sha, False, "ahead")
        return (latest_tag, latest_tag_sha, False, "up-to-date")

    if current_ref == latest_tag:
        return (latest_tag, latest_tag_sha, False, "up-to-date")
    if installed_sha and latest_tag_sha and installed_sha[:7] == latest_tag_sha[:7]:
        return (latest_tag, latest_tag_sha, False, "up-to-date")
    return (latest_tag, latest_tag_sha, True, "update-available")


def check_sources(
    selected: list[str] | None = None,
    channel: str | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    """Query tracked sources in parallel with ThreadPoolExecutor(max_workers=8) and persist cache."""
    sources_map = all_sources()
    policy = load_policy()
    active_channel = channel or policy["channel"]
    names = selected or list(sources_map.keys())
    unknown = [n for n in names if n not in sources_map]
    if unknown:
        raise SystemExit(f"unknown source(s): {', '.join(unknown)}. Options: {', '.join(sources_map)}")

    local_states = {n: local_source_state(n, sources_map[n][1]) for n in names}
    remote_states: dict[str, dict[str, Any]] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, max(1, len(names)))) as pool:
        futs = {
            pool.submit(query_remote, n, sources_map[n][0], sources_map[n][1], timeout): n
            for n in names
        }
        for fut in concurrent.futures.as_completed(futs):
            n = futs[fut]
            try:
                remote_states[n] = fut.result()
            except Exception as exc:  # pragma: no cover
                remote_states[n] = {
                    "latest_tag": None,
                    "latest_tag_sha": None,
                    "head_sha": None,
                    "error": str(exc),
                }

    cache = load_updates_cache()
    existing_sources = cache.get("sources") if isinstance(cache.get("sources"), dict) else {}
    records: dict[str, dict[str, Any]] = dict(existing_sources)

    for n in names:
        repo, pinned_ref, sparse = sources_map[n]
        meta = source_meta(n)
        loc = local_states[n]
        rem = remote_states[n]
        latest_ref, latest_sha, has_update, status_label = compare_refs(
            loc["current_ref"],
            loc["installed_sha"],
            pinned_ref,
            rem,
            active_channel,
        )
        auto = is_preapproved(n, policy)
        records[n] = {
            "source": n,
            "repo": repo,
            "url": f"https://github.com/{repo}",
            "skill": meta["skill"],
            "component": meta["component"],
            "kind": meta["kind"],
            "sparse_paths": sparse,
            "installed": loc["installed"],
            "installed_ref": loc["installed_ref"],
            "installed_sha": loc["installed_sha"],
            "pinned_ref": pinned_ref,
            "current_ref": loc["current_ref"],
            "latest_tag": rem.get("latest_tag"),
            "latest_tag_sha": rem.get("latest_tag_sha"),
            "head_sha": rem.get("head_sha"),
            "latest_ref": latest_ref,
            "latest_sha": latest_sha,
            "channel": active_channel,
            "update_available": has_update,
            "auto_approved": auto,
            "status": status_label,
            "error": rem.get("error"),
        }

    pending: list[dict[str, Any]] = []
    for n, rec in records.items():
        if isinstance(rec, dict) and rec.get("update_available"):
            pending.append({
                "source": n,
                "skill": rec.get("skill"),
                "component": rec.get("component"),
                "repo": rec.get("repo"),
                "url": rec.get("url"),
                "kind": rec.get("kind"),
                "current": rec.get("current_ref"),
                "latest": rec.get("latest_ref"),
                "latest_sha": rec.get("latest_sha"),
                "auto_approved": is_preapproved(n, policy),
                "auto": is_preapproved(n, policy),
            })

    checked_at = utc_now_iso()
    cache["checked_at"] = checked_at
    cache["policy"] = policy
    cache["sources"] = records
    cache["pending_updates"] = pending
    cache.setdefault("history", [])
    save_updates_cache(cache)
    return cache


# --- applying updates ----------------------------------------------------------------------------

def clone_or_checkout_upstream(
    name: str,
    repo: str,
    target_ref: str,
    sparse: list[str] | None,
) -> str | None:
    """Clone <repo> at <target_ref> (tag, branch, or commit SHA) into <HOME>/upstream/<name>."""
    dest = upstream_dir(name)
    url = f"https://github.com/{repo}.git"
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    is_sha = bool(SHA_RE.match(target_ref))
    cloned = False
    if not is_sha:
        cmd = ["git", "-c", "advice.detachedHead=false", "clone", "-q", "--depth", "1", "--branch", target_ref]
        if sparse:
            cmd += ["--filter=blob:none", "--sparse"]
        cmd += [url, dest]
        r = subprocess.run(cmd, text=True, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        if r.returncode == 0:
            cloned = True
            if sparse:
                cutroom.run(["git", "-C", dest, "sparse-checkout", "set"] + sparse)
        else:
            shutil.rmtree(dest, ignore_errors=True)

    if not cloned:
        os.makedirs(dest, exist_ok=True)
        cutroom.run(["git", "-C", dest, "init", "-q"])
        cutroom.run(["git", "-C", dest, "remote", "add", "origin", url])
        if sparse:
            cutroom.run(["git", "-C", dest, "sparse-checkout", "init", "--cone"])
            cutroom.run(["git", "-C", dest, "sparse-checkout", "set"] + sparse)
        cutroom.run(["git", "-C", dest, "fetch", "-q", "--depth", "1", "origin", target_ref])
        cutroom.run(["git", "-C", dest, "-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"])

    sha = git_out(["git", "-C", dest, "rev-parse", "HEAD"], timeout=5)
    write_ref_marker(dest, target_ref, sha=sha, repo=repo)
    return sha


def update_pin_in_cutroom_py(name: str, new_ref: str) -> list[str]:
    """Update the pinned version for `name` inside `cutroom.py` if writable."""
    updated_paths: list[str] = []
    candidates = [os.path.join(HARNESS, "cutroom.py")]
    repo_dir = cutroom_repo_dir()
    if repo_dir:
        repo_cutroom = os.path.join(repo_dir, "harness", "cutroom.py")
        if os.path.abspath(repo_cutroom) not in [os.path.abspath(p) for p in candidates]:
            candidates.append(repo_cutroom)

    pattern = re.compile(
        rf'("{re.escape(name)}"\s*:\s*\(\s*"[^"]+"\s*,\s*")([^"]+)(")'
    )
    for path in candidates:
        if not os.path.exists(path) or not os.access(path, os.W_OK):
            continue
        try:
            content = open(path, encoding="utf-8").read()
            new_content, count = pattern.subn(rf"\g<1>{new_ref}\g<3>", content, count=1)
            if count > 0 and new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated_paths.append(path)
        except OSError:
            pass
    if name in getattr(cutroom, "UPSTREAM", {}):
        repo, _, sparse = cutroom.UPSTREAM[name]
        cutroom.UPSTREAM[name] = (repo, new_ref, sparse)
    return updated_paths


def refresh_skill_safely(skill_name: str) -> bool:
    """Re-copy the corresponding cutroom-* skill to agent directories if source skills are accessible."""
    try:
        skills_dir = cutroom.source_skills()
        if os.path.isdir(os.path.join(skills_dir, skill_name)):
            cutroom.copy_skill(skill_name)
            return True
    except SystemExit:
        pass
    except OSError:
        pass
    return False


def apply_single_source(
    name: str,
    target_ref: str,
    update_pins: bool = False,
    approval_mode: str = "manual",
) -> dict[str, Any]:
    sources_map = all_sources()
    repo, pinned_ref, sparse = sources_map[name]
    meta = source_meta(name)
    loc = local_source_state(name, pinned_ref)
    from_ref = loc["current_ref"]
    sha: str | None = None

    if name in getattr(cutroom, "UPSTREAM", {}):
        print(f"↓ updating {name} ({repo}) {from_ref} → {target_ref}", flush=True)
        sha = clone_or_checkout_upstream(name, repo, target_ref, sparse)
    elif meta["kind"] == "self":
        repo_dir = cutroom_repo_dir()
        if repo_dir and os.path.isdir(os.path.join(repo_dir, ".git")):
            print(f"↓ fetching {name} ({repo}) in {repo_dir}", flush=True)
            cutroom.run(["git", "-C", repo_dir, "fetch", "--tags", "origin"], check=False)
            sha = git_out(["git", "-C", repo_dir, "rev-parse", "FETCH_HEAD"], timeout=5)
        else:
            dest = upstream_dir(name)
            write_ref_marker(dest, target_ref, repo=repo)
    else:
        dest = upstream_dir(name)
        print(f"• recording {name} ({repo}) target {target_ref} in {dest}/.cutroom-ref", flush=True)
        write_ref_marker(dest, target_ref, repo=repo)

    updated_pins: list[str] = []
    if update_pins:
        updated_pins = update_pin_in_cutroom_py(name, target_ref)

    skill_refreshed = refresh_skill_safely(meta["skill"])

    entry = {
        "applied_at": utc_now_iso(),
        "source": name,
        "repo": repo,
        "skill": meta["skill"],
        "component": meta["component"],
        "from_ref": from_ref,
        "to_ref": target_ref,
        "sha": sha,
        "mode": approval_mode,
        "updated_pins": updated_pins,
        "skill_refreshed": skill_refreshed,
    }
    return entry


def record_applied_entries(entries: list[dict[str, Any]]) -> None:
    if not entries:
        return
    cache = load_updates_cache()
    pol = load_policy()
    sources = cache.get("sources") if isinstance(cache.get("sources"), dict) else {}
    for entry in entries:
        name = entry["source"]
        rec = sources.get(name)
        if isinstance(rec, dict):
            rec["installed"] = True
            rec["installed_ref"] = entry["to_ref"]
            if entry.get("sha"):
                rec["installed_sha"] = entry["sha"]
            rec["current_ref"] = entry["to_ref"]
            rec["update_available"] = False
            rec["status"] = "up-to-date"

    cache["pending_updates"] = [
        p for p in (cache.get("pending_updates") or [])
        if isinstance(p, dict) and p.get("source") not in {e["source"] for e in entries}
    ]
    history = cache.get("history") if isinstance(cache.get("history"), list) else []
    history.extend(entries)
    cache["history"] = history[-100:]
    cache["policy"] = pol
    save_updates_cache(cache)


# --- formatting helpers --------------------------------------------------------------------------

def parse_source_args(raw_list: list[str] | None) -> list[str]:
    if not raw_list:
        return []
    out_list: list[str] = []
    for item in raw_list:
        for part in item.split(","):
            p = part.strip()
            if p and p not in out_list:
                out_list.append(p)
    return out_list


def print_check_table(cache: dict[str, Any], selected: list[str] | None = None) -> None:
    pol = normalize_policy(cache.get("policy") or load_policy())
    sources = cache.get("sources") or {}
    names = selected or list(all_sources().keys())

    print(
        f"cutroom updates · mode={pol['mode']} · channel={pol['channel']} "
        f"· interval={pol['interval_hours']}h · checked={cache.get('checked_at') or 'never'}\n"
    )
    header = f"{'Source':<13} {'Skill':<17} {'Installed/Pinned':<22} {'Latest Upstream':<18} {'Approval':<10} {'Status'}"
    print(header)
    print("-" * len(header))

    manual_pending: list[str] = []
    auto_pending: list[str] = []

    for name in names:
        rec = sources.get(name)
        if not isinstance(rec, dict):
            continue
        inst = rec.get("installed_ref")
        pin = rec.get("pinned_ref") or "-"
        if inst and inst != pin:
            cur_display = f"{inst} (pin {pin})"
        elif inst:
            cur_display = f"{inst} ✓"
        else:
            cur_display = f"{pin} (pinned)"

        latest_display = rec.get("latest_ref") or rec.get("latest_tag") or "-"
        auto = is_preapproved(name, pol)
        approval_display = "auto" if auto else "manual"
        status_label = rec.get("status") or "-"
        if rec.get("update_available"):
            status_display = f"↑ {latest_display} available"
            if auto:
                auto_pending.append(name)
            else:
                manual_pending.append(name)
        elif status_label == "offline":
            status_display = "✗ offline"
        else:
            status_display = "✓ up-to-date"

        print(
            f"{name:<13} {str(rec.get('skill') or '-'):<17} {cur_display:<22} "
            f"{latest_display:<18} {approval_display:<10} {status_display}"
        )

    print()
    if manual_pending:
        src_arg = " ".join(manual_pending)
        print(f"Updates awaiting approval ({len(manual_pending)}): {', '.join(manual_pending)}")
        print(f"  Manual approval:               cutroom updates apply {src_arg} --yes")
        print(f"  Pre-approve automatic updates: cutroom updates policy --mode auto  (or --approve {src_arg})")
    elif auto_pending:
        src_arg = " ".join(auto_pending)
        print(f"Pre-approved updates ready ({len(auto_pending)}): {', '.join(auto_pending)}")
        print(f"  Apply now: cutroom updates apply {src_arg}  (or cutroom updates check --apply-auto)")
    else:
        print("All tracked upstream sources are up to date.")


# --- CLI commands --------------------------------------------------------------------------------

def cmd_check(a: argparse.Namespace) -> int:
    selected = parse_source_args(a.source)
    pol = load_policy()
    channel = a.channel or pol["channel"]

    if a.cached:
        cache = load_updates_cache()
        if not cache_is_fresh(cache, pol["interval_hours"]):
            cache = check_sources(selected or None, channel=channel)
    else:
        cache = check_sources(selected or None, channel=channel)

    applied: list[dict[str, Any]] = []
    if a.apply_auto:
        sources = cache.get("sources") or {}
        for name in (selected or list(sources.keys())):
            rec = sources.get(name)
            if not isinstance(rec, dict) or not rec.get("update_available"):
                continue
            if is_preapproved(name, pol) and rec.get("latest_ref"):
                entry = apply_single_source(name, rec["latest_ref"], update_pins=False, approval_mode="auto")
                applied.append(entry)
        if applied:
            record_applied_entries(applied)
            cache = load_updates_cache()

    if a.json:
        out_payload = dict(cache)
        if applied:
            out_payload["applied"] = applied
        print(json.dumps(out_payload, indent=2, ensure_ascii=False))
        return 0

    print_check_table(cache, selected or None)
    if applied:
        print(f"\n✓ Auto-applied {len(applied)} pre-approved update(s): " + ", ".join(e["source"] for e in applied))
    return 0


def cmd_apply(a: argparse.Namespace) -> int:
    sources_map = all_sources()
    pol = load_policy()
    selected = parse_source_args(a.sources)

    if selected:
        unknown = [n for n in selected if n not in sources_map]
        if unknown:
            raise SystemExit(f"unknown source(s): {', '.join(unknown)}. Options: {', '.join(sources_map)}")

    cache = load_updates_cache()
    if not cache.get("sources") or (not a.to and not cache_is_fresh(cache, pol["interval_hours"])):
        cache = check_sources(selected or None, channel=pol["channel"])

    records = cache.get("sources") or {}
    targets: list[tuple[str, str, dict[str, Any]]] = []

    if a.to:
        if not selected:
            raise SystemExit("specify at least one <source> when using --to <ref>")
        for name in selected:
            rec = records.get(name) or {
                "source": name,
                "repo": sources_map[name][0],
                "url": f"https://github.com/{sources_map[name][0]}",
                "skill": source_meta(name)["skill"],
                "component": source_meta(name)["component"],
                "current_ref": local_source_state(name, sources_map[name][1])["current_ref"],
            }
            targets.append((name, a.to, rec))
    else:
        candidates = selected if selected else list(sources_map.keys())
        for name in candidates:
            rec = records.get(name)
            if not isinstance(rec, dict):
                continue
            if rec.get("update_available") and rec.get("latest_ref"):
                targets.append((name, rec["latest_ref"], rec))
            elif selected and not a.all:
                # Explicitly requested source that is already at latest_ref: allow re-sync if not installed locally
                loc = local_source_state(name, sources_map[name][1])
                target_ref = rec.get("latest_ref") or sources_map[name][1]
                if not loc["installed"] and name in getattr(cutroom, "UPSTREAM", {}):
                    targets.append((name, target_ref, rec))

    if not targets:
        if a.json:
            print(json.dumps({"applied": [], "pending_approval": [], "message": "No updates to apply."}, indent=2))
        else:
            print("No pending updates to apply.")
        return 0

    approved_targets: list[tuple[str, str, dict[str, Any], str]] = []
    manual_targets: list[tuple[str, str, dict[str, Any]]] = []

    for name, target_ref, rec in targets:
        if a.yes:
            approved_targets.append((name, target_ref, rec, "manual"))
        elif is_preapproved(name, pol):
            approved_targets.append((name, target_ref, rec, "auto"))
        else:
            manual_targets.append((name, target_ref, rec))

    if manual_targets and not approved_targets:
        plan = [
            {
                "source": name,
                "repo": rec.get("repo") or sources_map[name][0],
                "url": rec.get("url") or f"https://github.com/{sources_map[name][0]}",
                "skill": rec.get("skill") or source_meta(name)["skill"],
                "component": rec.get("component") or source_meta(name)["component"],
                "from_ref": rec.get("current_ref") or sources_map[name][1],
                "to_ref": target_ref,
                "approval": "manual",
            }
            for name, target_ref, rec in manual_targets
        ]
        if a.json:
            print(json.dumps({"dry_run": True, "plan": plan}, indent=2, ensure_ascii=False))
            return 0
        print("Update plan (manual approval required):\n")
        for item in plan:
            print(
                f"  • {item['source']} ({item['repo']}): {item['from_ref']} → {item['to_ref']} "
                f"[/{item['skill']} · component: {item['component']}]"
            )
        names_str = " ".join(item["source"] for item in plan)
        print(
            f"\nRun again with --yes to approve and apply locally:\n"
            f"  cutroom updates apply {names_str} --yes\n"
            f"Or pre-approve future updates with:\n"
            f"  cutroom updates policy --approve {names_str}"
        )
        return 0

    applied: list[dict[str, Any]] = []
    for name, target_ref, _, mode_label in approved_targets:
        entry = apply_single_source(name, target_ref, update_pins=a.update_pins, approval_mode=mode_label)
        applied.append(entry)

    record_applied_entries(applied)

    if a.json:
        print(
            json.dumps(
                {
                    "dry_run": False,
                    "applied": applied,
                    "pending_approval": [
                        {"source": n, "from_ref": r.get("current_ref"), "to_ref": t}
                        for n, t, r in manual_targets
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    for entry in applied:
        print(f"✓ {entry['source']}: {entry['from_ref']} → {entry['to_ref']} ({entry['mode']})")

    if manual_targets:
        names_str = " ".join(n for n, _, _ in manual_targets)
        print(f"\nSkipped {len(manual_targets)} source(s) requiring manual approval: {', '.join(n for n, _, _ in manual_targets)}")
        print(f"  Approve and apply: cutroom updates apply {names_str} --yes")
    return 0


def cmd_policy(a: argparse.Namespace) -> int:
    sources_map = all_sources()
    pol = load_policy()
    changed = False

    if a.mode:
        pol["mode"] = a.mode
        changed = True
    if a.channel:
        pol["channel"] = a.channel
        changed = True
    if a.interval is not None:
        if a.interval <= 0:
            raise SystemExit("--interval must be > 0 hours")
        pol["interval_hours"] = int(a.interval) if float(a.interval).is_integer() else float(a.interval)
        changed = True

    approve_list = parse_source_args(a.approve)
    if approve_list:
        if "all" in approve_list or "*" in approve_list:
            pol["preapproved"] = list(sources_map.keys())
        else:
            unknown = [n for n in approve_list if n not in sources_map]
            if unknown:
                raise SystemExit(f"unknown source(s): {', '.join(unknown)}. Options: {', '.join(sources_map)}, all")
            cur = list(pol.get("preapproved") or [])
            for n in approve_list:
                if n not in cur:
                    cur.append(n)
            pol["preapproved"] = cur
        changed = True

    revoke_list = parse_source_args(a.revoke)
    if revoke_list:
        if "all" in revoke_list or "*" in revoke_list:
            pol["preapproved"] = []
        else:
            pol["preapproved"] = [n for n in (pol.get("preapproved") or []) if n not in revoke_list]
        changed = True

    if changed:
        pol = save_policy(pol)

    if a.json:
        print(json.dumps(pol, indent=2, ensure_ascii=False))
        return 0

    prefix = "✓ Updated updates policy" if changed else "Updates policy"
    print(f"{prefix} ({os.path.join(home_dir(), 'config.json')}):")
    print(f"  mode:           {pol['mode']}  (ask = manual approval, auto = pre-approved automatic, off = disabled)")
    print(f"  channel:        {pol['channel']}  (tags = semver release tags, commits = default branch HEAD)")
    print(f"  interval_hours: {pol['interval_hours']}")
    print(f"  preapproved:    {', '.join(pol['preapproved']) if pol['preapproved'] else '(none)'}")
    return 0


def cmd_watch(a: argparse.Namespace) -> int:
    pol = load_policy()
    interval_minutes = a.interval if a.interval is not None else max(1, int(float(pol["interval_hours"]) * 60))

    def single_pass() -> dict[str, Any]:
        current_pol = load_policy()
        if current_pol["mode"] == "off":
            return {"skipped": True, "reason": "updates.mode is 'off'", "checked_at": utc_now_iso()}
        cache = check_sources(channel=current_pol["channel"])
        applied: list[dict[str, Any]] = []
        should_auto = a.apply_auto or current_pol["mode"] == "auto" or bool(current_pol.get("preapproved"))
        if should_auto:
            for name, rec in (cache.get("sources") or {}).items():
                if not isinstance(rec, dict) or not rec.get("update_available"):
                    continue
                if is_preapproved(name, current_pol) and rec.get("latest_ref"):
                    entry = apply_single_source(name, rec["latest_ref"], update_pins=False, approval_mode="auto")
                    applied.append(entry)
            if applied:
                record_applied_entries(applied)
                cache = load_updates_cache()
        return {
            "checked_at": cache.get("checked_at"),
            "policy": current_pol,
            "applied": applied,
            "pending_updates": cache.get("pending_updates") or [],
        }

    if a.once:
        result = single_pass()
        if a.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        if result.get("skipped"):
            print("• updates watch skipped: updates.mode is 'off' (enable with `cutroom updates policy --mode ask`).")
            return 0
        applied = result.get("applied") or []
        pending = result.get("pending_updates") or []
        print(f"[{result['checked_at']}] checked {len(all_sources())} upstream sources.")
        for e in applied:
            print(f"  ✓ auto-applied {e['source']}: {e['from_ref']} → {e['to_ref']}")
        for p in pending:
            print(
                f"  ↑ {p['source']}: {p['current']} → {p['latest']} "
                f"(approve: `cutroom updates apply {p['source']} --yes`)"
            )
        if not applied and not pending:
            print("  ✓ all sources up to date.")
        return 0

    print(f"Listening for upstream updates every {interval_minutes} min (Ctrl+C to stop)...", flush=True)
    try:
        while True:
            result = single_pass()
            if a.json:
                print(json.dumps(result, ensure_ascii=False), flush=True)
            else:
                applied = result.get("applied") or []
                pending = result.get("pending_updates") or []
                print(
                    f"[{result.get('checked_at')}] applied={len(applied)} pending={len(pending)}",
                    flush=True,
                )
                for p in pending:
                    print(
                        f"  ↑ {p['source']}: {p['current']} → {p['latest']} "
                        f"(`cutroom updates apply {p['source']} --yes`)",
                        flush=True,
                    )
            time.sleep(max(1, int(interval_minutes * 60)))
    except KeyboardInterrupt:
        return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="cutroom updates",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd")

    s_check = sub.add_parser("check", help="check tracked upstream repositories for new tags or commits")
    s_check.add_argument("--source", nargs="+", help="check only specific source(s)")
    s_check.add_argument("--channel", choices=("tags", "commits"), help="override tags or commits channel")
    s_check.add_argument("--cached", action="store_true", help="use cached updates.json if fresher than interval")
    s_check.add_argument("--apply-auto", action="store_true", help="automatically apply pre-approved updates")
    s_check.add_argument("--json", action="store_true")
    s_check.set_defaults(fn=cmd_check)

    s_apply = sub.add_parser("apply", help="apply upstream updates locally (requires --yes unless pre-approved)")
    s_apply.add_argument("sources", nargs="*", help="source name(s) to update")
    s_apply.add_argument("--all", action="store_true", help="select all sources with available updates")
    s_apply.add_argument("--to", help="explicit target tag, branch, or commit SHA")
    s_apply.add_argument("--update-pins", action="store_true", help="also update UPSTREAM pins in cutroom.py")
    s_apply.add_argument("--yes", action="store_true", help="confirm and apply manual updates")
    s_apply.add_argument("--json", action="store_true")
    s_apply.set_defaults(fn=cmd_apply)

    s_pol = sub.add_parser("policy", help="view or configure automatic vs manual approval policy")
    s_pol.add_argument("--mode", choices=("ask", "auto", "off"), help="ask (manual), auto (all), or off")
    s_pol.add_argument("--channel", choices=("tags", "commits"), help="track release tags or HEAD commits")
    s_pol.add_argument("--interval", type=float, help="check interval in hours (default: 12)")
    s_pol.add_argument("--approve", nargs="+", help="pre-approve source(s) for automatic updates (or 'all')")
    s_pol.add_argument("--revoke", nargs="+", help="remove source(s) from pre-approved list (or 'all')")
    s_pol.add_argument("--json", action="store_true")
    s_pol.set_defaults(fn=cmd_policy)

    s_watch = sub.add_parser("watch", help="poll upstream repositories and auto-apply pre-approved updates")
    s_watch.add_argument("--interval", type=int, help="polling interval in minutes (default: interval_hours * 60)")
    s_watch.add_argument("--once", action="store_true", help="run a single check + auto-apply pass and exit")
    s_watch.add_argument("--apply-auto", action="store_true", help="auto-apply pre-approved updates")
    s_watch.add_argument("--json", action="store_true")
    s_watch.set_defaults(fn=cmd_watch)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "cmd", None):
        # Default to `check --cached` when invoked as `cutroom updates` with no subcommand
        args = ap.parse_args(["check", "--cached"])
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
