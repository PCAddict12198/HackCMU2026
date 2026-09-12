import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { ExplainResponse } from "../../contract";
import { cuisineColor } from "../galaxy/colors";
import { useStore } from "../../state/store";
import { closerThan } from "../shared/copy";
import { AttributionBars } from "../shared/ProvenanceChip";
import { Radar, radarAxes } from "../shared/Radar";
import { ErrorState, Loading } from "../shared/Status";

export function ExplainPanel() {
  const pair = useStore((s) => s.explainPair);
  const space = useStore((s) => s.space);
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!pair) return;
    let live = true;
    setData(null);
    api
      .explain(pair[0], pair[1])
      .then((r) => live && (setData(r), setError(null)))
      .catch((e) => live && setError(e));
    return () => {
      live = false;
    };
  }, [pair, tick]);

  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  const dishA = space?.dishes.find((d) => d.id === data?.a);
  const dishB = space?.dishes.find((d) => d.id === data?.b);
  const axes = useMemo(() => {
    if (!dishA || !dishB || !space) return [];
    return radarAxes(dishA.vector, dishB.vector, space.meta.dim_order);
  }, [dishA, dishB, space]);

  if (!pair) return <p className="muted">Pick "Why?" on a twin to compare two dishes.</p>;
  if (error) return <ErrorState error={error} onRetry={() => setTick((n) => n + 1)} />;
  if (!data) return <Loading label="Comparing flavor dimensions..." />;

  const dims = [...data.dims].sort((x, y) => y.distance_share - x.distance_share).slice(0, 8);
  const top = dims[0]?.dim;
  return (
    <div>
      <h3>
        {name(data.a)} vs {name(data.b)}
      </h3>
      <p className="small">{closerThan(data.similarity_pct)}</p>
      {dishA && dishB && axes.length > 0 && (
        <Radar
          axes={axes}
          series={[
            { label: dishA.name, color: cuisineColor(dishA.cuisine), values: axes.map((d) => dishA.vector[d] ?? 0) },
            { label: dishB.name, color: cuisineColor(dishB.cuisine), values: axes.map((d) => dishB.vector[d] ?? 0) },
          ]}
        />
      )}
      <table>
        <thead>
          <tr>
            <th>dim</th>
            <th>{name(data.a)}</th>
            <th>{name(data.b)}</th>
            <th>share of difference</th>
          </tr>
        </thead>
        <tbody>
          {dims.map((d) => (
            <tr key={d.dim}>
              <td>{d.dim}</td>
              <td>{d.a.toFixed(2)}</td>
              <td>{d.b.toFixed(2)}</td>
              <td>{(100 * d.distance_share).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      {top && (
        <>
          <h4>
            Why is {name(data.a)} {top}?
          </h4>
          <AttributionBars items={(data.attributions.a[top] ?? []).slice(0, 6)} />
          <h4>
            Why is {name(data.b)} {top}?
          </h4>
          <AttributionBars items={(data.attributions.b[top] ?? []).slice(0, 6)} />
        </>
      )}
    </div>
  );
}
