"""Shared ownership logic (stdlib only, Python 3.9+) for the git hooks, CI and the Claude Code guard.

OWNER: integrator.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def git(*args: str, cwd: Optional[str] = None, check: bool = True) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout.strip()


def repo_root(cwd: Optional[str] = None) -> Path:
    return Path(git("rev-parse", "--show-toplevel", cwd=cwd))


def load_owners(root: Path) -> dict:
    return json.loads((root / "OWNERS.json").read_text())


_GLOB_CACHE: Dict[str, "re.Pattern[str]"] = {}


def glob_to_regex(glob: str) -> "re.Pattern[str]":
    if glob in _GLOB_CACHE:
        return _GLOB_CACHE[glob]
    i, out = 0, ""
    while i < len(glob):
        if glob.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif glob.startswith("**", i):
            out += ".*"
            i += 2
        elif glob[i] == "*":
            out += "[^/]*"
            i += 1
        elif glob[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(glob[i])
            i += 1
    pat = re.compile("^" + out + "$")
    _GLOB_CACHE[glob] = pat
    return pat


def matches_any(path: str, globs: List[str]) -> bool:
    return any(glob_to_regex(g).match(path) for g in globs)


def current_branch(cwd: Optional[str] = None) -> str:
    for var in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        if os.environ.get(var):
            return os.environ[var]
    return git("branch", "--show-current", cwd=cwd, check=False)


def role_for_branch(branch: str, owners: dict) -> Optional[str]:
    branches = owners["branches"]
    if branch in branches:
        return branches[branch]
    for prefix, role in branches.items():
        if prefix.startswith("agent/") and branch.startswith(prefix + "-"):
            return role
    return None


def tag_exists(tag: str, cwd: Optional[str] = None) -> bool:
    return bool(git("tag", "--list", tag, cwd=cwd, check=False))


def check_path(path: str, role: str, owners: dict, status: str = "M", cwd: Optional[str] = None) -> Optional[str]:
    """Return a human-readable violation message, or None if the change is allowed."""
    if role not in owners["roles"]:
        return f"unknown role '{role}'"
    allowed = owners["roles"][role]
    excluded = owners.get("exclude", {}).get(role, [])
    if not matches_any(path, allowed) or matches_any(path, excluded):
        owner = next((r for r, globs in owners["roles"].items()
                      if r != "integrator" and matches_any(path, globs)
                      and not matches_any(path, owners.get("exclude", {}).get(r, []))), "integrator")
        return f"{path}: owned by '{owner}', you are '{role}'"
    if status in ("M", "D", "R") and matches_any(path, owners.get("append_only", {}).get(role, [])):
        return f"{path}: append-only (add new fixture files instead of changing existing ones)"
    locked = owners.get("locked", {})
    if locked and matches_any(path, locked.get("paths", [])) and tag_exists(locked["tag"], cwd=cwd):
        if os.environ.get("ALLOW_LOCKED") != "1":
            return f"{path}: locked since tag '{locked['tag']}' (frozen sanity set; see docs/INTEGRATION.md)"
    return None


def best_merge_base(cwd: Optional[str] = None) -> Optional[str]:
    """Most recent merge-base between HEAD and main/origin/main (handles stale local main)."""
    bases = []
    for ref in ("origin/main", "main"):
        if git("rev-parse", "--verify", "--quiet", ref, cwd=cwd, check=False):
            mb = git("merge-base", "HEAD", ref, cwd=cwd, check=False)
            if mb:
                bases.append(mb)
    if not bases:
        return None
    best = bases[0]
    for b in bases[1:]:
        if subprocess.run(["git", "merge-base", "--is-ancestor", best, b], cwd=cwd).returncode == 0:
            best = b
    return best


def changed_files(mode: str, cwd: Optional[str] = None) -> List[Tuple[str, str]]:
    """[(status_letter, path)] for staged changes or for the whole branch vs its merge-base."""
    if mode == "staged":
        raw = git("diff", "--cached", "--name-status", cwd=cwd, check=False)
    else:
        base = best_merge_base(cwd)
        if base is None:
            return []
        raw = git("diff", "--name-status", base, "HEAD", cwd=cwd, check=False)
    out: List[Tuple[str, str]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if not parts or not parts[0]:
            continue
        status = parts[0][0]
        for p in parts[1:]:
            out.append((status, p))
    return out
