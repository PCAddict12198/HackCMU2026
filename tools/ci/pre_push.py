#!/usr/bin/env python3
"""git pre-push hook: only the integrator (on main) pushes main; nobody force-pushes or deletes
branches. OWNER: integrator. Emergency override: ALLOW_FORCE=1 (integrator only, with team OK)."""

import os
import subprocess
import sys

ZERO = "0" * 40


def main() -> int:
    branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
    problems = []
    for line in sys.stdin:
        parts = line.split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, remote_ref, remote_sha = parts
        if remote_ref in ("refs/heads/main", "refs/heads/master") and branch != "main":
            problems.append("agents never push main. Push your own branch: git push origin HEAD")
        if local_sha == ZERO:
            problems.append(f"deleting {remote_ref} is not allowed")
            continue
        if remote_sha != ZERO and os.environ.get("ALLOW_FORCE") != "1":
            ff = subprocess.run(["git", "merge-base", "--is-ancestor", remote_sha, local_sha],
                                capture_output=True).returncode == 0
            if not ff:
                problems.append(f"{remote_ref} has commits you don't have (or this is a force push). "
                                f"Run: git fetch origin && git merge origin/{remote_ref.split('/', 2)[-1]}")
    if problems:
        print("pre-push: BLOCKED\n  - " + "\n  - ".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
