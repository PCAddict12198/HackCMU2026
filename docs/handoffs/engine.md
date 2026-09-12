# Handoffs: ENGINE (P2). Only P2 edits this file. Newest entry first.

## Endpoint readiness (fixture = canned, baseline = real engine / simple, real = tuned)
| endpoint | status | notes |
|---|---|---|
| GET /api/health | baseline | build/data/grok flags |
| GET /api/space | baseline | PCA-3D; sparse-dim calibration fixed |
| GET /api/twins | baseline | adaptive ladder; clear note for single-dish courses |
| POST /api/shift | baseline | direction ladder; 0.3 ms/call at 300 dishes |
| GET /api/explain | baseline | exact attributions |
| POST /api/recipe | baseline | regex + fuzzy; Grok mapper when configured |
| POST /api/ask | baseline | Grok tool-calling; 503 grok_unavailable without key |

## Log
## H9 · build report: data gaps · READY
- what: build/report.md now has "Data gaps (fill these first)": the 79 empty-profile ingredients ranked by
  impact (recipe share x potency) plus dishes >= 50% unprofiled. Top today: dashi, red_wine, lamb, salmon,
  rice, hoisin, duck; 18 dishes (peking_duck 85%, teriyaki_salmon 81%, masala_dosa 80%, miso_soup 79%, ...)
- for: data
- action: fill ingredients in that order (`make build`, then read the section); it re-ranks as you go

## H8 · integrator smoke · REQUEST
- what: real mode (70 dishes): most galaxy stars render as large BLACK discs, only a few are colored.
  Mock mode (16 dishes) looked fine. Suspect the instanced Stars in Galaxy.tsx (instanceColor set after the
  material compiled, or per-instance scale). Repro: `make dev`, select any dish
- for: web
- action: fix on agent/web; mock-mode repro should be `?mockLarge=1` (80 dishes)

## H8 · integrator smoke · READY
- what: h8 merged all 3 branches; first build on real skeletons: sanity positive 2/10, negative 9/10
  (several positives at the 76-85th pct). Expected: 79 ingredients have empty profiles, the rest are seed values
- for: data
- action: don't tune to the sanity set; fill real values (USDA + Grok drafts) and re-read build/report.md

## H0+ · Grok live · REQUEST
- what: new optional env var GROK_REASONING_EFFORT (default "low"; "default" = don't send). Also: a
  pasted `GROK_MODEL=GROK_MODEL=grok-4.6` line broke every call; errors now say "Model not found: ..."
- for: integrator
- action: add `GROK_REASONING_EFFORT=` to .env.example; tell teammates to paste only the value after `=`

## H0+ · Grok live · READY
- what: live xAI verified (grok-4.6): Ask picks the right tools and every reply was grounded; mapper stays
  in the closed vocabulary (no match for miso/dragon fruit, correctly). Ask 11 s -> ~5 s with low reasoning
  effort; mapper 17 s -> 4 s. Explain now reports shared strengths (not dims both lack) and rounded values;
  duplicate select_dish actions removed. Opt-in live tests: `GROK_LIVE=1 uv run pytest backend/tests/live`
- for: web
- action: Ask takes ~5 s: show a "Grok is thinking" state; `grok_failed` errors now carry the real reason

## H0+ · recipe parser pass 1 · REQUEST
- what: recipe input "6 cups water" is reported unmatched: there is no water ingredient
- for: data
- action: add `water` (category liquid, empty profile) with aliases like "ice water", so recipes with
  water count it as bland volume instead of a coverage miss

## H0+ · recipe parser pass 1 · READY
- what: parser now handles 1½ (mixed unicode fractions), "2 x 400g can", "200g/7oz", "a handful of",
  "juice of 2 limes", "salt and pepper to taste" (split into two lines), container words (can/tin/jar)
- for: web
- action: none; RecipeResponse shape unchanged, coverage is just higher on messy recipes

## H0+ · engine hardening pass 1 · READY
- what: calibration now uses only dishes that HAVE each dim (sparse dims like smoky were pinning every
  smoky dish near 1; smoky spread on seed data 0.15 -> 0.32). Empty-course twins note. New tests.
- for: data, web
- action: none needed; dish vectors shift slightly on the next `make build`. Perf: shift 0.3 ms,
  twins 0.6 ms at 300 dishes (budget 50 ms). Weight tuning waits for real data after h8.

## H0 · scaffold · READY
- what: all 7 endpoints live on seed data; 41 tests (Grok faked)
- for: web
- action: build against mock fixtures until h8; then `make dev` for real mode
