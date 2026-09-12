# Handoffs: DATA (P1). Only P1 edits this file. Newest entry first.

## Status
| item | value |
|---|---|
| core dishes written / manifest | 70 / 70 |
| dishes `confidence: reviewed` | 70 / 70 |
| ingredients | 155 — `fresh_chili` split into `chili_mild`/`chili_hot`; `water` is correctly empty |
| grounded (non-seed) value share | 100% (665/665) — team 245, usda 213, grok_reviewed 136, literature 66, scoville 5 |
| rating study (H15) | 20 pairs picked and wired; **needs the three of us to rate 1-5** |
| sanity set | frozen (`sanity-lock`); data agent does not edit `data/sanity/**` |

## Log
## 11:42 · 6d1b4e6 · BLOCKED
- what: the H15 rating study is set up but cannot be finished by the data agent. `data/validation/ratings.yaml`
  now holds 20 core pairs, picked from the 70 dishes before looking at any model score and deliberately
  avoiding all 20 `data/sanity` pairs (whose scores P1 had already seen), so the set is independent of both
  the frozen sanity set and the engine. Step 2 of `docs/demo/rating_study.md` is "each teammate rates every
  pair 1-5 **alone, without looking at the app**" — those are three humans' judgements and inventing them
  would make the validation slide a measurement of P1's taste against the engine, which is circular. The
  pipeline is verified end to end: synthetic ratings in a throwaway copy produced "20 rated pairs ·
  Spearman rho = 0.03" (random input -> rho ~ 0, the negative control we want), so the maths works and only
  the numbers are missing.
- for: data | engine | web
- action: each of the three of us opens `data/validation/ratings.yaml`, rates all 20 pairs top to bottom on
  instinct without opening the app, and adds one `ratings` key per person. Then `make build` prints the real
  rho under "Human ratings vs model". The intended mix was 7 likely-similar, 7 likely-different and 6
  genuinely-uncertain pairs — recorded here rather than in the file so reading the file cannot bias a rater.

## 11:42 · 6d1b4e6 · DATA-ISSUE
- what: the additive Grok promotion in 932beae moved two frozen sanity pairs the wrong way, and it is worth
  knowing why before H16. Isolated by building HEAD's data on its own (`--data-dir` on a `git archive`
  export) and comparing: tiramisu/tres_leches 33.3 -> 13.3 pct, and beef_bourguignon/mole_poblano
  91.7 PASS -> 78.5 FAIL. The mechanism is narrow — of the 11 ingredients in those two desserts, Grok
  touched exactly two dims: `espresso` gained `smoky 0.2` + `earthy 0.15`, `cinnamon` gained `fruity 0.15`.
  `smoky` is one of the sparse dims MODEL.md section 4 warns about (calibration uses only dishes that have
  the dim), so giving espresso any smoky value makes tiramisu one of the only smoky desserts and pushes it
  to the edge of that axis, away from tres_leches.
- for: engine
- action: your call, not ours — we are deliberately NOT deleting espresso's smoky value to rescue a frozen
  pair (dark-roast coffee genuinely does read a little smoky). Please judge whether sparse-dim calibration
  should damp a single-dish dim like this. If you want the value gone on modelling grounds, say so in your
  handoff and we will remove it as a modelling decision rather than a score fix.

## 11:42 · 6d1b4e6 · READY
- what: the three gaps this agent had flagged are fixed. (1) `fresh_chili` is split into `chili_mild`
  (jalapeño 2.5k-8k / serrano 10k-23k SHU, spicy 0.45, unit 12 g) and `chili_hot` (Thai bird's eye
  50k-100k SHU, spicy 0.85, unit 2 g); 10 dishes were repointed on culinary grounds — hot for
  chana_masala, masala_dosa, aguachile, tom_yum_goong, green_curry, som_tam, larb; mild for
  butter_chicken, bun_cha, banh_mi. `fresh_chili` stays as the generic fallback so a pasted recipe saying
  only "chili" still maps. (2) `pork_shoulder` re-matched to the Boston butt row (rich 0.13 -> 0.39).
  (3) Reviewed the 145 new `grok_reviewed` values and corrected 9 of them: Grok had put `rich` on
  fat-free condiments (shrimp_paste 0.6, pomegranate_molasses 0.4, okonomiyaki_sauce 0.4, gochujang 0.35 —
  `rich` is the fat map in MODEL.md) and `brothy` on thin seasonings (soy_sauce 0.5, fish_sauce 0.55 at
  potency 6-7), which made 19 non-soup dishes including two raw salads and a sandwich read brothy. Brothy
  is liquid body: it belongs to stocks and to the soup format vector. Each corrected value says so in its
  note. Deliberately left alone: macro dims are not claimed for any chili, because potency multiplies every
  dim (section 4) and the USDA sugar figure would let a 5 g garnish sweeten a dish like a sweetener.
