# TasteSpace: rules for every AI coding agent (read ALL of this before doing anything)

Three people build TasteSpace at the same time, each with their own agent on their own branch. These
rules keep agents from blocking or breaking each other. Only the **integrator** merges into `main`, at
checkpoints (H8, H16, H20, final). OWNER of this file: integrator.

## 1. Find your role (first thing, every session)
Run `git branch --show-current`:

| branch | role | then read |
|---|---|---|
| `agent/data` | **data** (P1) | `docs/agents/data.md` |
| `agent/engine` | **engine** (P2) | `docs/agents/engine.md` |
| `agent/web` | **web** (P3) | `docs/agents/web.md` |
| `agent/data-dishes` | **data-dishes** (helper agent, e.g. Cursor/Codex) | `docs/agents/data-dishes.md` |
| `main` | **integrator**, only if the human explicitly said so; otherwise STOP and ask | `docs/agents/integrator.md` |

Any other branch: stop and ask the human.

## 2. Ownership (enforced by a Claude Code hook, a git pre-commit hook and CI)
You may READ anything. You may MODIFY only your role's paths (machine-readable in `OWNERS.json`):

- **data**: `data/**` (except `data/sanity/**`, frozen, and the core dish files below), `tools/data/**`, `docs/demo/**`, `docs/handoffs/data.md`
- **data-dishes** (helper): `data/dishes/core/<cuisine>.yaml` (not `_manifest.yaml`), `docs/handoffs/data-dishes.md`
- **engine**: `backend/tastespace/**`, `backend/tests/**` (existing files in `backend/tests/fixtures/data/` are append-only), `docs/MODEL.md`, `docs/handoffs/engine.md`
- **web**: `web/**` (including `package.json` / `package-lock.json`), `docs/handoffs/web.md`
- **integrator** (on `main` only): everything else: `contracts/**`, `pyproject.toml`, `uv.lock`, `backend/pyproject.toml`, `Makefile`, `.github/**`, `.githooks/**`, `.claude/**`, `tools/ci/**`, `tools/integrate/**`, `OWNERS.json`, `AGENTS.md`, `CLAUDE.md`, `docs/agents/**`, `docs/CONTRACTS.md`, `docs/INTEGRATION.md`, `docs/TASKS.md`, `README.md`, `.gitignore`, `.env.example`

**Do not "helpfully" fix files outside your area**, even obvious bugs. File a REQUEST (section 4).

## 3. Never
- push to `main`, force-push, rebase, `git reset --hard`, delete branches, use `--no-verify`
- merge another agent's branch (only the integrator merges, at checkpoints)
- edit `contracts/**` or regenerate `contracts/fixtures/**` / `contracts/generated/**`
- add or remove Python dependencies (`uv add`, `pip install`): integrator only. JS dependencies: web only
- commit `.env` or secrets, or print API keys
- change `data/sanity/**` (frozen at `h0-freeze`)

## 4. When you need something from another area
1. Append an entry at the top of YOUR handoff file `docs/handoffs/<your role>.md`.
2. Commit + push your branch.
3. Work around it (mock, fixture, stub) and keep going. Never sit and wait.

```
## 14:05 · a1b2c3d · REQUEST | READY | BLOCKED | BREAKING | DATA-ISSUE
- what: one line
- for: data | engine | web | integrator
- action: what you want them to do
```

## 5. Every session and every commit
- **Start:** `make inbox` shows the other roles' latest handoffs without merging anything.
- **Before each commit:** `make check-<role>` (`check-data` / `check-engine` / `check-web`). Fix failures in YOUR files.
- **Commit small, every 30-60 min:** `git commit -m "[data] ..."`, then `git push origin HEAD`.
- **After "main @ hN ready":** `git fetch origin && git merge --no-edit origin/main && make setup && make check-<role>`
  (single-machine setup without a remote: `git merge --no-edit main`). Never rebase.

## 6. Contracts are the law
Interfaces are frozen in `contracts/`: pydantic models -> `contracts/openapi.json` ->
`contracts/generated/api.d.ts`, plus canonical fixtures in `contracts/fixtures/api/`. If what you need
conflicts with the contract, the contract wins: file a REQUEST and keep working against the current
contract. Additive changes ship fast as integrator hotfixes (see `docs/CONTRACTS.md`).

## 7. Grok (xAI) rules: "Grok is the interface, the engine is the judge"
- Grok never computes similarity and never supplies sensory values used at runtime.
- The Ask agent calls engine tools; every number in a reply must come from a tool result (enforced).
- The ingredient mapper can only answer with ids from the ontology (enum).
- Grok-drafted priors go to `data/drafts/` first; canonical data changes only after human review.
- Everything except Ask must work with `XAI_API_KEY` unset. Tests mock Grok; no network in tests.

## 8. Commands
`make help` · `make setup` · `make build` · `make api` · `make web` · `make dev` · `make check-<role>` · `make inbox`
