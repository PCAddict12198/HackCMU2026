#!/usr/bin/env python3
"""Claude Code PreToolUse guard (wired in .claude/settings.json). OWNER: integrator.

Blocks (exit 2, reason shown to the agent):
  * Edit/Write/MultiEdit/NotebookEdit on files the current branch's role does not own (OWNERS.json)
  * risky git commands: push to main, force push, reset --hard, rebase, --no-verify, switching to main,
    deleting branches, merging other agent branches, changing hooksPath
  * dependency changes by roles that don't own the lockfile (uv add/remove/lock; npm install <pkg>)

The role comes from the git branch of the directory Claude is working in, so the same committed
settings file behaves correctly in every worktree / clone. Stdlib only.
"""

import json
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_lib import check_path, current_branch, load_owners, repo_root, role_for_branch  # noqa: E402


def block(msg: str) -> None:
    print(f"TasteSpace guard: {msg}\nIf another area needs this change, write a REQUEST in your "
          f"docs/handoffs/<role>.md and keep working (see AGENTS.md).", file=sys.stderr)
    sys.exit(2)


def check_edit(path_str: str, cwd: str, role: str, owners: dict, root: Path) -> None:
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(cwd) / p
    try:
        rel = p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return  # outside the repo (scratch files etc.)
    if rel.startswith(".git/"):
        block(f"editing {rel} is not allowed")
    violation = check_path(rel, role, owners, "M", str(root))
    if violation:
        block(violation)


GIT_RULES = [
    (r"\bgit\b.*\bpush\b.*(--force\b|--force-with-lease|\s-f\b|\s\+\S)", "force-push is not allowed"),
    (r"\bgit\b.*\breset\b.*--hard", "git reset --hard is not allowed (it destroys work); use git restore <file>"),
    (r"\bgit\b.*\brebase\b", "rebase is not allowed; refresh with: git merge origin/main"),
    (r"\bgit\b.*\b(commit|push|merge)\b.*(--no-verify|\s-n\b)", "bypassing git hooks is not allowed"),
    (r"\bgit\b.*\bconfig\b.*core\.hooksPath", "changing hooksPath is not allowed"),
    (r"\bgit\b.*\bbranch\b.*\s-(d|D)\b", "deleting branches is not allowed"),
]
AGENT_ONLY_GIT_RULES = [
    (r"\bgit\b.*\bpush\b.*\b(main|master)\b", "agents never push to main; push your own branch: git push origin HEAD"),
    (r"\bgit\b.*\b(checkout|switch)\b\s+(-\S+\s+)*(main|master)\b", "stay on your agent branch; do not switch to main"),
    (r"\bgit\b.*\bmerge\b.*\bagent/", "never merge another agent's branch; only the integrator merges (at checkpoints)"),
    (r"\bgit\b.*\bworktree\b.*\b(add|remove|prune|move)\b", "worktrees are managed by the integrator"),
]


def check_bash(cmd: str, role: str) -> None:
    for pat, msg in GIT_RULES:
        if re.search(pat, cmd):
            block(msg)
    if role != "integrator":
        for pat, msg in AGENT_ONLY_GIT_RULES:
            if re.search(pat, cmd):
                block(msg)
        if re.search(r"\buv\s+(add|remove|lock)\b", cmd) or re.search(r"\bpip\d*\s+install\b", cmd):
            block("Python dependencies are integrator-owned (uv.lock). Request the package in your handoff file.")
    if role not in ("web", "integrator"):
        try:
            words = shlex.split(cmd)
        except ValueError:
            words = cmd.split()
        for i, w in enumerate(words):
            if w == "npm" and i + 1 < len(words) and words[i + 1] in ("install", "i", "add", "uninstall", "remove", "rm"):
                rest = [x for x in words[i + 2:] if not x.startswith("-")]
                if rest and rest[0] not in ("&&", ";", "|"):
                    block("JS dependencies are owned by web (P3). Request the package in your handoff file.")


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    cwd = event.get("cwd") or "."
    tool = event.get("tool_name", "")
    tin = event.get("tool_input") or {}
    try:
        root = repo_root(cwd)
        owners = load_owners(root)
    except Exception:
        sys.exit(0)  # not inside a TasteSpace checkout
    branch = current_branch(str(root))
    role = role_for_branch(branch, owners)
    if role is None:
        if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            block(f"branch '{branch}' has no role. Agents work on agent/data, agent/engine or agent/web.")
        sys.exit(0)

    if tool in ("Edit", "Write", "MultiEdit"):
        check_edit(tin.get("file_path", ""), cwd, role, owners, root)
    elif tool == "NotebookEdit":
        check_edit(tin.get("notebook_path", ""), cwd, role, owners, root)
    elif tool == "Bash":
        check_bash(tin.get("command", ""), role)
    sys.exit(0)


if __name__ == "__main__":
    main()
