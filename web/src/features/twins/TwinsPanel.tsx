import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { TwinsResponse } from "../../contract";
import { useStore } from "../../state/store";
import { closerThan } from "../shared/copy";
import { Radar, radarAxes } from "../shared/Radar";
import { ErrorState, Loading } from "../shared/Status";
import { cuisineColor } from "../galaxy/colors";

export function TwinsPanel() {
  const selectedId = useStore((s) => s.selectedId);
  const space = useStore((s) => s.space);
  const setHighlights = useStore((s) => s.setHighlights);
  const setExplainPair = useStore((s) => s.setExplainPair);
  const focusDish = useStore((s) => s.focusDish);
  const setTwinHighlight = useStore((s) => s.setTwinHighlight);
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
  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  const topTwin = data?.twins[0];
  const twinDish = space?.dishes.find((d) => d.id === topTwin?.dish_id);
  const axes = useMemo(() => {
    if (!source || !twinDish || !space) return [];
    return radarAxes(source.vector, twinDish.vector, space.meta.dim_order);
  }, [source, twinDish, space]);

  if (!selectedId) return <p className="muted">Click a star to find its flavor twins.</p>;
  return (
    <div>
      <h3>Flavor twins{data ? ` of ${name(data.source_id)}` : selectedId ? ` of ${name(selectedId)}` : ""}</h3>
      {error != null && <ErrorState error={error} onRetry={() => setTick((n) => n + 1)} />}
      {busy && !data && <Loading label="Searching flavor twins..." />}
      {busy && data && <p className="muted small">Updating twins…</p>}
      {data && error == null && (
        <>
      {data.relaxation_level > 0 && <p className="muted small relax">{data.relaxation_note}</p>}
      {source && twinDish && axes.length > 0 && (
        <Radar
          axes={axes}
          series={[
            { label: source.name, color: cuisineColor(source.cuisine), values: axes.map((d) => source.vector[d] ?? 0) },
            { label: twinDish.name, color: cuisineColor(twinDish.cuisine), values: axes.map((d) => twinDish.vector[d] ?? 0) },
          ]}
        />
      )}
      {data.twins.map((t) => (
        <div key={t.dish_id} className="card">
          <div className="row">
            <strong>{name(t.dish_id)}</strong>
            <span className="pill">{closerThan(t.similarity_pct)}</span>
          </div>
          <div className="small">shared: {t.shared_dims.join(", ") || "-"}</div>
          <div className="small">
            differs: {t.diffs.map((d) => `${d.dim} ${d.delta > 0 ? "+" : ""}${d.delta.toFixed(2)}`).join(", ")}
          </div>
          <div className="row">
            <button
              type="button"
              onClick={() => {
                setTwinHighlight(t.dish_id);
                focusDish(t.dish_id);
              }}
            >
              Fly to twin
            </button>
            <button type="button" onClick={() => setExplainPair(data.source_id, t.dish_id)}>
              Why?
            </button>
          </div>
        </div>
      ))}
        </>
      )}
    </div>
  );
}
