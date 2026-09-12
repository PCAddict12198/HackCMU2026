import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { DishPoint, TwinResult } from "../../contract";
import { closerThan } from "../shared/copy";
import { DishVisual } from "../dish/DishVisual";
import { CRAVINGS, matchDishes, pickByDim, topLabels } from "../dish/sensory";
import { useStore } from "../../state/store";

const SEEDS = ["tonkotsu_ramen", "pho_bo", "mango_sticky_rice"];

type Pair = { source: DishPoint; twin: TwinResult; twinDish: DishPoint };

export function Discover({
  onExplore,
  onAsk,
}: {
  onExplore: () => void;
  onAsk: (q: string) => void;
}) {
  const space = useStore((s) => s.space);
  const health = useStore((s) => s.health);
  const select = useStore((s) => s.select);
  const setPanel = useStore((s) => s.setPanel);
  const setExplainPair = useStore((s) => s.setExplainPair);
  const setShiftDeltas = useStore((s) => s.setShiftDeltas);
  const [q, setQ] = useState("");
  const [pairs, setPairs] = useState<Pair[]>([]);
  const [pairsBusy, setPairsBusy] = useState(true);

  useEffect(() => {
    if (!space) return;
    const byId = new Map(space.dishes.map((d) => [d.id, d]));
    const seeds = SEEDS.filter((id) => byId.has(id));
    let live = true;
    setPairsBusy(true);
    Promise.all(seeds.map((id) => api.twins(id, 3)))
      .then((results) => {
        if (!live) return;
        const next: Pair[] = [];
        for (const r of results) {
          const source = byId.get(r.source_id);
          if (!source) continue;
          const pick =
            r.twins.find((t) => byId.get(t.dish_id)?.cuisine !== source.cuisine) ?? r.twins[0];
          const twinDish = pick ? byId.get(pick.dish_id) : null;
          if (pick && twinDish) next.push({ source, twin: pick, twinDish });
        }
        setPairs(next);
      })
      .catch(() => {
        if (live) setPairs([]);
      })
      .finally(() => {
        if (live) setPairsBusy(false);
      });
    return () => {
      live = false;
    };
  }, [space]);

  const openDish = (id: string, panel: "twins" | "shift" = "twins") => {
    select(id);
    setPanel(panel);
    onExplore();
  };

  const submitCraving = () => {
    const text = q.trim();
    if (!text) return;
    if (health?.grok_configured) {
      onAsk(text);
      return;
    }
    if (!space) return;
    const hits = matchDishes(text, space.dishes, 1);
    const lower = text.toLowerCase();
    if (hits[0]) {
      openDish(hits[0].id, /light|sour|acid|spic|smok/.test(lower) ? "shift" : "twins");
      if (/light/.test(lower)) setShiftDeltas({ rich: -0.8, sour: 1.2 });
      else if (/spic/.test(lower)) setShiftDeltas({ spicy: 1.4 });
      else if (/smok/.test(lower)) setShiftDeltas({ smoky: 1.2, roasted: 0.6 });
      return;
    }
    const craving = CRAVINGS.find((c) => lower.includes(c.label.toLowerCase()) || lower.includes(c.dim));
    const dish = craving ? pickByDim(space.dishes, craving.dim) : space.dishes[0];
    if (dish) openDish(dish.id);
  };

  return (
    <div className="page">
      <div className="discover">
        <section className="hero">
          <h1>What are you craving?</h1>
          <p className="lede">Discover food by how it tastes—not what cuisine it’s called.</p>
          <form
            className="hero-search"
            onSubmit={(e) => {
              e.preventDefault();
              submitCraving();
            }}
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Something like ramen, but lighter..."
              aria-label="What are you craving"
            />
            <button type="submit" className="primary">
              Discover
            </button>
          </form>
          <div className="craving-chips">
            {CRAVINGS.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => {
                  const dish = space ? pickByDim(space.dishes, c.dim) : null;
                  if (dish) openDish(dish.id);
                }}
              >
                {c.label}
              </button>
            ))}
          </div>
        </section>

        <section>
          <div className="section-head">
            <h2>Unexpected matches</h2>
            <p>Different dishes. Surprisingly similar tastes.</p>
          </div>
          {pairsBusy && pairs.length === 0 && (
            <div className="pair-grid">
              <div className="pair-card"><div className="skeleton" /><div className="skeleton short" /></div>
              <div className="pair-card"><div className="skeleton" /><div className="skeleton short" /></div>
              <div className="pair-card"><div className="skeleton" /><div className="skeleton short" /></div>
            </div>
          )}
          {pairs.length > 0 && (
            <div className="pair-grid">
              {pairs.map((p) => {
                const shared = p.twin.shared_dims.slice(0, 3).map((d) => d.replaceAll("_", " ")).join(" · ");
                return (
                  <button
                    key={`${p.source.id}-${p.twin.dish_id}`}
                    type="button"
                    className="pair-card"
                    onClick={() => {
                      useStore.getState().select(p.source.id);
                      setExplainPair(p.source.id, p.twin.dish_id);
                      onExplore();
                    }}
                  >
                    <div className="pair-visuals">
                      <DishVisual dish={p.source} />
                      <span className="swap">↕</span>
                      <DishVisual dish={p.twinDish} />
                    </div>
                    <h3>
                      {p.source.name}
                      <span className="muted"> & </span>
                      {p.twinDish.name}
                    </h3>
                    {shared ? <p className="taste-line">{shared}</p> : null}
                    <p className="pair-sub">{closerThan(p.twin.similarity_pct)}</p>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <div className="map-teaser">
          <div>
            <h2>Explore the Taste Map</h2>
            <p>See dishes by how they taste—not their labels.</p>
            <button type="button" className="primary" onClick={onExplore}>
              Open Taste Map
            </button>
          </div>
          {space?.dishes[0] && (
            <div className="food-card compact" style={{ maxWidth: 320 }}>
              <DishVisual dish={space.dishes.find((d) => d.id === "pho_bo") ?? space.dishes[0]} />
              <div className="food-card-body">
                <h4>{(space.dishes.find((d) => d.id === "pho_bo") ?? space.dishes[0]).name}</h4>
                <p className="taste-line">
                  {topLabels((space.dishes.find((d) => d.id === "pho_bo") ?? space.dishes[0]).vector, space.dims, 3).join(
                    " · ",
                  )}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
