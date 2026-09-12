# P2: ENGINE agent (branch `agent/engine`)

**You own:** `backend/tastespace/**`, `backend/tests/**` (existing files in `backend/tests/fixtures/data/` are
append-only: add new fixture files, never change old ones), `docs/MODEL.md`, `docs/handoffs/engine.md`
**Read, never modify:** `contracts/**` (the pydantic models ARE the API), `data/**`, `web/**`, `Makefile`,
`backend/pyproject.toml`, `uv.lock`. P2 is also the integrator, but integration happens in a SEPARATE
session on `main` (`docs/agents/integrator.md`), never on this branch.

## What you inherit (working + tested)
`engine/aggregate.py` (saturating aggregation, exact attribution) · `transforms.py` · `space.py` (weighted
z-space, percentile similarity, PCA) · `twins.py` (adaptive ladder) · `shift.py` (direction ladder) ·
`explain.py` · `recipe.py` · `build.py` + `report.py` · `api.py` (all 6 routes + health, contract errors) ·
`grok/` (xai_sdk client, tool-calling agent, grounding, closed-vocabulary mapper).

## Tasks
- **H0-3, engine hardening:** dim weights (`space.DEFAULT_WEIGHTS`), calibration quantile, twin/shift ladders,
  shared/diff dims, edge cases (tiny courses, identical dishes). Shift must stay under 50 ms.
- **H3-5, recipe parser:** more units/descriptors ("a handful of", "1 x 400g can"), better fuzzy matching,
  process words, clearer coverage notes. Test with the fixture lexicon.
- **H5-8, Grok:** run a live smoke test with your key (`GROK_LIVE=1`, never in CI), tune the system prompt and
  tool descriptions, check grounding templates, try the ingredient mapper live. Update `engine.md` readiness.
- **H9-16, on REAL data (after the h8 merge):** read `build/report.md`, tune weights/ladders. Never edit
  data or the sanity pairs. At H16: `uv run python -m tastespace.build --freeze-calibration`.
- Keep `docs/MODEL.md` accurate. It is the "how it works" slide source.

## Contract rules
- Route paths, parameters and response models are frozen. `make check-contracts` fails if the OpenAPI output
  changes, and that includes route docstrings, so keep route functions docstring-free.
- Need a new field or endpoint? REQUEST to integrator. Additive changes ship as a hotfix to `main`; merge `main` when announced.
- Tests read only `backend/tests/fixtures/data`, never `data/`. Grok is always faked (`tests/fakes/fake_grok.py`).

## Grok rules (GrokBot prize: judges scan the code for meaningful Grok use)
All Grok code stays in `backend/tastespace/grok/`, documented. Grok never computes similarity and never
supplies runtime sensory values. Ask replies are grounded (`grounding.py`); `ui_actions` are derived from
the tool trace; the mapper only returns ontology ids. Every endpoint except `/api/ask` works with no key.

## Before every commit
`make check-engine` (ruff + pytest, no network)

## Kickoff prompt (paste into your agent)
> You are the P2 ENGINE agent for TasteSpace. Read AGENTS.md, docs/agents/engine.md, docs/MODEL.md and
> docs/CONTRACTS.md completely. Confirm `git branch --show-current` prints agent/engine. Run `make inbox`
> and `make check-engine`. Then work through the Tasks list in docs/agents/engine.md in order. Only edit
> backend/tastespace/**, backend/tests/**, docs/MODEL.md and docs/handoffs/engine.md. Never change the
> pydantic contracts or route signatures; if you need an API change, write a REQUEST in
> docs/handoffs/engine.md. Tests must use backend/tests/fixtures only and fake Grok. Run
> `make check-engine` before every commit; commit "[engine] ..." every 30-60 minutes and
> `git push origin HEAD`. Keep the endpoint readiness table in docs/handoffs/engine.md current.
