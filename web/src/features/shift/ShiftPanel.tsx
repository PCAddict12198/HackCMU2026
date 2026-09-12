import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { DimId } from "../../contract";
import { useStore } from "../../state/store";
import { closerThan, movedBits, shiftFormula } from "../shared/copy";
import { ErrorState, Loading } from "../shared/Status";

const SLIDERS: DimId[] = ["rich", "sour", "spicy", "smoky", "brothy", "sweet"];

const PRESETS: { key: string; label: string; deltas: Partial<Record<DimId, number>> }[] = [
  { key: "l", label: "Lighter + more acidic (L)", deltas: { rich: -0.8, sour: 1.2 } },
  { key: "s", label: "Spicier (S)", deltas: { spicy: 1.4 } },
  { key: "m", label: "Smokier (M)", deltas: { smoky: 1.2, roasted: 0.6 } },
];

export function ShiftPanel() {
  const { selectedId, space, shiftDeltas, shiftResult, setShiftDelta, setShiftDeltas, resetShift, setShiftResult, setHighlights } =
    useStore();
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!selectedId) return;
    let live = true;
    const t = setTimeout(() => {
      api
        .shift({ dish_id: selectedId, deltas: shiftDeltas, k: 5 })
        .then((r) => {
          if (!live) return;
          setShiftResult(r);
          setHighlights(r.results.map((x) => x.dish_id));
          setError(null);
        })
        .catch((e) => live && setError(e));
    }, 120);
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [selectedId, shiftDeltas, setShiftResult, setHighlights, tick]);

  const dim = (id: DimId) => space?.dims.find((d) => d.id === id);
  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  const formula = useMemo(() => (selectedId ? shiftFormula(selectedId, shiftDeltas) : ""), [selectedId, shiftDeltas]);

  if (!selectedId) return <p className="muted">Select a dish, then move the sliders.</p>;
  return (
    <div>
      <h3>Shift {name(selectedId)}</h3>
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
      <div className="how-card">
        <div className="small muted">HOW?</div>
        <code>{formula}</code>
      </div>
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
      {!error && !shiftResult && <Loading label="Shifting through flavor space..." />}
      {shiftResult && (
        <>
          {shiftResult.relaxation_level > 0 && <p className="muted small relax">{shiftResult.relaxation_note}</p>}
          <ol>
            {shiftResult.results.map((r) => (
              <li key={r.dish_id}>
                {name(r.dish_id)} <span className="pill">{closerThan(r.similarity_pct)}</span>
                {movedBits(r.moved) && <div className="small muted">moved {movedBits(r.moved)}</div>}
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
