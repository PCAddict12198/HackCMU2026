import { type ComponentType, useEffect, useMemo, useState } from "react";
import { API_MODE } from "./api/client";
import type { Panel } from "./contract";
import { AskPanel } from "./features/ask/AskPanel";
import { Discover } from "./features/discover/Discover";
import { DishVisual } from "./features/dish/DishVisual";
import { matchDishes, topLabels } from "./features/dish/sensory";
import { ExplainPanel } from "./features/explain/ExplainPanel";
import { CuisineLegend, Galaxy, MapFilters } from "./features/galaxy/Galaxy";
import { RecipePanel } from "./features/recipe/RecipePanel";
import { DEMO_SOURCE_ID, explainPairForDemo, partnerId } from "./features/shared/demo";
import { ErrorState } from "./features/shared/Status";
import { ShiftEngine } from "./features/shift/ShiftEngine";
import { ShiftPanel } from "./features/shift/ShiftPanel";
import { TwinsPanel } from "./features/twins/TwinsPanel";
import { BrandMark } from "./ui/BrandMark";
import { useDish, useStore } from "./state/store";

type Route = "discover" | "map" | "recipe";

const PANELS: Record<Exclude<Panel, "ask">, { label: string; View: ComponentType }> = {
  twins: { label: "Flavor Twins", View: TwinsPanel },
  shift: { label: "Taste Shift", View: ShiftPanel },
  explain: { label: "Why this match?", View: ExplainPanel },
  recipe: { label: "Map my recipe", View: RecipePanel },
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
  const { load, loadError, space, health, panel, setPanel, selectedId, resetView, highlightIds, bumpPlaceRecipe, setExplainPair, twinHighlight, select } =
    useStore();
  const selected = useDish(selectedId);
  const [query, setQuery] = useState(search);
  const [route, setRoute] = useState<Route>("discover");
  const [askOpen, setAskOpen] = useState(false);
  const [askSeed, setAskSeed] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [debugOpen, setDebugOpen] = useState(false);
  const [cuisineFilter, setCuisineFilter] = useState<string | null>(null);
  const [findQ, setFindQ] = useState("");
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
    const show = () => setRoute("map");
    window.addEventListener("tastespace:show-map", show);
    return () => window.removeEventListener("tastespace:show-map", show);
  }, []);

  useEffect(() => {
    if (panel === "ask" && health && !health.grok_configured) setPanel("twins");
  }, [health, panel, setPanel]);

  const goMap = (p?: Panel) => {
    if (p === "recipe") {
      setPanel("recipe");
      setRoute("recipe");
      setAskOpen(false);
      return;
    }
    if (p === "ask") {
      setAskOpen(true);
      setRoute("map");
      return;
    }
    if (p) setPanel(p);
    setRoute("map");
  };

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
        setRoute("map");
        setAskOpen(false);
        return;
      }
      if (e.key === "1") {
        const ids = new Set(s.space?.dishes.map((d) => d.id) ?? []);
        if (ids.has(DEMO_SOURCE_ID)) s.select(DEMO_SOURCE_ID);
        s.setPanel("twins");
        setRoute("map");
      }
      if (e.key === "2") {
        s.setPanel("twins");
        setRoute("map");
        const id = partnerId(s.selectedId, s.twinHighlight, s.highlightIds);
        if (id) s.focusDish(id);
      }
      if (e.key === "3" || e.key === "l" || e.key === "L") {
        s.setPanel("shift");
        setRoute("map");
        s.setShiftDeltas({ rich: -0.8, sour: 1.2 });
      }
      if (e.key === "4") {
        const ids = new Set(s.space?.dishes.map((d) => d.id) ?? []);
        const pair = explainPairForDemo(ids, s.selectedId, s.twinHighlight, s.highlightIds);
        if (pair) s.setExplainPair(pair[0], pair[1]);
        else s.setPanel("explain");
        setRoute("map");
      }
      if (e.key === "5") {
        s.bumpPlaceRecipe();
        setRoute("recipe");
      }
      if (e.key === "6" && s.health?.grok_configured) {
        setAskOpen(true);
        setRoute("map");
      }
      if (e.key === "s" || e.key === "S") {
        s.setPanel("shift");
        setRoute("map");
        s.setShiftDeltas({ spicy: 1.4 });
      }
      if (e.key === "m" || e.key === "M") {
        s.setPanel("shift");
        setRoute("map");
        s.setShiftDeltas({ smoky: 1.2, roasted: 0.6 });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const workingPanel: Exclude<Panel, "ask"> = panel === "ask" || panel === "recipe" ? "twins" : panel;
  const { View } = PANELS[workingPanel];
  const hits = useMemo(
    () => (space && searchQ.trim() ? matchDishes(searchQ, space.dishes, 6) : []),
    [space, searchQ],
  );

  const openAsk = (seed?: string) => {
    if (seed) setAskSeed(seed);
    setAskOpen(true);
    setRoute("map");
  };

  return (
    <div className="app">
      <header className="topbar">
        <button type="button" className="brand-mark" onClick={() => setRoute("discover")}>
          <BrandMark />
        </button>
        <nav className="nav-main">
          <button type="button" className={route === "discover" ? "active" : ""} onClick={() => setRoute("discover")}>
            Discover
          </button>
          <button type="button" className={route === "map" ? "active" : ""} onClick={() => goMap(workingPanel)}>
            Taste Map
          </button>
          <button
            type="button"
            className={route === "recipe" ? "active" : ""}
            onClick={() => {
              setPanel("recipe");
              setRoute("recipe");
            }}
          >
            My Recipe
          </button>
        </nav>
        <div className="nav-right">
          <div className="search-wrap">
            <button type="button" className="nav-link" onClick={() => setSearchOpen((v) => !v)}>
              Search
            </button>
            {searchOpen && (
              <div className="search-pop">
                <input
                  autoFocus
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  placeholder="Find a dish"
                />
                {hits.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    className="search-hit"
                    onClick={() => {
                      select(d.id);
                      setPanel("twins");
                      setRoute("map");
                      setSearchOpen(false);
                    }}
                  >
                    <DishVisual dish={d} className="mini" />
                    <span>
                      <strong>{d.name}</strong>
                      <span className="muted small"> · {d.cuisine}</span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {health?.grok_configured && (
            <button type="button" className={`nav-link ${askOpen ? "active" : ""}`} onClick={() => openAsk()}>
              Ask TasteSpace
            </button>
          )}
          <div className="debug-menu">
            <button type="button" className="ghost" onClick={() => setDebugOpen((v) => !v)} aria-label="Demo tools">
              ···
            </button>
            {debugOpen && (
              <div className="debug-pop">
                <span className={`badge ${API_MODE}`}>{API_MODE === "mock" ? "Mock" : "Live"}</span>
                {space && <span className="muted small">{space.dishes.length} dishes</span>}
                {forced && (
                  <a className="badge mock" href="/">
                    clear debug error
                  </a>
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
              </div>
            )}
          </div>
        </div>
      </header>
      {loadError != null && (
        <div className="banner">
          <ErrorState error={loadError} onRetry={() => void load()} />
        </div>
      )}
      {route === "discover" && (
        <Discover onExplore={() => setRoute("map")} onAsk={(text) => openAsk(text)} />
      )}
      <div className="page" hidden={route !== "recipe"}>
        <RecipePanel />
      </div>
      {route === "map" && (
        <main className="workspace">
          <ShiftEngine />
          <section className="galaxy">
            <Galaxy cuisineFilter={cuisineFilter} />
            <MapFilters
              query={findQ}
              onQuery={setFindQ}
              onPick={(id) => {
                select(id);
                setFindQ("");
              }}
            />
            <CuisineLegend active={cuisineFilter} onToggle={setCuisineFilter} />
            {selected && (
              <div className="selected-sheet">
                <DishVisual dish={selected} />
                <div className="pad">
                  <h3>{selected.name}</h3>
                  <p className="cuisine-line">{selected.cuisine}</p>
                  <p className="taste-line">{topLabels(selected.vector, space?.dims, 3).join(" · ")}</p>
                  <p className="blurb">{selected.blurb}</p>
                  <div className="actions">
                    <button type="button" className="primary" onClick={() => setPanel("twins")}>
                      Find a Flavor Twin
                    </button>
                    <button type="button" onClick={() => setPanel("shift")}>
                      Make it more my taste
                    </button>
                  </div>
                </div>
              </div>
            )}
          </section>
          <aside className="panel">
            <nav className="panel-nav">
              {(Object.keys(PANELS) as Exclude<Panel, "ask">[])
                .filter((p) => p !== "recipe")
                .map((p) => (
                  <button
                    key={p}
                    type="button"
                    className={p === workingPanel ? "active" : ""}
                    onClick={() => {
                      if (p === "explain") {
                        const ids = new Set(useStore.getState().space?.dishes.map((d) => d.id) ?? []);
                        const pair = explainPairForDemo(ids, selectedId, twinHighlight, highlightIds);
                        if (pair) setExplainPair(pair[0], pair[1]);
                        else setPanel(p);
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
      )}
      {askOpen && health?.grok_configured && (
        <>
          <button type="button" className="ask-backdrop" aria-label="Close Ask" onClick={() => setAskOpen(false)} />
          <div className="ask-drawer">
            <div className="row" style={{ marginBottom: 8 }}>
              <span />
              <button type="button" className="ghost" onClick={() => setAskOpen(false)}>
                Close
              </button>
            </div>
            <AskPanel
              seed={askSeed}
              onConsumedSeed={() => setAskSeed(null)}
              onUsedEngine={() => setRoute("map")}
            />
          </div>
        </>
      )}
    </div>
  );
}
