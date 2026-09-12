# DATA-DISHES helper agent (branch `agent/data-dishes`), e.g. Cursor / Codex

A second data agent that works in parallel with P1. **P1 owns ingredients; you own dish recipes.** The
split is by file, so the two of you can never edit the same file.

**You own:** `data/dishes/core/<cuisine>.yaml` (the 10 cuisine files) and `docs/handoffs/data-dishes.md`.
**Never modify:** `data/dishes/core/_manifest.yaml` (the agreed dish list), `data/ingredients/**`,
`data/lexicon/**`, `data/sanity/**`, `data/formats.yaml`, `data/processes.yaml`, and anything outside `data/`.
The git pre-commit hook and CI enforce this. Never bypass them (`--no-verify` is forbidden).

## Your job: turn 70 draft skeletons into reviewed canonical recipes
For each dish in each cuisine file:
1. **Canonical recipe, grams only.** Use one well-known, typical version of the dish (not a fusion or
   restaurant twist). Realistic ratios matter, because a dish's flavor is computed from each ingredient's share of the grams.
   Include the potent ingredients (sauces, spices, herbs, citrus) at realistic amounts, even if they're small.
2. **Processes per ingredient**, from the frozen list: raw, boiled, simmered, braised, steamed, grilled,
   roasted, fried, deep_fried, smoked, caramelized, toasted, fermented, pickled, cured. They are applied in order.
   Example: onion for French onion soup is `[caramelized]`, not raw.
3. **format + course.** Check them against `data/formats.yaml` (soup, noodles, stew_braise, fried, ...).
4. **blurb:** one plain sentence. **recipe_basis:** where the recipe comes from (a named cookbook or site,
   or "common home recipe, cross-checked with 2 sources").
5. Set `confidence: reviewed` only after steps 1-4 are done for that dish.

## Ingredients you need but that don't exist yet
Use ONLY ingredient ids that already exist in `data/ingredients/*.yaml`. The validator rejects anything else.
If the right ingredient is missing, use the closest existing one, add `note: "wanted <x>"` on that line, and
list it in `docs/handoffs/data-dishes.md` as a REQUEST for P1. Never add ingredients yourself.

## Rules
- Never tune a recipe to make a sanity pair or demo pair come out a certain way.
- YAML: quote any text containing a comma or colon.
- Work one cuisine file at a time. Run `make check-data` before every commit. Commit
  `[data-dishes] <cuisine>: ...` after each cuisine, then `git push origin HEAD`.
- Start every session with `make inbox`. Never push `main`, never rebase, never force-push, never merge other branches.
- Refresh only after the integrator announces a checkpoint: `git fetch origin && git merge --no-edit origin/main`.

## Kickoff prompt (paste into Cursor / Codex)
> You are the DATA-DISHES helper agent for TasteSpace. Read AGENTS.md and docs/agents/data-dishes.md
> completely, then docs/MODEL.md sections 3-4, data/formats.yaml and data/processes.yaml. Confirm
> `git branch --show-current` prints agent/data-dishes. Run `make inbox` and `make check-data`.
> Then review the dish recipes in data/dishes/core/ one cuisine file at a time (japanese.yaml first),
> following "Your job" in docs/agents/data-dishes.md: realistic canonical grams, per-ingredient processes,
> correct format/course, blurb, recipe_basis, then confidence: reviewed. Only edit
> data/dishes/core/<cuisine>.yaml (never _manifest.yaml) and docs/handoffs/data-dishes.md. Use only existing
> ingredient ids; list missing ones as REQUESTs for P1 in docs/handoffs/data-dishes.md. Run `make check-data`
> before every commit, commit "[data-dishes] <cuisine>: ..." after each cuisine and `git push origin HEAD`.
> Never use --no-verify, never push main, never rebase or merge other branches.
