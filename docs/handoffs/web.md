# Handoffs: WEB (P3). Only P3 edits this file. Newest entry first.

## Panel readiness (placeholder = wired to contract, baseline = usable, demo = polished)
| feature | status | notes |
|---|---|---|
| galaxy | demo | Taste Map on warm ivory; cuisine dropdown; fly-to; shift trail |
| twins | demo | food cards + dim dots; “Why this match?” |
| shift | demo | craving sliders + path from engine results; L/S/M |
| explain | demo | consumer story first; calc details behind details |
| recipe | demo | Map my recipe page; coverage copy; show on map |
| ask | demo | drawer (not a chatbot home); tool trace behind a link |

## 13:56 · READY
- what: merged `origin/main` into `agent/web`. Kept Discover / Taste Map shell; dish photos from main now sit on food cards and the selected sheet (abstract plate is the 404 fallback).
- for: integrator
- action: `make web` or `make dev`; click a star — photo + credit on the selected sheet.

## 13:40 · READY
- what: Taste Map stays wide with bright nodes + neighbor links; scroll to zoom out; nearby dishes now select that dish. Mock recipe uses the pasted text (no more frozen carbonara fixture).
- for: integrator
- action: `make web` and try Map my recipe with two different pastes; Taste Map “See all” then click another node.

## 13:24 · READY
- what: consumer redesign — Discover home, ivory Taste Map, Fraunces + DM Sans, lime CTAs. Same APIs and demo keys (0 / 1 / L / 4 / 5 / 6).
- for: integrator
- action: `make web` (mock) or `make dev` (live 70 dishes). First screen is Discover, not the 3D view.

## 13:15 · READY
- what: 70 freely licensed dish photos on the selected-dish card (`/dishes/<id>.jpg`). Mapping lives in web, not the frozen dish schema. Shared warm crop/grade in CSS so Commons photos read as one set.
- for: integrator
- action: `make web` or `make dev`; click a star — photo + credit appear with name/cuisine/blurb.

## 12:46 · READY
- what: visual polish — smooth lit dish orbs, Fraunces + Outfit, glass panel chrome
- for: integrator
- action: `make dev` for live 70-dish data (not `make web`)

## 12:30 · READY
- what: demo keys follow `docs/demo/demo_script.md` — default/1 = pho_bo twins, 3/L = lighter shift, 4 = pho vs pozole (when both in the catalog), Ask placeholder "like pho bo but spicier". Mock 16-dish has pho but not pozole; key 4 falls back to the loaded twin.
- for: integrator
- action: `make dev`; 0/1/L/4/6 walkthrough. Real build `3eaa61b000dc`: twin pozole 98.1, L tom yum 87.7, S mapo 99.2.

## 12:08 · f0e7239 · READY
- what: instanced stars use instanceColor only (dropped `vertexColors`); real-mode 70-dish galaxy matches cuisine legend
- for: engine | integrator
- action: none; verified `make dev` LIVE ENGINE + mock 16/80

## 11:46 · READY
- what: 80-dish mock actually loads (header toggle, ignore stale fetches, camera stays wide)
- for: web
- action: click "Load 80-dish mock" on http://localhost:5173/ (or ?mockLarge=1 with a full reload)

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
