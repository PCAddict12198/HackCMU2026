# Handoffs: DATA (P1). Only P1 edits this file. Newest entry first.

## Status
| item | value |
|---|---|
| core dishes written / manifest | 70 / 70 (all skeletons `confidence: draft`) |
| dishes `confidence: reviewed` | 0 |
| ingredients | 153 — every one profiled except `water` (correctly zero on every dim) |
| grounded (non-seed) value share | 100% (525/525) — usda 266, team 236, literature 66, grok_reviewed 8, scoville 2 |
| sanity set | frozen (`sanity-lock`); data agent does not edit `data/sanity/**` |

## Log
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
