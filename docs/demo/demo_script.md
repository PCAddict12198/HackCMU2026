# Demo script (2-3 min). OWNER: data (P1). Numbers copied from a real core build (`0c4812829798`, 70 dishes). Not hand-picked against sanity.

| time | action | say |
|---|---|---|
| 0:00-0:15 | rotating galaxy | "Food apps organize the world by cuisine. Cuisines don't own flavor." |
| 0:15-0:30 | click **pho bo** -> Flavor Twin -> **french onion soup** (97.6th percentile; top 10% band; cuisine distance 1.0) | "Vietnam and France, same neighborhood of the space: both are beef-broth bowls — brothy, umami, earthy, roasted, rich." |
| 0:30-0:50 | Shift preset **L** (rich −0.8σ, sour +1.2σ) from pho bo; first hit **pozole rojo** (97.8th, every requested dim moves the right way). Second: **tom yum goong** (88.0th, sour +0.40, rich −0.53). | "What I love about pho, lighter and more acidic. The engine lands on pozole, then tom yum — still brothy, more sour, less fat." |
| 0:50-1:10 | "Why?" on pho bo vs french onion soup | "Similarity 97.6. Shared body is beef bone broth (`src: team`) plus the soup format. Pho's lime is literature sour; onion soup's extra richness is USDA fat on gruyere and butter. Every chip is an ingredient, a process, or a format — not a vibe." |
| 1:10-1:30 | Ask: "like pho bo but spicier" -> galaxy; engine shift spicy +1.4σ first hit **mapo tofu** (99.0th, spicy +0.36) | "Grok is the interface; the engine is the judge. It can only quote engine numbers." |
| 1:30-1:50 | validation slide | "Frozen sanity set: 4/10 positive pairs above the 90th percentile, 9/10 negative pairs below the 50th. We do not tune ingredients to move those scores. Pair-rating Spearman rho 0.89 over 20 pairs — but say what it is: one AI rater, not a human panel, and the same agent wrote much of the data, so it is an upper bound, not independent validation." |

Demo pairs (copied from `find_twins` / `shift` / `explain` on this build):
- twin: pho_bo -> french_onion_soup, similarity_pct **97.6**, relaxation_level **0** ("twins are in the top 10% of similar dish pairs"), cuisine_distance **1.0**, shared_dims brothy / umami / earthy / roasted / rich. Next twins: pozole_rojo 97.2, osso_buco 97.1.
- shift: pho_bo + `{rich: -0.8, sour: 1.2}` (UI preset L) -> pozole_rojo **97.8** (sour +0.079, rich −0.286), then tom_yum_goong **88.0**.
- ask/spicier: pho_bo + `{spicy: 1.4}` (UI preset S) -> mapo_tofu **99.0**.
