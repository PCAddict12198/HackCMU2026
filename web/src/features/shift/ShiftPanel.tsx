// Taste Shift (baseline). Sliders are sigma units (-2..2) sent to POST /api/shift (debounced).
// P3 TODO: animate the target glide, show the "HOW" formula, keyboard shortcuts for the demo.
import { useEffect, useState } from "react";
import { api, errorMessage } from "../../api/client";
import type { DimId } from "../../contract";
import { useStore } from "../../state/store";

const SLIDERS: DimId[] = ["rich", "sour", "spicy", "smoky", "brothy", "sweet"];

export function ShiftPanel() {
  const { selectedId, space, shiftDeltas, shiftResult, setShiftDelta, resetShift, setShiftResult, setHighlights } =
    useStore();
  const [error, setError] = useState<string | null>(null);

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
        .catch((e) => live && setError(errorMessage(e)));
    }, 120);
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [selectedId, shiftDeltas, setShiftResult, setHighlights]);

  const dim = (id: DimId) => space?.dims.find((d) => d.id === id);
  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
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
      <button onClick={resetShift}>Reset</button>
      {error && <p className="error">{error}</p>}
      {shiftResult && (
        <>
          <p className="muted small">{shiftResult.relaxation_note}</p>
          <ol>
            {shiftResult.results.map((r) => (
              <li key={r.dish_id}>
                {name(r.dish_id)} <span className="pill">{r.similarity_pct.toFixed(0)} pct</span>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
