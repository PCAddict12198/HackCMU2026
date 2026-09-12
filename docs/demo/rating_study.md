# Pair-rating study (H15). OWNER: data (P1)

What actually shipped for the hackathon:

1. P1 picked 20 core pairs **before** looking at model scores (mix of likely-similar, likely-different, and uncertain). None of them is a frozen sanity pair.
2. A real human panel was not run. The file `data/validation/ratings.yaml` has one rater key, `claude` (AI). Treat Spearman rho as an **AI baseline / upper bound**, not human validation.
3. `make build` -> `build/report.md` -> "Rater panel vs model" tags that key as AI. Engine will not use AI keys to retune weights.
4. To run this properly later: each person rates 1-5 alone, without the app, and adds a human key (`p1`, `ishan`, …) on every pair.

Do not invent human scores. Do not revise ratings after looking at engine percentiles in order to raise rho.
