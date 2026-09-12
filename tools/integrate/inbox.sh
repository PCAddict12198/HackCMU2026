#!/usr/bin/env bash
# `make inbox`: read every agent's latest committed handoff notes WITHOUT merging anything.
# Uses whichever of origin/agent/<role> or agent/<role> is newer. OWNER: integrator.
set -uo pipefail
git fetch -q origin 2>/dev/null || true
for role in data engine web; do
  best="" best_ts=0
  for ref in "origin/agent/$role" "agent/$role"; do
    if git rev-parse -q --verify "$ref" >/dev/null; then
      ts=$(git log -1 --format=%ct "$ref")
      if [ "$ts" -gt "$best_ts" ]; then best=$ref; best_ts=$ts; fi
    fi
  done
  if [ -z "$best" ]; then echo "=== $role: no branch yet"; continue; fi
  echo "=============== $role  ($best @ $(git log -1 --format='%h, %cr' "$best")) ==============="
  git show "$best:docs/handoffs/$role.md" 2>/dev/null | head -n "${INBOX_LINES:-40}"
  echo
done
