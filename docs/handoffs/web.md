# Handoffs: WEB (P3). Only P3 edits this file. Newest entry first.

## Panel readiness (placeholder = wired to contract, baseline = usable, demo = polished)
| feature | status | notes |
|---|---|---|
| galaxy | demo | instanced stars, fly-to, PCA axes, cuisine legend, recipe star, shift glide |
| twins | demo | radar, fly-to twin, closer-than-N% copy, Why? |
| shift | demo | 6 sliders, HOW formula, moved bits, L/S/M presets, target trail |
| explain | demo | radar, attribution bars, provenance chips |
| recipe | demo | coverage + line status colors, format/course, glowing star |
| ask | demo | tool trace, grounded badge, suggestion chips, retry; hidden if grok off |

## Log
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
