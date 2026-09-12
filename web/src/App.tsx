// Layout shell with fixed panel slots. Each feature lives in src/features/<name>/ (see its README).
import { type ComponentType, useEffect } from "react";
import { API_MODE } from "./api/client";
import type { Panel } from "./contract";
import { AskPanel } from "./features/ask/AskPanel";
import { ExplainPanel } from "./features/explain/ExplainPanel";
import { Galaxy } from "./features/galaxy/Galaxy";
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
  const { load, loadError, space, health, panel, setPanel, selectedId } = useStore();
  const selected = useDish(selectedId);
  useEffect(() => {
    void load();
  }, [load]);

  const tabs = (Object.keys(PANELS) as Panel[]).filter((p) => p !== "ask" || health?.grok_configured);
  const { View } = PANELS[panel];
  return (
    <div className="app">
      <header>
        <strong>TasteSpace</strong>
        <span className="muted small">search by flavor, not by name</span>
        <span className={`badge ${API_MODE}`}>{API_MODE === "mock" ? "MOCK DATA" : "LIVE ENGINE"}</span>
        {space && <span className="muted small">build {space.meta.build_id} - {space.meta.n_dishes} dishes</span>}
      </header>
      {loadError && <div className="error banner">{loadError}</div>}
      <main>
        <section className="galaxy">
          <Galaxy />
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
              <button key={p} className={p === panel ? "active" : ""} onClick={() => setPanel(p)}>
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
