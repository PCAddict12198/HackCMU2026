import { useEffect } from "react";
import { api } from "../../api/client";
import { useStore } from "../../state/store";

function deltasActive(d: Record<string, number | undefined>): boolean {
  return Object.values(d).some((v) => v != null && Math.abs(v) >= 0.05);
}

/** Runs the shift call when Grok (or anything) moves a craving while ShiftPanel isn't open. */
export function ShiftEngine() {
  const selectedId = useStore((s) => s.selectedId);
  const shiftDeltas = useStore((s) => s.shiftDeltas);
  const panel = useStore((s) => s.panel);
  const setShiftResult = useStore((s) => s.setShiftResult);
  const setHighlights = useStore((s) => s.setHighlights);

  useEffect(() => {
    if (!selectedId || panel === "shift" || !deltasActive(shiftDeltas)) return;
    let live = true;
    const t = setTimeout(() => {
      api
        .shift({ dish_id: selectedId, deltas: shiftDeltas, k: 5 })
        .then((r) => {
          if (!live) return;
          setShiftResult(r);
          setHighlights(r.results.map((x) => x.dish_id));
        })
        .catch(() => undefined);
    }, 120);
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [selectedId, shiftDeltas, panel, setShiftResult, setHighlights]);
  return null;
}