- for: engine
- action: none. My own earlier prediction was wrong and the record should show it: I expected raising
  som_tam's heat to push tabbouleh/som_tam further apart, but my changes moved it 62.1 -> 67.2 (closer),
  because som_tam's fish sauce also stopped contributing brothy. No pair flipped either way on my changes;
  net stayed 4/10 positive and 9/10 negative.
## 11:28 · agent/data · READY
- what: `.env` `GROK_MODEL` is now a real model id (`grok-*`, not a doubled `GROK_MODEL=` prefix). USDA and xAI keys still set. Grok drafts can load from dotenv without a shell workaround.
- for: data
- action: none

## 11:30 · agent/data · READY
- what: H3-5 USDA + Grok fill done. USDA `--all` matches were reviewed; only 72 verified FDC hits promoted. Grok aroma/mouthfeel drafted for all 153, then promoted **only missing dims** (77 ingredients) as `grok_reviewed` so USDA/literature/scoville/team values were not overwritten. Engine REQUEST: added `water` (empty profile, ice/tap aliases).
- for: engine | web
- action: none; `GROK_MODEL` in `.env` was `GROK_MODEL=grok-4.6` (doubled) — integrator should fix the line to `GROK_MODEL=grok-4.6` (data cannot edit `.env`). Workaround: export `GROK_MODEL=grok-4.6` in the shell.

## 11:14 · 279a2b5 · BREAKING
- what: `data/drafts/ingredients/grok_20260912_105317.yaml` has grown to 120 ingredients, and 94 of them
  are ingredients that are already reviewed and sourced. `promote_draft.py` overwrites the dims it is
  given, so running it on that draft WITHOUT `--only` would replace 94 ingredients' verified values with
  model estimates — e.g. it rates almonds `rich` 0.4 where the USDA row (fat 49.9 g/100g) gives 0.86 next
  to peanuts 0.86 / walnuts 0.93 on the same axis.
- for: data
- action: whoever is running that script — promote it with `--only <the still-unprofiled ids>`, or not at
  all. Every canonical ingredient already has provenance; there is nothing left for it to fill.

## 11:14 · 279a2b5 · READY
- what: all 70 core dishes are `confidence: reviewed`. Each was checked for ingredients, grams, processes,
  format and course against a canonical recipe; the 16 dishes still labelled `recipe_basis: seed
  placeholder` now name their real serving basis (the recipes themselves were sound — the label was
  stale, not the data). One factual fix: `tacos_al_pastor` was missing achiote, which with guajillo *is*
  the al pastor adobo — `cochinita_pibil` already set that precedent. Nothing else needed changing.
- for: engine | web
- action: none; `tier: core` is now fully reviewed data and safe to demo against.

## 11:14 · 279a2b5 · DATA-ISSUE
- what: sanity moved while marking dishes reviewed, and not uniformly in our favour. positive 3/10 -> 4/10
  (beef_bourguignon/mole_poblano 85.8 -> 91.7 now PASS), but tiramisu/tres_leches got WORSE (40.0 -> 33.3)
  and the failing negative pho_bo/margherita_pizza got worse too (56.3 -> 68.0). The only maths-affecting
  change in this commit is 4 g of achiote in one dish: thresholds are percentile-based, so one added
  ingredient shifts the reference distribution under every pair. The recipes were reviewed on culinary
  merit and the build was run once afterwards — no pair was tuned for, and `data/sanity/**` is untouched
  (the lock still verifies).
- for: engine
- action: read the positive rate as noisy at this granularity — a single ingredient in an unrelated dish
  moves it by a pair. tiramisu/tres_leches at 33.3 remains the most diagnostic miss.

## 11:06 · 6e96633 · DATA-ISSUE
- what: the USDA fuzzy matcher is not safe to promote unreviewed on the non-Western tail of the ontology.
  `usda_fill.py` searches `pageSize=1` on the bare ingredient name and takes hit #1, which gave
  salmon -> salmon OIL, peanuts -> peanut OIL, duck -> duck LIVER, spinach -> spinach SOUFFLE,
  long_bean -> cellophane NOODLES, rice/wheat_noodles -> rice noodles, rice_cake (tteok) -> puffed rice
  CRACKER, sweet_potato_noodles -> sweet potato LEAVES, tamarind -> tamarind CANDY. 33 of 38 matches in
  `data/drafts/ingredients/usda_20260912_105532.yaml` were the wrong food, so that draft was rejected
  whole rather than promoted. Re-querying FDC with full descriptions ("Fish, cod, Atlantic, raw") hits
  the right row nearly every time.
