# Integration runbook. OWNER: integrator

## Topologies
- **A: all three agents on one Mac.** `tools/integrate/make_worktrees.sh` creates `../HackCMU2026-p1-data`,
  `-p2-engine`, `-p3-web` (branches `agent/data|engine|web`, ports 8001/5174, 8002/5175, 8003/5176). A GitHub
  remote is optional (backup); refresh with `git merge --no-edit main`.
- **B: each teammate on their own laptop.** A shared private GitHub repo is required.
  `tools/integrate/publish_branches.sh` pushes `main`, the tags and the three agent branches; each teammate
  clones, runs `git switch agent/<role>`, then `tools/integrate/setup_worktree.sh . <role>`. Refresh with `git merge --no-edit origin/main`.

The main checkout `~/HackCMU2026` stays on `main` and belongs to the integrator session.

## Checkpoints: H8 (60 min) · H16 (60 min, then FEATURE FREEZE) · H20 (30 min, bugfixes) · H22 final
1. **T-15 min:** every agent commits and pushes; each writes a `READY` or `BLOCKED` handoff entry with its commit hash.
   Humans pause their agents.
2. **Integrator:** `bash tools/integrate/checkpoint.sh h8`. It merges engine -> data (+ `make build`) -> web,
   running `make check` after each merge. A branch that conflicts or fails is backed out and reported.
3. **Real-mode smoke checklist** (`make dev`):
   - [ ] galaxy loads the real space
   - [ ] click a dish -> twins appear
   - [ ] drag a slider -> target glides, results change
   - [ ] "Why?" -> explain shows attributions with provenance chips
   - [ ] recipe returns coverage
   - [ ] Ask works with a key (or the tab is hidden without one)
   - [ ] `build/report.md`: attribution OK, sanity numbers noted (not tuned)
4. **Pass:** `git tag h8 && git push origin main --tags`, then post "main @ h8 ready".
   **Fail:** each failing owner gets a 30-min fix window on their own branch, then re-run.
5. **Everyone refreshes:** `git fetch origin && git merge --no-edit origin/main && make setup && make check-<role>`.

## Rules
- The integrator fixes only integrator-owned files on `main`. Code bugs go back to the owner via a handoff REQUEST.
- Merge conflicts should be impossible (exclusive ownership). A conflict means someone crossed a boundary:
  find it with `python3 tools/ci/check_ownership.py` on that branch.
- **H16 freeze:** pick demo pairs from actual engine output (`docs/demo/demo_script.md`), freeze calibration
  (`python -m tastespace.build --freeze-calibration` on agent/engine), and after that ship bugfixes only.
- **After `final`:** only the integrator commits, and only for demo-blocking issues.
