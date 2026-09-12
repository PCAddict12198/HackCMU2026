# Demo script (2-3 min). OWNER: data (P1). Numbers copied from a real core build (`3eaa61b000dc`, 70 dishes, frozen H16 calibration). Not hand-picked against sanity.

| time | action | say |
|---|---|---|
| 0:00-0:15 | rotating galaxy | "Food apps organize the world by cuisine. Cuisines don't own flavor." |
| 0:15-0:30 | click **pho bo** -> Flavor Twin -> **pozole rojo** (98.1th percentile; top 10% band; cuisine distance 1.0) | "Vietnam and Mexico, same neighborhood: both are meat-and-chili broth bowls — brothy, umami, rich, spicy, chewy." |
| 0:30-0:50 | Shift preset **L** (rich −0.8σ, sour +1.2σ) from pho bo; first hit **tom yum goong** (87.7th, sour +0.405, rich −0.529; every requested dim moves the right way). Tied second: **kimchi jjigae** (87.7th). | "What I love about pho, lighter and more acidic. The engine leaves the pork-chili stew behind and lands on tom yum." |
| 0:50-1:10 | "Why?" on pho bo vs pozole rojo | "Similarity 98.1. Shared body is broth plus soup format. Pho's beef bone broth is `src: team`; pozole's pork bone broth is the same source class. Lime on both is literature sour; pozole's chili flakes add the spice pho only hints at. Every chip is an ingredient, a process, or a format — not a vibe." |
| 1:10-1:30 | Ask: "like pho bo but spicier" -> galaxy; engine shift spicy +1.4σ first hit **mapo tofu** (99.2th, spicy +0.36) | "Grok is the interface; the engine is the judge. It can only quote engine numbers." |
| 1:30-1:50 | validation slide | "Frozen sanity set: 4/10 positive pairs above the 90th percentile, 9/10 negative pairs below the 50th. We do not tune ingredients to move those scores. Pair-rating Spearman rho 0.90 over 20 pairs — but say what it is: one AI rater, not a human panel, and the same agent wrote much of the data, so it is an upper bound, not independent validation." |

Demo pairs (copied from `find_twins` / `shift` / `explain` on this build, with `load_frozen_calibration()`):
- twin: pho_bo -> pozole_rojo, similarity_pct **98.1**, relaxation_level **0** ("twins are in the top 10% of similar dish pairs"), cuisine_distance **1.0**, shared_dims brothy / umami / rich / spicy / chewy. Next twins: french_onion_soup **97.7**, osso_buco **97.2**.
- shift: pho_bo + `{rich: -0.8, sour: 1.2}` (UI preset L) -> tom_yum_goong **87.7**, then kimchi_jjigae **87.7**, then hot_and_sour_soup **86.7**.
- ask/spicier: pho_bo + `{spicy: 1.4}` (UI preset S) -> mapo_tofu **99.2**.
