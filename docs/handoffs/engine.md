# Handoffs: ENGINE (P2). Only P2 edits this file. Newest entry first.

## Endpoint readiness (fixture = canned, baseline = real engine / simple, real = tuned)
| endpoint | status | notes |
|---|---|---|
| GET /api/health | baseline | build/data/grok flags |
| GET /api/space | baseline | PCA-3D; sparse-dim calibration fixed |
| GET /api/twins | baseline | adaptive ladder; clear note for single-dish courses |
| POST /api/shift | baseline | direction ladder; 0.3 ms/call at 300 dishes |
| GET /api/explain | baseline | exact attributions |
| POST /api/recipe | baseline | regex + fuzzy; Grok mapper when configured |
| POST /api/ask | baseline | Grok tool-calling; 503 grok_unavailable without key |

## Log
## H0+ · engine hardening pass 1 · READY
- what: calibration now uses only dishes that HAVE each dim (sparse dims like smoky were pinning every
  smoky dish near 1; smoky spread on seed data 0.15 -> 0.32). Empty-course twins note. New tests.
- for: data, web
- action: none needed; dish vectors shift slightly on the next `make build`. Perf: shift 0.3 ms,
  twins 0.6 ms at 300 dishes (budget 50 ms). Weight tuning waits for real data after h8.

## H0 · scaffold · READY
- what: all 7 endpoints live on seed data; 41 tests (Grok faked)
- for: web
- action: build against mock fixtures until h8; then `make dev` for real mode
