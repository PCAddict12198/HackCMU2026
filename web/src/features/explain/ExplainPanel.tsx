import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { ExplainResponse } from "../../contract";
import { useStore } from "../../state/store";
import { closerThan } from "../shared/copy";
import { AttributionBars } from "../shared/ProvenanceChip";
import { ErrorState, Loading } from "../shared/Status";
import { DishCard } from "../dish/DishCard";
import { SensoryCompare } from "../dish/SensoryCompare";
import { dimLabel } from "../dish/sensory";

export function ExplainPanel() {
  const pair = useStore((s) => s.explainPair);
  const space = useStore((s) => s.space);
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!pair) return;
    let live = true;
    setBusy(true);
    api
      .explain(pair[0], pair[1])
      .then((r) => live && (setData(r), setError(null)))
      .catch((e) => live && setError(e))
      .finally(() => live && setBusy(false));
    return () => {
      live = false;
    };
  }, [pair, tick]);

  const dishOf = (id: string) => space?.dishes.find((d) => d.id === id);
  const dishA = dishOf(data?.a ?? pair?.[0] ?? "");
  const dishB = dishOf(data?.b ?? pair?.[1] ?? "");
  const sharedHigh = useMemo(() => {
    if (!data) return [];
    return [...data.dims].filter((d) => d.a >= 0.4 && d.b >= 0.4).sort((x, y) => Math.min(y.a, y.b) - Math.min(x.a, x.b)).slice(0, 4);
  }, [data]);
  const compareDims = useMemo(() => {
    if (!data) return [];
    return [...data.dims].sort((x, y) => Math.max(y.a, y.b) - Math.max(x.a, x.b)).slice(0, 6).map((d) => d.dim);
  }, [data]);

  if (!pair) return <p className="muted">Open a flavor twin and tap “Why this match?”</p>;
  const top = data ? [...data.dims].sort((x, y) => y.distance_share - x.distance_share)[0]?.dim : undefined;
  const story =
    dishA && dishB && sharedHigh.length
      ? `Both dishes are ${sharedHigh.map((d) => dimLabel(space?.dims, d.dim).toLowerCase()).join(", ")}, despite coming from different kitchens.`
      : "These two sit near each other in TasteSpace even when the cuisines look unrelated.";

  return (
    <div>
      <h3>Why this match?</h3>
      {error != null && <ErrorState error={error} onRetry={() => setTick((n) => n + 1)} />}
      {busy && !data && <Loading label="Tasting the pair…" />}
      {dishA && dishB && (
        <div className="twin-pair">
          <DishCard dish={dishA} dims={space?.dims} compact />
          <DishCard dish={dishB} dims={space?.dims} compact />
        </div>
      )}
      {data && error == null && (
        <>
          <h4>Why you’ll probably recognize the flavor</h4>
          <p className="small">{story}</p>
          {dishA && dishB && compareDims.length > 0 && (
            <SensoryCompare
              dims={compareDims}
              meta={space?.dims}
              aName={dishA.name}
              bName={dishB.name}
              aVec={dishA.vector}
              bVec={dishB.vector}
            />
          )}
          <p className="small">
            <strong>{closerThan(data.similarity_pct)}</strong>
          </p>
          <details className="tech">
            <summary>See how TasteSpace calculated this</summary>
            <table>
              <thead>
                <tr>
                  <th>taste</th>
                  <th>{dishA?.name}</th>
                  <th>{dishB?.name}</th>
                  <th>share</th>
                </tr>
              </thead>
              <tbody>
                {[...data.dims]
                  .sort((x, y) => y.distance_share - x.distance_share)
                  .slice(0, 8)
                  .map((d) => (
                    <tr key={d.dim}>
                      <td>{dimLabel(space?.dims, d.dim)}</td>
                      <td>{d.a.toFixed(2)}</td>
                      <td>{d.b.toFixed(2)}</td>
                      <td>{(100 * d.distance_share).toFixed(0)}%</td>
                    </tr>
                  ))}
              </tbody>
            </table>
            {top && (
              <>
                <h4>Ingredients behind {dimLabel(space?.dims, top)}</h4>
                <p className="small muted">{dishA?.name}</p>
                <AttributionBars items={(data.attributions.a[top] ?? []).slice(0, 6)} />
                <p className="small muted">{dishB?.name}</p>
                <AttributionBars items={(data.attributions.b[top] ?? []).slice(0, 6)} />
              </>
            )}
          </details>
        </>
      )}
    </div>
  );
}
