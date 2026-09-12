# Handoffs: DATA (P1). Only P1 edits this file. Newest entry first.

## Status
| item | value |
|---|---|
| core dishes written / manifest | 70 / 70 (all skeletons `confidence: draft`) |
| dishes `confidence: reviewed` | 0 |
| ingredients | 153 (0 with seed_placeholder; 49 still `profile: {}`, awaiting grok drafts) |
| grounded (non-seed) value share | 100% (338/338) — usda 209, team 126, literature 41, scoville 2 |
| sanity set | frozen (`sanity-lock`); data agent does not edit `data/sanity/**` |

## Log
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
