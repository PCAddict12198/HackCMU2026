#!/usr/bin/env bash
# Fail if contracts/openapi.json, contracts/schemas/* or contracts/generated/api.d.ts no longer match
# the pydantic models + FastAPI routes. Only the integrator regenerates them (`make contracts`).
# Note for P2: route docstrings/summaries end up in OpenAPI, so keep route functions docstring-free.
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
uv run --frozen python -m tastespace.export_openapi "$TMP/openapi.json" >/dev/null
uv run --frozen python -m tastespace_contracts.export_schemas "$TMP/schemas" >/dev/null
(cd web && npx --no-install openapi-typescript "$TMP/openapi.json" -o "$TMP/api.d.ts" >/dev/null 2>&1)
fail=0
diff -q "$TMP/openapi.json" contracts/openapi.json >/dev/null || { echo "  drift: contracts/openapi.json"; fail=1; }
diff -rq "$TMP/schemas" contracts/schemas >/dev/null || { echo "  drift: contracts/schemas/"; fail=1; }
diff -q "$TMP/api.d.ts" contracts/generated/api.d.ts >/dev/null || { echo "  drift: contracts/generated/api.d.ts"; fail=1; }
if [ "$fail" = 1 ]; then
  echo "contracts: DRIFT - the API/data models no longer match the frozen contract."
  echo "  Agents: revert your change to the models/routes and file a REQUEST in your handoff."
  echo "  Integrator: follow docs/CONTRACTS.md (make contracts, bump contracts/VERSION)."
  exit 1
fi
echo "contracts: OK (no drift)"
