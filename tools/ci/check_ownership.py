#!/usr/bin/env python3
"""Fail if this branch touches files outside its role (see OWNERS.json). OWNER: integrator.

    python3 tools/ci/check_ownership.py            # whole branch vs merge-base with main (CI, make check)
    python3 tools/ci/check_ownership.py --staged   # staged files only (git pre-commit hook)
    python3 tools/ci/check_ownership.py --locked   # locked paths unchanged since the lock tag (any branch)
    python3 tools/ci/check_ownership.py --role data --paths web/src/App.tsx   # ad-hoc query
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_lib import (  # noqa: E402
    changed_files,
    check_path,
    current_branch,
    git,
    load_owners,
    repo_root,
    role_for_branch,
    tag_exists,
)


def check_locked(root: Path, owners: dict) -> int:
    locked = owners.get("locked", {})
    tag = locked.get("tag")
    if not tag or not tag_exists(tag, str(root)):
        print(f"locked paths: tag '{tag}' not created yet (sanity set still editable)")
        return 0
    changed = git("diff", "--name-only", tag, "HEAD", "--", *[p.replace("/**", "") for p in locked["paths"]],
                  cwd=str(root), check=False).split()
    if changed and os.environ.get("ALLOW_LOCKED") != "1":
        print(f"locked paths: BLOCKED - changed since tag '{tag}': {', '.join(changed)}", file=sys.stderr)
        return 1
    print(f"locked paths: OK (unchanged since '{tag}')")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--locked", action="store_true")
    ap.add_argument("--role")
    ap.add_argument("--paths", nargs="*")
    args = ap.parse_args()

    root = repo_root()
    owners = load_owners(root)
    if args.locked:
        return check_locked(root, owners)
    branch = current_branch(str(root))
    role = args.role or role_for_branch(branch, owners)
    if role is None:
        print(f"ownership: branch '{branch}' is not an agent branch (agent/data, agent/engine, agent/web) or main.\n"
              f"  Work only on your role branch. See AGENTS.md.", file=sys.stderr)
        return 1

    if args.paths is not None:
        files = [("M", p) for p in args.paths]
    else:
        files = changed_files("staged" if args.staged else "branch", str(root))

    violations = [v for s, p in files if (v := check_path(p, role, owners, s, str(root)))]
    if violations:
        print(f"ownership: BLOCKED - branch '{branch}' (role '{role}') changed files it does not own:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        print("  Fix: undo those changes (git restore --staged <file> && git restore <file>) and write a REQUEST\n"
              f"  in docs/handoffs/{role if role != 'integrator' else '<role>'}.md instead. See AGENTS.md.",
              file=sys.stderr)
        return 1
    print(f"ownership: OK ({len(files)} file(s) checked, role '{role}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
