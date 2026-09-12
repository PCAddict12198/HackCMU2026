// Flavor Twins (baseline). P3 TODO: side-by-side radar chart, "fly to twin", nicer cards.
import { useEffect, useState } from "react";
import { api, errorMessage } from "../../api/client";
import type { TwinsResponse } from "../../contract";
import { useStore } from "../../state/store";

export function TwinsPanel() {
  const selectedId = useStore((s) => s.selectedId);
  const space = useStore((s) => s.space);
  const setHighlights = useStore((s) => s.setHighlights);
  const setExplainPair = useStore((s) => s.setExplainPair);
  const [data, setData] = useState<TwinsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedId) return;
    let live = true;
    setError(null);
    api
      .twins(selectedId, 3)
      .then((r) => {
        if (!live) return;
        setData(r);
        setHighlights(r.twins.map((t) => t.dish_id));
      })
      .catch((e) => live && setError(errorMessage(e)));
    return () => {
      live = false;
    };
  }, [selectedId, setHighlights]);

  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  if (!selectedId) return <p className="muted">Click a star to find its flavor twins.</p>;
  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Searching...</p>;
  return (
    <div>
      <h3>Flavor twins of {name(data.source_id)}</h3>
      <p className="muted small">{data.relaxation_note}</p>
      {data.twins.map((t) => (
        <div key={t.dish_id} className="card">
          <div className="row">
            <strong>{name(t.dish_id)}</strong>
            <span className="pill">closer than {t.similarity_pct.toFixed(0)}% of pairs</span>
          </div>
          <div className="small">shared: {t.shared_dims.join(", ") || "-"}</div>
          <div className="small">
            differs: {t.diffs.map((d) => `${d.dim} ${d.delta > 0 ? "+" : ""}${d.delta.toFixed(2)}`).join(", ")}
          </div>
          <button onClick={() => setExplainPair(data.source_id, t.dish_id)}>Why?</button>
        </div>
      ))}
    </div>
  );
}
