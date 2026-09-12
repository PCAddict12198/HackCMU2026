# Hour-by-hour plan. OWNER: integrator

H0 = the moment the three agents launch. If the scaffold has to be built during the event, everything
shifts by ~1.5 h and the H22-24 buffer absorbs it.

| Time | P1 Data (`agent/data`) | P2 Engine (`agent/engine`) | P3 Web (`agent/web`) |
|---|---|---|---|
| **H-0:45-0** (all, on `main`) | edit `_manifest.yaml` (70 dishes), write `sanity_pairs.yaml`, get USDA + xAI keys | review contracts, `make contracts && make fixtures && make check`, tag `h0-freeze` + `sanity-lock`, create worktrees/branches | confirm topology, ports, mock mode runs |
| H0-3 | dish skeletons for 35 dishes -> ingredient list | engine hardening: weights, calibration, ladders | shell, API client, galaxy (instanced stars, colors, labels, click, fly-to) |
| H3-5 | `usda_fill` + Scoville basic tastes; `grok_draft_ingredients` -> drafts | recipe parser (units, aliases, fuzzy, coverage) | Twins + Explain panels |
| H5-8 | review + promote drafts; other 35 skeletons | Grok live smoke, prompt/tool tuning, mapper | Shift (glide), Recipe + Ask UIs on mocks, uiActions |
| **H8-9** | **Integration #1**: all pause · `checkpoint.sh h8` · smoke · tag `h8` · everyone merges `main` | | |
| H9-12 | finish 70 dishes; fix `build/report.md` issues | tune on real data (no data edits) | real mode, loading/error states, Ask drives galaxy |
| H12-15 | review pass 2; extended drafts only if core done | recipe on real lexicon; Ask on real engine; shift < 50 ms | recipe star, PCA axis labels, glide polish |
| H15-16 | **all:** 15-min blind rating study; P1 enters ratings | validation metrics in report | projector-size performance check |
| **H16-17** | **Integration #2 + FEATURE FREEZE**: demo pairs from real output -> `docs/demo/demo_script.md`; freeze calibration; tag `h16` | | |
| H17-20 | slides, validation report | bugfixes; Grok code map for README (REQUEST to integrator) | demo mode (keyboard steps, reset view) |
| **H20-20:30** | **Integration #3** (bugfixes only), tag `h20` | | |
| H20:30-22 | rehearse x3 with Wi-Fi OFF for the core path; record a backup video of the Ask/Grok flows + the full demo | | |
| **H22** | **`final` tag**; integrator-only emergency fixes | | |
| H22-24 | buffer, submission | | |
