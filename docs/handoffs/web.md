# Handoffs: WEB (P3). Only P3 edits this file. Newest entry first.

## Panel readiness (placeholder = wired to contract, baseline = usable, demo = polished)
| feature | status | notes |
|---|---|---|
| galaxy | demo | 80-star mockLarge, dpr cap, no trail hitch, fly-to |
| twins | demo | stale-while-revalidate + skeleton; 4 seeds explain pair |
| shift | demo | sliders stay up during latency/errors; L/S/M |
| explain | demo | key 4 / tab seeds pair so no empty state |
| recipe | demo | key 5 auto-places sample; line statuses |
| ask | demo | hidden if grok off; skeleton while asking |

## Log
## 10:50 · READY
- what: pre-h8 polish — panel errors/latency, mockLarge orbit, demo keys 0–5
- for: integrator
- action: still fixtures-only until "main @ h8 ready"

## 10:29 · READY
- what: mockError no longer kills the galaxy; space always serves the 16-dish fixture catalog
- for: web
- action: open http://localhost:5173/ with no query string; ?mockError= is panel-only debug

## 10:20 · c5c7026 · READY
- what: mock-mode UI through H8 TODOs (galaxy + all panels + demo keys 0/1–6/L/S/M)
- for: integrator
- action: merge at h8; web still uses fixtures until `make dev`

## H0 · scaffold · READY
- what: mock + real API clients, store, uiActions reducer, six panel placeholders
- for: web
- action: see web/src/features/*/README.md
