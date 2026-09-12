// Explain (baseline): per-dim comparison + ingredient attributions with provenance chips.
// P3 TODO: radar chart, attribution bars, highlight seed/grok values differently.
import { useEffect, useState } from "react";
import { api, errorMessage } from "../../api/client";
import type { ExplainResponse } from "../../contract";
import { useStore } from "../../state/store";

export function ExplainPanel() {
  const pair = useStore((s) => s.explainPair);
  const space = useStore((s) => s.space);
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pair) return;
    let live = true;
    api
      .explain(pair[0], pair[1])
      .then((r) => live && (setData(r), setError(null)))
      .catch((e) => live && setError(errorMessage(e)));
    return () => {
      live = false;
    };
  }, [pair]);

  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  if (!pair) return <p className="muted">Pick "Why?" on a twin to compare two dishes.</p>;
  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Comparing...</p>;
  const dims = [...data.dims].sort((x, y) => Math.max(y.a, y.b) - Math.max(x.a, x.b)).slice(0, 8);
  return (
    <div>
      <h3>
        {name(data.a)} vs {name(data.b)}
      </h3>
      <p className="small">
        closer than <strong>{data.similarity_pct.toFixed(0)}%</strong> of same-course dish pairs
      </p>
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
      <h4>Why is {name(data.a)} {dims[0]?.dim}?</h4>
      <ul>
        {(data.attributions.a[dims[0]?.dim] ?? []).slice(0, 4).map((c) => (
          <li key={c.kind + c.id + c.process.join()} className="small">
            +{c.value.toFixed(2)} {c.id} {c.process.length > 0 && `(${c.process.join(", ")})`}{" "}
            <span className="chip">{c.src ?? c.kind}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
