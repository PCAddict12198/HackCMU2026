#!/usr/bin/env bash
# TOPOLOGY A (all three agents on THIS machine). INTEGRATOR ONLY, run from the main checkout after the
# H0 review + `git tag h0-freeze && git tag sanity-lock`. Creates:
#   ../<repo>-p1-data (agent/data)  ../<repo>-p2-engine (agent/engine)  ../<repo>-p3-web (agent/web)
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
[ "$(git branch --show-current)" = main ] || { echo "run from the main checkout"; exit 1; }
git rev-parse -q --verify h0-freeze >/dev/null || { echo "create the freeze tags first: git tag h0-freeze && git tag sanity-lock"; exit 1; }
PARENT=$(dirname "$ROOT")
NAME=$(basename "$ROOT")

add() {
  local role=$1 suffix=$2 api=$3 web=$4
  local dir="$PARENT/$NAME-$suffix"
  if [ -d "$dir" ]; then echo "exists: $dir"; else git worktree add -b "agent/$role" "$dir" h0-freeze; fi
  bash "$ROOT/tools/integrate/setup_worktree.sh" "$dir" "$role" "$api" "$web"
}
add data p1-data 8001 5174
add engine p2-engine 8002 5175
add web p3-web 8003 5176
git worktree list
