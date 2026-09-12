# P3: WEB agent (branch `agent/web`)

**You own:** `web/**` (ALL runtime frontend code, including `package.json` / `package-lock.json`), `docs/handoffs/web.md`
**Read, never modify:** `contracts/**` (generated types + fixtures), `backend/**`, `data/**`, `Makefile`

## Data source: mock first, real later
- `.env` has `VITE_API_MODE=mock`, so the app runs on `contracts/fixtures/api/*.json` with no backend needed.
  `make web`, then open http://localhost:<WEB_PORT>.
  - `?mockLarge=1` gives an 80-dish synthetic galaxy (layout/performance)
  - `?mockError=not_found` (or any error code) shows error states
  - `?mockError=grok_unavailable` hides Ask
  - `?mockLatency=800` shows loading states
- After the h8 merge: `make dev` runs the real API + web together (`VITE_API_MODE=real`).
- Mock mode must keep working forever. It is the demo fallback.

## Types
Import API types only from `src/contract.ts` (re-exports `@contracts/generated/api`). Never hand-write API
shapes, and never edit `contracts/`. If you need a field that doesn't exist: REQUEST to integrator, then build
the UI against the fixture and a local optional fallback.

## Feature folders (each has a README with its TODO list)
`src/features/galaxy` · `twins` · `shift` · `explain` · `recipe` · `ask`. The shared pieces are `src/api/*`
(mock/real client), `src/state/store.ts`, and `src/state/uiActions.ts` (the ONLY place Ask actions change state).

## Rules
- Handle every `ErrorCode` (`validation_error`, `not_found`, `not_ready`, `grok_unavailable`, `grok_failed`,
  `internal`) plus `network`.
- Similarity is a percentile ("closer than 93% of pairs"). Never show a fake percentage.
- Hide the Ask tab when `health.grok_configured` is false.
- Show provenance chips (`src`) wherever ingredient values appear.
- You may add JS dependencies (you own the lockfile). Commit `package.json` + `package-lock.json` together.

## Timeline
H0-3 app shell + galaxy (instanced stars, colors, hover labels, click-select, camera fly-to) ·
H3-5 Twins + Explain panels (radar, attribution bars, provenance chips) ·
H5-8 Shift (sliders -> debounced shift -> smooth target glide), Recipe + Ask UIs on mocks ·
H9-12 real mode, loading/error states, Ask actions animate the galaxy ·
H12-16 polish, recipe star in galaxy, PCA axis labels, projector-size check ·
H17-20 demo mode (keyboard shortcut per demo step, "reset view").

## Before every commit
`make check-web` (typecheck + vitest)

## Kickoff prompt (paste into your agent)
> You are the P3 WEB agent for TasteSpace. Read AGENTS.md and docs/agents/web.md completely, then
> web/src/contract.ts, web/src/api/*, web/src/state/* and every README in web/src/features/.
> Confirm `git branch --show-current` prints agent/web. Run `make inbox` and `make check-web`, then
> `make web` (mock mode). Work through the Timeline in docs/agents/web.md, one feature folder at a time.
> Only edit web/** and docs/handoffs/web.md. Use only types from src/contract.ts; never edit contracts/.
> Keep mock mode working. Run `make check-web` before every commit; commit "[web] ..." every
> 30-60 minutes and `git push origin HEAD`. Keep the panel readiness table in docs/handoffs/web.md current.
