# TasteSpace: search by flavor, not by name

TasteSpace is a computational map of food. Every dish sits at a position computed from its ingredients'
sensory profiles, how they're prepared, and the dish's format, across 17 interpretable dimensions (taste,
aroma, mouthfeel). With that map you can:
- find **Flavor Twins**: dishes with a similar sensory profile from a different cuisine;
- **shift** a dish toward "lighter", "more acidic" and so on, and see what lives there;
- **explain** every match down to the ingredients and data sources behind it.

> Built for HackCMU 2026 by a team of three, each working in parallel with an AI coding agent.

## How we use Grok (xAI): the interface, never the judge
| where | what Grok does | guardrail |
|---|---|---|
| [`backend/tastespace/grok/agent.py`](backend/tastespace/grok/agent.py) | **Ask TasteSpace**: Grok tool-calls our engine (`search_dishes`, `find_twins`, `shift_taste`, `explain_pair`) and phrases the answer; its tool calls drive the 3D galaxy | [`grounding.py`](backend/tastespace/grok/grounding.py) rejects any number a tool didn't return; UI actions come from the tool trace |
| [`backend/tastespace/grok/ingredient_mapper.py`](backend/tastespace/grok/ingredient_mapper.py) | maps unrecognized recipe ingredients onto our ontology | structured output restricted to an **enum of our ingredient ids** |
| [`tools/data/grok_draft_ingredients.py`](tools/data/grok_draft_ingredients.py) | drafts sensory priors for new ingredients | drafts go to `data/drafts/`; canonical data only after human review (`grok_reviewed`) |

The flavor space itself (aggregation, similarity, twins, shift, explanations) is computed by our engine
([`docs/MODEL.md`](docs/MODEL.md)). Remove Grok and everything except Ask keeps working.

## Photo credits
Dish photos in `web/public/dishes/` are freely licensed (CC0, public domain, CC BY, CC BY-SA) from Wikimedia
Commons, Flickr and Openverse. They are not our photography. Each photo's author, license and source page are
listed in [`web/public/dishes/sources.json`](web/public/dishes/sources.json) and credited on the card in the app.

## Quick start
Prerequisites: macOS or Linux (use WSL on Windows), `brew install uv node`, and Node ≥ 20.

```bash
make setup     # Python 3.12 env via uv + web deps + git hooks
make build     # data/ -> build/tastespace.json + build/report.md
make dev       # API (FastAPI) + web (Vite) in real mode
```
Or `make web` alone for mock mode (no backend needed). Copy `.env.example` to `.env` for Grok/USDA keys.

## Team workflow (3 people x 3 agents in parallel)
- **Rules for agents:** [`AGENTS.md`](AGENTS.md) (Claude Code reads it through `CLAUDE.md`)
- **Roles:** [`docs/agents/`](docs/agents/): `data` (P1), `engine` (P2 + integrator), `web` (P3), each with a kickoff prompt
- **Ownership:** [`OWNERS.json`](OWNERS.json), enforced by a Claude Code hook, git hooks and CI
- **Contracts:** [`docs/CONTRACTS.md`](docs/CONTRACTS.md). Pydantic -> OpenAPI -> TypeScript, plus shared fixtures
- **Checkpoints:** [`docs/INTEGRATION.md`](docs/INTEGRATION.md) · **timeline:** [`docs/TASKS.md`](docs/TASKS.md)
- **Talking between agents:** `docs/handoffs/<role>.md`, read with `make inbox`

| path | owner |
|---|---|
| `data/`, `tools/data/`, `docs/demo/` | P1 data |
| `backend/tastespace/`, `backend/tests/`, `docs/MODEL.md` | P2 engine |
| `web/` | P3 web |
| `contracts/`, root files, `tools/ci/`, `tools/integrate/`, `docs/agents/` | integrator (`main` only) |
