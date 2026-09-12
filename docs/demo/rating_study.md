# Mini human-rating study (H15, ~15 min). OWNER: data (P1)

1. P1 picks 20 core pairs **before** looking at their model scores: a mix of likely-similar, likely-different and surprising pairs.
2. Each teammate rates every pair 1-5 ("how similar would these taste?") alone, without looking at the app.
3. P1 enters the ratings in `data/validation/ratings.yaml`:
   `- {a: tonkotsu_ramen, b: pho_bo, ratings: {p1: 4, p2: 3, p3: 4}}`
4. `make build` -> `build/report.md` -> "Human ratings vs model" shows Spearman rho. Report it honestly on the
   validation slide, whatever it is.
