# ask (P3)
Baseline: chat -> `api.ask` -> reply + `applyUiActions(res.ui_actions)`; tab hidden when `health.grok_configured` is false.

TODO
- [x] show the tool trace ("Grok called find_twins(tonkotsu_ramen)")
- [x] grounded badge; when `grounded=false`, say "summary generated from engine results"
- [x] suggestion chips ("flavor twin of ...", "like ... but lighter")
- [x] handle grok_failed / network gracefully (retry button)
