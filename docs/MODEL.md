# How TasteSpace computes flavor. OWNER: engine (P2)

"We built an interpretable computational representation of sensory similarity." It is an
approximation, and every number can be traced back to ingredients, preparation and a source.

## 1. Dimensions (17, each in [0, 1])
- **taste:** sweet, salty, sour, bitter, umami
- **aroma:** spicy, smoky, roasted, fermented, herbal, fruity, earthy
- **mouthfeel:** rich, creamy, crispy, chewy, brothy

## 2. Ingredients
`r_i` = intensity of each dim when the ingredient is eaten neat. `potency_i` = how strongly it carries when
diluted. Every value has provenance (`src`):
- **usda**: from USDA FoodData Central via `tools/data/usda_fill.py`:
  - sweet = 1 - exp(-sugar g/100g / 12)
  - salty = 1 - exp(-sodium mg/100g / 1500)
  - rich = 1 - exp(-fat g/100g / 25)
- **scoville**: literature heat values
- **literature**
- **team**
- **grok_reviewed**: drafted by Grok, then checked by a person. Drafts (`grok_draft`) can never be canonical.

## 3. Preparation and format
- Per ingredient, in order: `r' = clip(r * scale_p + delta_p, 0, 1)` (`data/processes.yaml`). For example,
  caramelizing adds sweet and roasted and cuts pungency.
- Per dish: a format vector `f` (`data/formats.yaml`), because mouthfeel mostly comes from technique (a soup is brothy).

## 4. Aggregation (`backend/tastespace/engine/aggregate.py`)
```
raw_k = sum_i share_i * potency_i * r'_ik      share_i = grams_i / total grams
ing_k = 1 - exp(-raw_k / s_k)                  s_k: the 90th-percentile core dish scores 0.9
D_k   = ing_k + f_k * (1 - ing_k)
```
Bland bulk (water, noodles) has `r ~ 0`, so it doesn't dilute potent ingredients the way a weighted average would.
**Attribution is exact:** ingredient i contributes `ing_k * term_ik / raw_k` and the format contributes
`f_k * (1 - ing_k)`. They sum to `D_k`, which the build report checks to within 1e-6.

## 5. Space (`engine/space.py`)
- z-score every dim over the built dishes, with per-dim weights `w_k`.
- **Distance** = `sqrt(sum_k w_k (z_ak - z_bk)^2)`.
- **Similarity** = percentile: the share of same-course dish pairs that are farther apart. It is never a cosine,
  and never presented as "84% the same taste".
- **PCA-3D** on weighted z-scores. Mean, std, components and scale are stored, so recipes and shift targets
  project linearly into the same galaxy.

## 6. Flavor Twins (`engine/twins.py`)
Same course. Candidates are filled from an adaptive ladder of similarity thresholds (90th -> 80th -> 70th
percentile -> any other cuisine -> same-cuisine fallback), and within a level they're ranked by cuisine distance
first (0 / 0.4 same region / 0.7 same macro-region / 1.0), then similarity. The response reports the level used.

## 7. Taste Shift (`engine/shift.py`)
`target = z_A + delta` (sigma units). Candidates must move the requested way on the touched dims
(all -> majority -> any). Untouched dims keep their full weight, so the result stays close to what you liked.

## 8. Recipes (`engine/recipe.py`)
regex (quantity + unit) -> `data/lexicon` units + aliases -> exact / fuzzy match -> Grok maps the leftovers onto
the closed list of ingredient ids -> grams -> the same aggregation and stored calibration -> projected into the galaxy.
Every line reports how it matched.

## 9. Where Grok (xAI) fits: the interface, never the judge
- **Ask TasteSpace** (`grok/agent.py`): Grok picks engine tools (search / twins / shift / explain) and phrases the
  answer. Numbers not returned by a tool are rejected (`grok/grounding.py`), and UI actions come from the tool trace.
- **Ingredient mapper** (`grok/ingredient_mapper.py`): structured output restricted to the ontology's ids.
- **Prior drafting** (`tools/data/grok_draft_ingredients.py`): drafts for human review only.

Remove Grok entirely and the ontology, aggregation, similarity, twins, shift, explain and galaxy all keep working.

## 10. Honest limits
- Values are approximations from nutrients, literature and reviewed estimates. Perception interactions like
  masking are not modeled.
- One canonical recipe stands in for a whole family of versions of a dish.
- The build report shows sanity-pair results and the human-rating correlation. We report them; we don't tune data to them.
