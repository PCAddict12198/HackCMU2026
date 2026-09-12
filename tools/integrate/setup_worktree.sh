#!/usr/bin/env bash
# Prepare one checkout (worktree or clone) for a role. OWNER: integrator.
#   tools/integrate/setup_worktree.sh <dir> <data|engine|web|integrator> [api_port] [web_port]
# Writes .env.local (role + ports), copies .env from the main checkout if missing, enables the git hooks,
# installs deps, and runs the role's check. Safe to re-run.
set -euo pipefail
DIR="${1:?usage: setup_worktree.sh <dir> <data|engine|web|integrator> [api_port] [web_port]}"
ROLE="${2:?role: data|engine|web|integrator}"
API_PORT="${3:-8000}"
WEB_PORT="${4:-5173}"
cd "$DIR"
MAIN_CHECKOUT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"

cat > .env.local <<EOF
# per-checkout settings (gitignored). Written by tools/integrate/setup_worktree.sh
ROLE=$ROLE
API_PORT=$API_PORT
WEB_PORT=$WEB_PORT
EOF
if [ ! -f .env ]; then
  if [ -f "$MAIN_CHECKOUT/.env" ] && [ "$MAIN_CHECKOUT" != "$(pwd)" ]; then cp "$MAIN_CHECKOUT/.env" .env
  else cp .env.example .env; fi
fi
git config core.hooksPath .githooks
make setup
if [ "$ROLE" = integrator ]; then make check; else make "check-$ROLE"; fi
echo
echo "Ready: $(pwd)  role=$ROLE  branch=$(git branch --show-current)  api=:$API_PORT  web=:$WEB_PORT"
echo "Next: open this folder in your AI agent and paste the kickoff prompt from docs/agents/$ROLE.md"
