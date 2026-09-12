# DATA-DISHES helper agent (branch `agent/data-dishes`), e.g. Cursor / Codex

A second data agent working in parallel with P1. **P1 owns the 70 core dishes and all ingredients. You add
extended-tier dishes.** The split is by folder, so the two of you can never edit the same file.

**You own:** `data/dishes/extended/<cuisine>.yaml` (one file per cuisine, e.g. `thai.yaml`) and
`docs/handoffs/data-dishes.md`.
**Never modify:** anything else: `data/dishes/core/**`, `data/ingredients/**`, `data/lexicon/**`,
`data/sanity/**`, `data/formats.yaml`, `data/processes.yaml`, or anything outside `data/`. The git pre-commit
hook and CI enforce this. Never bypass them (`--no-verify` is forbidden).

## Why extended dishes
The core 70 are reviewed and drive calibration, sanity checks and the demo. Extended dishes make the galaxy
richer (more stars, more twin candidates) without touching any of that: the engine never calibrates on them,
and they only appear when the app runs with `DATA_TIER=all`. They show as dimmer stars.

## Your job: ~5 well-known dishes per cuisine (about 50 total)
Cuisines: japanese, chinese, korean, thai, vietnamese, indian, levantine, italian, french, mexican.
For each dish, copy the format of a core file (e.g. `data/dishes/core/thai.yaml`):
1. `id` unique across ALL dishes (check core files and the manifest), `tier: extended`, `confidence: draft`.
2. **Canonical recipe, grams only.** One well-known, typical version with realistic ratios, because flavor is
   computed from each ingredient's share of the grams. Include potent ingredients (sauces, spices, herbs, citrus)
   at realistic small amounts.
3. **Processes per ingredient** from the frozen list: raw, boiled, simmered, braised, steamed, grilled, roasted,
   fried, deep_fried, smoked, caramelized, toasted, fermented, pickled, cured (applied in order).
4. `format` and `course` from `data/formats.yaml` (course: savory or dessert), a one-sentence `blurb`, and a
   `recipe_basis` (where the recipe comes from).
Prefer dishes that are distinct from the core ones (not a second ramen). Include a few desserts: the dessert
course has only 10 core dishes.

## Ingredients
Use ONLY ingredient ids that already exist in `data/ingredients/*.yaml`; the validator rejects anything else. If
a dish needs a missing ingredient, either pick another dish or list it as a REQUEST for P1 in
`docs/handoffs/data-dishes.md`. Never add ingredients yourself.

## Rules
- Never tune a recipe to make a sanity or demo pair come out a certain way.
- YAML: quote any text containing a comma or colon.
- One cuisine file at a time. Before every commit: `make check-data`, plus
  `uv run python -m tastespace.build --tier all --out-dir build/all` to confirm your dishes build.
  Commit `[data-dishes] <cuisine>: N extended dishes`, then `git push origin HEAD`.
- Start every session with `make inbox`. Never push `main`, never rebase, never force-push, never merge other branches.
- Refresh only after the integrator announces a checkpoint: `git fetch origin && git merge --no-edit origin/main`.

## Kickoff prompt (paste into Cursor / Codex)
> You are the DATA-DISHES helper agent for TasteSpace. Read AGENTS.md and docs/agents/data-dishes.md
> completely, then docs/MODEL.md sections 3-4, data/formats.yaml, data/processes.yaml, one core dish file
> (data/dishes/core/thai.yaml) as a format example, and the ingredient ids in data/ingredients/*.yaml.
> Confirm `git branch --show-current` prints agent/data-dishes. Run `make inbox` and `make check-data`.
> Then add about 5 well-known extended-tier dishes per cuisine, one new file per cuisine in
> data/dishes/extended/<cuisine>.yaml (tier: extended, confidence: draft), following "Your job" in
> docs/agents/data-dishes.md. Only edit data/dishes/extended/*.yaml and docs/handoffs/data-dishes.md. Use
> only existing ingredient ids and unique dish ids; list missing ingredients as REQUESTs for P1 in
> docs/handoffs/data-dishes.md. Before each commit run `make check-data` and
> `uv run python -m tastespace.build --tier all --out-dir build/all`; commit
> "[data-dishes] <cuisine>: N extended dishes" and `git push origin HEAD`. Never use --no-verify, never push
> main, never rebase or merge other branches.
