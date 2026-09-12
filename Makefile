# TasteSpace task runner. OWNER: integrator (main only). `make help` lists targets.
SHELL := /bin/bash
.DEFAULT_GOAL := help
-include .env.local
API_PORT ?= 8000
WEB_PORT ?= 5173
export API_PORT WEB_PORT
UV := uv run --frozen
PY := $(UV) python

.PHONY: help setup build report api web dev check check-ownership check-contracts check-data check-engine \
        check-web contracts fixtures inbox

help: ## show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## install Python (uv) + web (npm) deps and enable the git hooks
	uv sync --frozen
	cd web && npm ci --no-audit --no-fund
	git config core.hooksPath .githooks

build: ## data/ -> build/tastespace.json + build/report.md
	$(PY) -m tastespace.build

report: build ## build, then print the report
	@cat build/report.md

api: ## FastAPI on API_PORT (after data edits run `make build`; the API reloads the artifact)
	$(UV) uvicorn tastespace.api:app --reload --reload-dir backend --port $(API_PORT)

web: ## Vite on WEB_PORT; data source = VITE_API_MODE in .env (mock | real)
	cd web && npm run dev -- --port $(WEB_PORT) --strictPort

dev: build ## API + web in REAL mode together (Ctrl-C stops both)
	@trap 'kill 0' INT TERM EXIT; \
	  $(UV) uvicorn tastespace.api:app --reload --reload-dir backend --port $(API_PORT) & \
	  (cd web && VITE_API_MODE=real npm run dev -- --port $(WEB_PORT) --strictPort) & \
	  wait

check-ownership: ## every file changed on this branch belongs to your role (OWNERS.json)
	python3 tools/ci/check_ownership.py

check-contracts: ## generated contracts match the models; canonical fixtures validate
	bash tools/ci/check_contract_drift.sh
	$(UV) pytest contracts/tests -q

check-data: ## P1: validate data/, sanity lock, core build smoke test, lint tools/data
	$(PY) tools/data/validate_data.py
	python3 tools/ci/check_ownership.py --locked
	$(PY) -m tastespace.build --out-dir build/check >/dev/null
	$(UV) ruff check tools/data

check-engine: ## P2: lint + engine/API/Grok tests (fixtures only, no network)
	$(UV) ruff check backend contracts tools/integrate tools/ci
	$(UV) pytest backend/tests -q

check-web: ## P3: typecheck + unit tests
	cd web && npm run typecheck && npm test -- --run

check: check-ownership check-contracts check-data check-engine check-web ## everything (CI + checkpoints)
	@echo "ALL CHECKS PASSED"

contracts: ## INTEGRATOR: regenerate openapi.json, TS types, data schemas (then bump contracts/VERSION)
	$(PY) -m tastespace.export_openapi contracts/openapi.json
	$(PY) -m tastespace_contracts.export_schemas contracts/schemas
	cd web && npx --no-install openapi-typescript ../contracts/openapi.json -o ../contracts/generated/api.d.ts
	$(UV) pytest contracts/tests -q

fixtures: ## INTEGRATOR (rare): regenerate contracts/fixtures/api/*.json from the current data/
	$(PY) tools/integrate/gen_api_fixtures.py

inbox: ## read the other agents' latest handoff notes (no merge)
	@bash tools/integrate/inbox.sh
