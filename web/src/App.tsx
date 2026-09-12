import { type ComponentType, useEffect } from "react";
import { API_MODE } from "./api/client";
import type { Panel } from "./contract";
import { AskPanel } from "./features/ask/AskPanel";
import { ExplainPanel } from "./features/explain/ExplainPanel";
import { CuisineLegend, Galaxy } from "./features/galaxy/Galaxy";
import { RecipePanel } from "./features/recipe/RecipePanel";
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

export default function App() {
  const { load, loadError, space, health, panel, setPanel, selectedId, resetView, setShiftDeltas, highlightIds, focusDish } =
    useStore();
  const selected = useDish(selectedId);
  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (panel === "ask" && health && !health.grok_configured) setPanel("twins");
  }, [health, panel, setPanel]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT")) return;
      if (e.key === "Escape" || e.key === "0" || e.key === "r" || e.key === "R") {
        e.preventDefault();
        resetView();
        return;
      }
      if (e.key === "1") setPanel("twins");
      if (e.key === "2") {
        const id = useStore.getState().twinHighlight ?? highlightIds[0];
        if (id) focusDish(id);
      }
      if (e.key === "3") {
        setPanel("shift");
        setShiftDeltas({ rich: -0.8, sour: 1.2 });
      }
      if (e.key === "4") setPanel("explain");
      if (e.key === "5") setPanel("recipe");
      if (e.key === "6" && health?.grok_configured) setPanel("ask");
      if (e.key === "l" || e.key === "L") {
        setPanel("shift");
        setShiftDeltas({ rich: -0.8, sour: 1.2 });
      }
      if (e.key === "s" || e.key === "S") {
        setPanel("shift");
        setShiftDeltas({ spicy: 1.4 });
      }
      if (e.key === "m" || e.key === "M") {
        setPanel("shift");
        setShiftDeltas({ smoky: 1.2, roasted: 0.6 });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusDish, health?.grok_configured, highlightIds, resetView, setPanel, setShiftDeltas]);

  const tabs = (Object.keys(PANELS) as Panel[]).filter((p) => p !== "ask" || health?.grok_configured);
  const active = tabs.includes(panel) ? panel : "twins";
  const { View } = PANELS[active];
  return (
    <div className="app">
      <header>
        <strong>TasteSpace</strong>
        <span className="muted small">search by flavor, not by name</span>
        <span className={`badge ${API_MODE}`}>{API_MODE === "mock" ? "MOCK DATA" : "LIVE ENGINE"}</span>
        {space && (
          <span className="muted small">
            build {space.meta.build_id} · {space.meta.n_dishes} dishes
          </span>
        )}
        <button type="button" className="ghost" onClick={resetView}>
          Reset view
        </button>
        <span className="muted small hide-narrow">1–5 panels · L/S/M shift · 0 reset</span>
      </header>
      {loadError && (
        <div className="banner error-card">
          <strong>Could not load the flavor space</strong>
          <p className="small">{loadError}</p>
          <button type="button" onClick={() => void load()}>
            Retry
          </button>
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
              <button key={p} type="button" className={p === active ? "active" : ""} onClick={() => setPanel(p)}>
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
