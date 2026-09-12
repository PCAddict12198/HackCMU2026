import { type ComponentType, useEffect, useState } from "react";
import { API_MODE } from "./api/client";
import type { Panel } from "./contract";
import { AskPanel } from "./features/ask/AskPanel";
import { ExplainPanel } from "./features/explain/ExplainPanel";
import { CuisineLegend, Galaxy } from "./features/galaxy/Galaxy";
import { RecipePanel } from "./features/recipe/RecipePanel";
import { DEMO_SOURCE_ID, explainPairForDemo, partnerId } from "./features/shared/demo";
import { ErrorState } from "./features/shared/Status";
import { ShiftPanel } from "./features/shift/ShiftPanel";
import { TwinsPanel } from "./features/twins/TwinsPanel";
import { useDish, useStore } from "./state/store";

const PANELS: Record<Panel, { label: string; View: ComponentType }> = {
  twins: { label: "Flavor Twins", View: TwinsPanel },
  shift: { label: "Taste Shift", View: ShiftPanel },
  explain: { label: "Explain", View: ExplainPanel },
  recipe: { label: "My Recipe", View: RecipePanel },
  ask: { label: "Ask (Grok)", View: AskPanel },
};

const search = () => (typeof location === "undefined" ? "" : location.search);

const debugError = (q: string) => new URLSearchParams(q).get("mockError");

function setMockQuery(mutate: (params: URLSearchParams) => void) {
  const u = new URL(window.location.href);
  mutate(u.searchParams);
  history.pushState({}, "", u);
  window.dispatchEvent(new Event("tastespace:query"));
}

export default function App() {
  const { load, loadError, space, health, panel, setPanel, selectedId, resetView, highlightIds, bumpPlaceRecipe, setExplainPair, twinHighlight } =
    useStore();
  const selected = useDish(selectedId);
  const [query, setQuery] = useState(search);
  const forced = debugError(query);
  const mockLarge = new URLSearchParams(query).get("mockLarge") === "1";
  useEffect(() => {
    const sync = () => setQuery(search());
    window.addEventListener("popstate", sync);
    window.addEventListener("tastespace:query", sync);
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener("tastespace:query", sync);
    };
  }, []);
  useEffect(() => {
    void load();
  }, [load, query]);

  useEffect(() => {
    if (panel === "ask" && health && !health.grok_configured) setPanel("twins");
  }, [health, panel, setPanel]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT")) return;
      const s = useStore.getState();
      if (e.key === "Escape" || e.key === "0" || e.key === "r" || e.key === "R") {
        e.preventDefault();
        const ids = new Set(s.space?.dishes.map((d) => d.id) ?? []);
        if (ids.has(DEMO_SOURCE_ID)) s.select(DEMO_SOURCE_ID);
        s.resetView();
        s.setPanel("twins");
        return;
      }
      if (e.key === "1") {
        const ids = new Set(s.space?.dishes.map((d) => d.id) ?? []);
        if (ids.has(DEMO_SOURCE_ID)) s.select(DEMO_SOURCE_ID);
        s.setPanel("twins");
      }
      if (e.key === "2") {
        s.setPanel("twins");
        const id = partnerId(s.selectedId, s.twinHighlight, s.highlightIds);
        if (id) s.focusDish(id);
      }
      if (e.key === "3" || e.key === "l" || e.key === "L") {
        s.setPanel("shift");
        s.setShiftDeltas({ rich: -0.8, sour: 1.2 });
      }
      if (e.key === "4") {
        const ids = new Set(s.space?.dishes.map((d) => d.id) ?? []);
        const pair = explainPairForDemo(ids, s.selectedId, s.twinHighlight, s.highlightIds);
        if (pair) s.setExplainPair(pair[0], pair[1]);
        else s.setPanel("explain");
      }
      if (e.key === "5") s.bumpPlaceRecipe();
      if (e.key === "6" && s.health?.grok_configured) s.setPanel("ask");
      if (e.key === "s" || e.key === "S") {
        s.setPanel("shift");
        s.setShiftDeltas({ spicy: 1.4 });
      }
      if (e.key === "m" || e.key === "M") {
        s.setPanel("shift");
        s.setShiftDeltas({ smoky: 1.2, roasted: 0.6 });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const tabs = (Object.keys(PANELS) as Panel[]).filter((p) => p !== "ask" || health?.grok_configured);
  const active = tabs.includes(panel) ? panel : "twins";
  const { View } = PANELS[active];
  return (
    <div className="app">
      <header>
        <strong>TasteSpace</strong>
        <span className="muted small">search by flavor, not by name</span>
        <span className={`badge ${API_MODE}`}>{API_MODE === "mock" ? "MOCK DATA" : "LIVE ENGINE"}</span>
        {forced && (
          <a className="badge mock" href="/">
            debug ?mockError={forced} — clear
          </a>
        )}
        {health && !health.grok_configured && <span className="badge mock">Ask hidden</span>}
        {space && (
          <span className="muted small">
            build {space.meta.build_id} · {space.dishes.length} dishes
          </span>
        )}
        {API_MODE === "mock" && (
          <button
            type="button"
            className={mockLarge ? "active" : "ghost"}
            onClick={() =>
              setMockQuery((p) => {
                if (p.get("mockLarge") === "1") p.delete("mockLarge");
                else {
                  p.set("mockLarge", "1");
                  p.delete("mockError");
                }
              })
            }
          >
            {mockLarge ? "80-dish mock on" : "Load 80-dish mock"}
          </button>
        )}
        <button type="button" className="ghost" onClick={resetView}>
          Reset view
        </button>
        <span className="muted small hide-narrow">0 reset · 1 twins · 2 fly · 3/L shift · 4 why · 5 recipe</span>
      </header>
      {loadError != null && (
        <div className="banner">
          <ErrorState error={loadError} onRetry={() => void load()} />
        </div>
      )}
      <main>
        <section className="galaxy">
          <Galaxy />
          <CuisineLegend />
          {selected && (
            <div className="dish-card">
              <strong>{selected.name}</strong> <span className="muted">{selected.cuisine}</span>
              <div className="small">{selected.blurb}</div>
            </div>
          )}
        </section>
        <aside>
          <nav>
            {tabs.map((p) => (
              <button
                key={p}
                type="button"
                className={p === active ? "active" : ""}
                onClick={() => {
                  if (p === "explain") {
                    const ids = new Set(useStore.getState().space?.dishes.map((d) => d.id) ?? []);
                    const pair = explainPairForDemo(ids, selectedId, twinHighlight, highlightIds);
                    if (pair) setExplainPair(pair[0], pair[1]);
                    else setPanel(p);
                  } else if (p === "recipe") {
                    if (!useStore.getState().recipeStar) bumpPlaceRecipe();
                    else setPanel("recipe");
                  } else setPanel(p);
                }}
              >
                {PANELS[p].label}
              </button>
            ))}
          </nav>
          <View />
        </aside>
      </main>
    </div>
  );
}
