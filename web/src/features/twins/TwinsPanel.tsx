import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { TwinsResponse } from "../../contract";
import { useStore } from "../../state/store";
import { closerThan } from "../shared/copy";
import { ErrorState, Loading } from "../shared/Status";
import { DishCard } from "../dish/DishCard";
import { DimDots } from "../dish/SensoryCompare";
import { radarAxes } from "../shared/Radar";

export function TwinsPanel() {
  const selectedId = useStore((s) => s.selectedId);
  const space = useStore((s) => s.space);
  const setHighlights = useStore((s) => s.setHighlights);
  const setExplainPair = useStore((s) => s.setExplainPair);
  const [data, setData] = useState<TwinsResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!selectedId) return;
    let live = true;
    setError(null);
    setBusy(true);
    api
      .twins(selectedId, 3)
      .then((r) => {
        if (!live) return;
        setData(r);
        setHighlights(r.twins.map((t) => t.dish_id));
      })
      .catch((e) => live && setError(e))
      .finally(() => live && setBusy(false));
    return () => {
      live = false;
    };
  }, [selectedId, setHighlights, tick]);

  const source = space?.dishes.find((d) => d.id === selectedId);
  const dishOf = (id: string) => space?.dishes.find((d) => d.id === id);
  const topTwin = data?.twins[0];
  const twinDish = topTwin ? dishOf(topTwin.dish_id) : null;
  const axes = useMemo(() => {
    if (!source || !twinDish || !space) return [];
    return radarAxes(source.vector, twinDish.vector, space.meta.dim_order, 5);
  }, [source, twinDish, space]);

  if (!selectedId) return <p className="muted">Pick a dish on the map to find something that tastes like it.</p>;
  return (
    <div>
      <h3>Find a Flavor Twin</h3>
      <p className="lede-sm">Something that tastes like this, even if it isn’t the same kind of food.</p>
      {error != null && <ErrorState error={error} onRetry={() => setTick((n) => n + 1)} />}
      {busy && !data && <Loading label="Looking for flavor twins…" />}
      {busy && data && <p className="muted small">Updating…</p>}
      {data && error == null && (
        <>
          {data.relaxation_level > 0 && <p className="muted small relax">{data.relaxation_note}</p>}
          {source && twinDish && topTwin && (
            <>
              <div className="twin-pair">
                <DishCard dish={source} dims={space?.dims} compact />
                <DishCard dish={twinDish} dims={space?.dims} compact />
              </div>
              <p className="kicker">Surprisingly similar</p>
              <p className="small">{closerThan(topTwin.similarity_pct)}</p>
              {axes.length > 0 && (
                <DimDots dims={axes} meta={space?.dims} a={source.vector} b={twinDish.vector} />
              )}
              <button type="button" className="primary" onClick={() => setExplainPair(data.source_id, twinDish.id)}>
                Why this match?
              </button>
            </>
          )}
          <h4>Nearby in taste</h4>
          {data.twins.map((t) => {
            const d = dishOf(t.dish_id);
            if (!d) return null;
            return (
              <div key={t.dish_id} className="card">
                <DishCard
                  dish={d}
                  dims={space?.dims}
                  compact
                  onClick={() => {
                    useStore.getState().select(t.dish_id);
                  }}
                />
                <div className="row" style={{ marginTop: 8 }}>
                  <span className="pill">{closerThan(t.similarity_pct)}</span>
                  <button type="button" onClick={() => setExplainPair(data.source_id, t.dish_id)}>
                    Why this match?
                  </button>
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
