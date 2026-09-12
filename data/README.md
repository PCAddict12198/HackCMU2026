# data/ (OWNER: data, P1)

| path | what |
|---|---|
| `dims.yaml`, `cuisines.yaml` | frozen ids, editable labels |
| `formats.yaml`, `processes.yaml` | dish-format vectors, preparation transforms (frozen ids, editable values) |
| `ingredients/*.yaml` | the ontology: profile (0..1 per dim, with `src`), potency, unit weights |
| `dishes/core/_manifest.yaml` | the agreed ~70 core dishes |
| `dishes/core/<cuisine>.yaml` | one canonical recipe per dish (grams only) |
| `dishes/extended/` | optional extra dishes (`confidence: draft`), never required |
| `lexicon/` | recipe-parser units + aliases |
| `drafts/` | Grok/USDA drafts awaiting review (never loaded by the engine) |
| `sanity/sanity_pairs.yaml` | frozen at h0-freeze |
| `validation/ratings.yaml` | human rating study (H15) |

Validate: `make check-data`. Workflow and rules: `docs/agents/data.md`. Math: `docs/MODEL.md`.