- for: data
- action: if anyone extends the corpus, query with a full USDA-style description and read the match
  before promoting. The rejected draft is kept in `data/drafts/` as the record.

## 11:06 · 6e96633 · READY
- what: ingredient profiles are complete — the 49 remaining `profile: {}` ids are filled and every value
  in the corpus carries provenance. 20 ingredients got verified FDC rows (fdc id in the note) through the
  MODEL.md maps; documented chemistry is `literature` (kombu/katsuobushi umami synergy, tartaric acid in
  tamarind, malic acid in sumac, EGCG in matcha, laver glutamate, oxalic astringency in spinach);
  everything else is `team` with its basis in the note. 8 values are `grok_reviewed` (texture dims for
  achiote/almonds/avocado kept from the grok draft after review). `water` stays at `profile: {}` on
  purpose. Dish `confidence` is still `draft` — that is the next step, not done here.
- for: engine
- action: none required. Worth knowing: grok rated almonds `rich` 0.4 by feel where the USDA row gives
  0.86 (peanuts 0.86, walnuts 0.93 on the same axis), so model-proposed macro values are not used.

## 11:06 · 6e96633 · REQUEST
- what: positive sanity pairs moved 2/10 -> 3/10 as a side effect of the profile fill (no pair was tuned
  for — `data/sanity/**` untouched and the lock still verifies). The standout miss is
  tiramisu/tres_leches at 40.0 pct, far below the other positives; both are sweet dairy desserts, so the
  espresso/cocoa bitter-roasted axis in tiramisu may be dominating the distance.
- for: engine
- action: if the positive rate matters for the demo, tiramisu/tres_leches is the most diagnostic pair to
  look at first — please judge whether that is dim weighting or genuinely honest output before H16.
## 11:00 · 3fffa4e · DATA-ISSUE
- what: three provenance artifacts worth knowing before anyone reads engine output as truth.
  (1) `fresh_chili` / `chili_flakes` each bundle a huge Scoville range under one id (jalapeño ~2.5k-8k SHU
  vs. Thai bird's eye ~50k-100k SHU); the single `spicy` value is a real approximation and som_tam, larb
  and dan_dan_noodles all hinge on that difference. (2) `cumin` rich 0.59 and `mustard_seeds` rich 0.76 come
  from whole-seed fat (22-36 g/100g) via the MODEL.md `rich` formula — nutritionally correct, sensorially
  wrong for a spice. (3) `pork_shoulder` matched USDA "Shoulder breast, boneless" (3.4 g fat), not a
  braising butt (~20 g fat), so rich reads 0.13 where carnitas/ragù want ~0.4.
- for: data | engine
- action: data — consider splitting into `chili_mild` / `chili_hot` and re-matching pork_shoulder if H9-12
  time allows. engine — no change requested; flagging so spice `rich` is not read as a bug in your weighting.

## 11:00 · 3fffa4e · READY
- what: ingredient provenance pass — every seeded `profile` value now carries `{v, src, note}`. USDA values
  computed from the MODEL.md formulas with the raw nutrient figure in the note so they stay auditable;
  `literature` for documented food chemistry (capsaicin, piperine, glutamate, citric acid, vanillin);
  `team` for texture dims and condiments with no canonical composition. No value is labeled `usda` unless a
  nutrient figure backs it. 0 `seed_placeholder` values remain.
- for: engine
- action: none; profiles for the 49 remaining `profile: {}` ids are next (grok drafts + review)
## 10:55 · 5f1a383 · REQUEST
- what: USDA_API_KEY and XAI_API_KEY are unset locally; H3-5 fill/draft scripts cannot run
- for: integrator
- action: put keys in `.env` (not committed) so P1 can run `usda_fill.py --all` and `grok_draft_ingredients.py`

## 10:50 · agent/data · READY
- what: remaining 26 skeletons (indian, levantine, italian, french, mexican) — full 70-dish core present
- for: engine
- action: none; next is USDA fill + grok drafts for empty-profile ingredients (H3-5)

## 10:35 · agent/data · READY
- what: first 35 manifest skeletons done (japanese through vietnamese); remaining 35 are IN/LEV/IT/FR/MX
- for: engine
- action: none; unknown-id list is now the ingredient-profile to-do (empty `profile: {}` ids)

## 10:15 · agent/data · READY
- what: japanese core complete (7/7) — added shoyu_ramen, miso_soup, teriyaki_salmon, okonomiyaki, matcha_ice_cream skeletons
- for: engine
- action: none; continue H0-3 skeletons cuisine by cuisine

## H0 · scaffold · READY
- what: seed data (73 ingredients, 16 dishes, 70-dish manifest, draft sanity pairs) validates
- for: data
- action: replace seed values; write the remaining 54 manifest dishes
