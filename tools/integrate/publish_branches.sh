#!/usr/bin/env bash
# TOPOLOGY B (each teammate on their own laptop). INTEGRATOR ONLY, after `origin` exists
# (e.g. `gh repo create HackCMU2026 --private --source . --push`) and the freeze tags are created.
# Pushes main + tags and creates the three agent branches on the remote.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
[ "$(git branch --show-current)" = main ] || { echo "run from the main checkout"; exit 1; }
git rev-parse -q --verify h0-freeze >/dev/null || { echo "create the freeze tags first: git tag h0-freeze && git tag sanity-lock"; exit 1; }
git push -u origin main
git push origin --tags
for role in data engine web; do
  git push origin "h0-freeze^{commit}:refs/heads/agent/$role"
done
echo
echo "Each teammate now runs (replace URL and role):"
echo "  git clone <repo-url> ~/HackCMU2026-p1-data && cd ~/HackCMU2026-p1-data && git switch agent/data"
echo "  tools/integrate/setup_worktree.sh . data"
