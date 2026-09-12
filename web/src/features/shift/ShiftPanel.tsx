import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { DimId } from "../../contract";
import { useStore } from "../../state/store";
import { closerThan, movedBits, shiftFormula } from "../shared/copy";
import { ErrorState, Loading } from "../shared/Status";
import { DishCard } from "../dish/DishCard";

const SLIDERS: DimId[] = ["rich", "sour", "spicy", "smoky", "brothy", "sweet"];

const PRESETS: { key: string; label: string; deltas: Partial<Record<DimId, number>> }[] = [
  { key: "l", label: "Lighter + brighter", deltas: { rich: -0.8, sour: 1.2 } },
  { key: "s", label: "Spicier", deltas: { spicy: 1.4 } },
  { key: "m", label: "Smokier", deltas: { smoky: 1.2, roasted: 0.6 } },
];

export function ShiftPanel() {
  const { selectedId, space, shiftDeltas, shiftResult, setShiftDelta, setShiftDeltas, resetShift, setShiftResult, setHighlights, select, setPanel } =
    useStore();
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!selectedId) return;
    let live = true;
    const t = setTimeout(() => {
      setBusy(true);
      api
        .shift({ dish_id: selectedId, deltas: shiftDeltas, k: 5 })
        .then((r) => {
          if (!live) return;
          setShiftResult(r);
          setHighlights(r.results.map((x) => x.dish_id));
          setError(null);
        })
        .catch((e) => live && setError(e))
        .finally(() => live && setBusy(false));
    }, 120);
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [selectedId, shiftDeltas, setShiftResult, setHighlights, tick]);

  const dim = (id: DimId) => space?.dims.find((d) => d.id === id);
  const dishOf = (id: string) => space?.dishes.find((d) => d.id === id);
  const source = dishOf(selectedId ?? "");
  const formula = selectedId ? shiftFormula(selectedId, shiftDeltas) : "";
  const path =
    source && shiftResult
      ? [source, ...shiftResult.results.map((r) => dishOf(r.dish_id)).filter((d): d is NonNullable<typeof d> => !!d)]
      : [];

  if (!selectedId) return <p className="muted">Select a dish, then move your craving.</p>;
  return (
    <div>
      <h3>Make it more your taste</h3>
      <p className="lede-sm">
        Starting with <strong>{source?.name ?? selectedId}</strong>. Move the sliders and watch the map follow.
      </p>
      {SLIDERS.map((id) => (
        <label key={id} className="slider">
          <span className="small">{dim(id)?.low_label ?? id}</span>
          <input
            type="range"
            min={-2}
            max={2}
            step={0.1}
            value={shiftDeltas[id] ?? 0}
            onChange={(e) => setShiftDelta(id, Number(e.target.value))}
          />
          <span className="small">{dim(id)?.high_label ?? id}</span>
        </label>
      ))}
      <div className="row wrap">
        <button type="button" onClick={resetShift}>
          Reset
        </button>
        {PRESETS.map((p) => (
          <button key={p.key} type="button" onClick={() => setShiftDeltas(p.deltas)}>
            {p.label}
          </button>
        ))}
      </div>
      {error != null && <ErrorState error={error} onRetry={() => setTick((n) => n + 1)} />}
      {busy && !shiftResult && error == null && <Loading label="Moving your craving…" />}
      {busy && shiftResult && error == null && <p className="muted small">Updating nearby dishes…</p>}
      {error == null && shiftResult && (
        <>
          {path.length > 1 && (
            <>
              <h4>A path through taste</h4>
              <ol className="craving-path">
                {path.slice(0, 4).map((d) =>
                  d ? (
                    <li key={d.id}>
                      <strong>{d.name}</strong>
                      <span className="muted small"> · {d.cuisine}</span>
                    </li>
                  ) : null,
                )}
              </ol>
            </>
          )}
          {shiftResult.relaxation_level > 0 && <p className="muted small relax">{shiftResult.relaxation_note}</p>}
          <h4>Try these</h4>
          {shiftResult.results.map((r) => {
            const d = dishOf(r.dish_id);
            if (!d) return null;
            return (
              <div key={r.dish_id} className="card">
                <DishCard
                  dish={d}
                  dims={space?.dims}
                  compact
                  onClick={() => {
                    select(r.dish_id);
                    setPanel("twins");
                  }}
                />
                <p className="small muted" style={{ margin: "8px 0 0" }}>
                  {closerThan(r.similarity_pct)}
                  {movedBits(r.moved) ? ` · ${movedBits(r.moved)}` : ""}
                </p>
              </div>
            );
          })}
        </>
      )}
      <details className="tech">
        <summary>See how TasteSpace calculated this</summary>
        <div className="how-card">
          <code>{formula}</code>
        </div>
      </details>
    </div>
  );
}
