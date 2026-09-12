#!/usr/bin/env bash
# INTEGRATOR ONLY: merge the agent branches into main in dependency order, running checks after each.
#   tools/integrate/checkpoint.sh h8
# A branch that conflicts or fails `make check` is backed out (git reset --keep) and reported; the
# others still merge. Tagging happens only after you finish the real-mode smoke checklist.
set -euo pipefail
TAG="${1:?usage: checkpoint.sh <tag, e.g. h8>}"
cd "$(git rev-parse --show-toplevel)"
[ "$(git branch --show-current)" = main ] || { echo "run from the main checkout"; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "main has uncommitted changes - commit or stash first"; exit 1; }
git fetch origin --tags 2>/dev/null || true

pick() {  # newest of origin/agent/<role> and agent/<role>
  local role=$1 best="" best_ts=0 ts
  for ref in "origin/agent/$role" "agent/$role"; do
    if git rev-parse -q --verify "$ref" >/dev/null; then
      ts=$(git log -1 --format=%ct "$ref"); if [ "$ts" -gt "$best_ts" ]; then best=$ref; best_ts=$ts; fi
    fi
  done
  echo "$best"
}

failed=()
for role in engine data data-dishes web; do
  ref=$(pick "$role")
  if [ -z "$ref" ]; then echo "== $role: no branch, skipping"; continue; fi
  echo "================ merging $ref ================"
  before=$(git rev-parse HEAD)
  if ! git merge --no-ff --no-edit -m "[checkpoint $TAG] merge agent/$role" "$ref"; then
    git merge --abort || true
    echo "!! CONFLICT merging $role (someone edited outside their folder?). Backed out."
    failed+=("$role (conflict)"); continue
  fi
  case "$role" in data*) make build || true ;; esac
  if ! make check; then
    echo "!! make check FAILED after merging $role. Backing it out; owner fixes on their branch."
    git reset --keep "$before"
    failed+=("$role (checks)")
  fi
done

echo
echo "================ checkpoint $TAG ================"
git log --oneline -5
if [ ${#failed[@]} -gt 0 ]; then echo "NOT merged: ${failed[*]}  -> write a REQUEST to each owner, 30-min fix window, re-run."; fi
cat <<EOF

Now run the real-mode smoke checklist (docs/INTEGRATION.md): make dev  (VITE_API_MODE=real)
  [ ] galaxy loads the real space   [ ] click dish -> twins   [ ] drag slider -> target glides
  [ ] explain shows provenance       [ ] recipe returns coverage [ ] Ask works (or is hidden w/o key)
If it passes:   git tag $TAG && git push origin main --tags     (then post: "main @ $TAG ready")
Agents refresh: git fetch origin && git merge --no-edit origin/main && make setup && make check-<role>
EOF
