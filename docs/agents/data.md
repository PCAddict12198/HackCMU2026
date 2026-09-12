# P1: DATA agent (branch `agent/data`)

**You own:** `data/**` (except `data/sanity/**`), `tools/data/**`, `docs/demo/**`, `docs/handoffs/data.md`
**Read, never modify:** `backend/**`, `web/**`, `contracts/**`, `Makefile`, `pyproject.toml`, `uv.lock`,
`OWNERS.json`, `AGENTS.md`, `docs/agents/**`. If another subsystem needs a change: REQUEST in
`docs/handoffs/data.md`, commit, keep working.

**Since h8:** the core dish recipes (`data/dishes/core/<cuisine>.yaml`) belong to the **data-dishes helper**
(branch `agent/data-dishes`, see `docs/agents/data-dishes.md`). You own ingredients, lexicon, drafts,
extended dishes and validation. Add the ingredients the helper REQUESTs in `docs/handoffs/data-dishes.md`
(read it with `make inbox`).

## Goal
A reviewed **core** corpus: ~100 ingredients, the ~70 dishes in `data/dishes/core/_manifest.yaml`,
10 cuisines, every number with honest provenance. The demo and the validation run on core only.
Extended dishes (`data/dishes/extended/`, `confidence: draft`) are optional and never required.

## How the data works (details: `docs/MODEL.md`)
- **Ingredient profile:** intensity per dim when eaten neat, 0..1, omitted dims = 0. **potency:** how strongly
  it carries when diluted (bland starch 0.5, meat 1, cheese 2-3, soy sauce 6, dried spices 8).
- **Dish:** one canonical recipe, **grams only**, a `process` list per ingredient, one `format`, one `course`.
- **Provenance:** every value has `src` (`usda | scoville | literature | team | grok_reviewed`). Evidence goes in `note`.
- **Schema:** `contracts/src/tastespace_contracts/data_models.py` (JSON Schemas in `contracts/schemas/` give
  editor autocompletion). `make check-data` explains every error with file + id.

## Order of work (skeleton first!)
1. **H0-3:** dish skeletons for the first 35 manifest dishes (ingredients + grams + processes + format + course,
   `confidence: draft`). New ingredient ids can start with name/category/potency and an empty `profile: {}`.
2. The validator lists unknown ingredient ids, which is your ingredient to-do list.
3. **H3-5:** `uv run python tools/data/usda_fill.py --all` -> check matches -> `promote_draft.py`.
   `uv run python tools/data/grok_draft_ingredients.py --ids ... / --new ...` -> drafts in `data/drafts/` ->
   **review every value** -> `uv run python tools/data/promote_draft.py <draft> --reviewer <name>`.
4. **H5-8:** finish review/promotion; skeletons for the other 35 dishes.
5. **H9-12 (after the h8 merge):** complete all 70; fix issues flagged in `build/report.md` (`make build`).
6. Replace every `seed_placeholder` value before H16 (the validator counts them). Mark dishes `confidence: reviewed`.
7. **H15:** rating study (`docs/demo/rating_study.md`) -> `data/validation/ratings.yaml`.
8. **H16+:** slides, `docs/demo/demo_script.md` (demo pairs chosen from REAL engine output), extended tier if time.

## Rules
- `src: grok_draft` is forbidden in `data/ingredients/` (drafts live in `data/drafts/`).
- Guesses are `src: team` with a note, never `usda`.
- **Never tune data to make a sanity pair or the demo pass.** The sanity set is frozen so the results stay honest.
- YAML: quote any text containing a comma or colon (`why: "rich, creamy"`).
- Need a Python package? REQUEST to integrator. Need an engine change? REQUEST to engine.

## Before every commit
`make check-data` (validate + sanity lock + core build smoke + lint of tools/data)

## Kickoff prompt (paste into your agent)
> You are the P1 DATA agent for TasteSpace. Read AGENTS.md and docs/agents/data.md completely, then
> docs/MODEL.md. Confirm `git branch --show-current` prints agent/data. Run `make inbox` and
> `make check-data`. Then follow "Order of work" in docs/agents/data.md, starting with dish skeletons
> for the dishes in data/dishes/core/_manifest.yaml, one cuisine file at a time. Only edit data/**,
> tools/data/**, docs/demo/** and docs/handoffs/data.md. Run `make check-data` before every commit,
> commit with "[data] ..." every 30-60 minutes and `git push origin HEAD`. Keep the status table in
> docs/handoffs/data.md current. Never invent provenance: an estimate is src: team with a note.
