# Handoffs: ENGINE (P2). Only P2 edits this file. Newest entry first.

## Endpoint readiness (fixture = canned, baseline = real engine / simple, real = tuned)
| endpoint | status | notes |
|---|---|---|
| GET /api/health | baseline | build/data/grok flags |
| GET /api/space | baseline | PCA-3D, seed data |
| GET /api/twins | baseline | adaptive ladder |
| POST /api/shift | baseline | direction ladder |
| GET /api/explain | baseline | exact attributions |
| POST /api/recipe | baseline | regex + fuzzy; Grok mapper when configured |
| POST /api/ask | baseline | Grok tool-calling; 503 grok_unavailable without key |

## Log
## H0 · scaffold · READY
- what: all 7 endpoints live on seed data; 41 tests (Grok faked)
- for: web
- action: build against mock fixtures until h8; then `make dev` for real mode
