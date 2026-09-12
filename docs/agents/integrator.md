# INTEGRATOR (P2, separate session on `main` in `~/HackCMU2026`)

Only this session merges into `main`, changes contracts and root files, and tags checkpoints.

## H0 (before anyone launches an agent)
1. Team review (~45 min, humans): edit `data/dishes/core/_manifest.yaml` (70 core dishes) and
   `data/sanity/sanity_pairs.yaml` (10 positive + 10 negative, **before** looking at results). Read `docs/CONTRACTS.md`.
2. Commit, then run `make contracts && make fixtures && make build && make check`.
3. `git tag h0-freeze && git tag sanity-lock` (the lock makes the sanity set immutable).
4. **Topology A** (one Mac): `bash tools/integrate/make_worktrees.sh`.
   **Topology B** (three laptops): create the GitHub repo, then `bash tools/integrate/publish_branches.sh`,
   add collaborators, and each teammate clones + `tools/integrate/setup_worktree.sh . <role>`.
5. Each person opens their folder in their agent and pastes the kickoff prompt from `docs/agents/<role>.md`.

## Checkpoints (H8, H16, H20, final): `docs/INTEGRATION.md`
`bash tools/integrate/checkpoint.sh h8`, smoke checklist, `git tag h8 && git push origin main --tags`, then announce.

## Contract change protocol (details in docs/CONTRACTS.md)
- **Additive** (new optional field, new endpoint, new enum value): hotfix on `main` any time: edit
  `contracts/src/...` -> `make contracts` -> bump `contracts/VERSION` + `CONTRACT_VERSION` -> update fixtures if
  needed (`make fixtures`) -> `make check` -> commit `[contract] v1.x` -> tag `contract-v1.x` -> push -> announce.
- **Breaking** (rename/remove/change type): only at a checkpoint, major bump, all three roles agree.

## Dependency requests
Python: `uv add <pkg> --package tastespace` on `main` -> `make check` -> commit `[deps] ...` -> announce (everyone runs
`make setup` after merging main). JS dependencies belong to web (P3); don't touch them.

## Unlocking the sanity set (should never be needed)
Team agreement -> `ALLOW_LOCKED=1 git commit ...` -> `git tag -f sanity-lock` -> note it in the report/slides.
