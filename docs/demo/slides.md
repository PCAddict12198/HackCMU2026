# TasteSpace slides (H17). OWNER: data (P1). Speak from `docs/demo/demo_script.md`; this is the deck outline.

Times assume a ~3 min live demo plus ~2 min on method/limits. Numbers are from core build `3eaa61b000dc` (frozen H16 calibration) unless a later `make build` is quoted on the validation slide.

## 1. Hook
- Line: "Food apps organize the world by cuisine. Cuisines don't own flavor."
- Show: rotating galaxy, stars colored by cuisine.

## 2. Twin
- Click **pho bo** → Flavor Twin **pozole rojo**.
- Speak the engine number: **98.1th percentile**, top 10% band, cuisine distance 1.0.
- Shared dims from the tool: brothy, umami, rich, spicy, chewy.
- Point: Vietnam and Mexico, same neighborhood of sensory space. Second twin is still french onion soup at 97.7.

## 3. Shift
- Preset **L** (rich −0.8σ, sour +1.2σ) from pho bo.
- First hit **tom yum goong** (87.7th, every requested dim moves the right way), then **kimchi jjigae** (87.7th).
- Line: "What I love about pho, lighter and more acidic."

## 4. Why / provenance
- Explain pho vs pozole, similarity 98.1.
- Chips: beef bone broth (`team`), pork bone broth (`team`), lime (`literature`), chili flakes (`scoville`), soup format.
- Line: "Every number traces back to ingredients, preparation and a source."

## 5. Ask
- "like pho bo but spicier" → Grok calls shift; first hit **mapo tofu** (99.2th, spicy +0.36).
- Line: "Grok is the interface; the engine is the judge."

## 6. Validation (honest)
- Frozen sanity (not tuned): **4/10** positive ≥ 90th pct, **9/10** negative < 50th pct.
- Rating panel: **AI baseline, not a human study.** If `make build` still says Spearman rho ≈ 0.90 with rater key `claude`, say so on the slide. It is an upper bound (same agent also wrote a lot of the corpus). Do not call it human validation.
- Limits: one canonical recipe per dish; no perceptual masking; sparse dims (e.g. smoky on espresso) move dessert twins.

## 7. What we built
- ~70 core dishes × 10 cuisines, ~155 ingredients, every nonzero value sourced.
- Optional extended drafts (13 dishes, including bun thit nuong) live in `data/dishes/extended/` and do not move calibration.
