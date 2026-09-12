import type { Contribution, ProvenanceSrc } from "../../contract";
import { SRC_LABEL } from "./copy";

export function ProvenanceChip({ src }: { src: ProvenanceSrc }) {
  if (!src) return <span className="chip">derived</span>;
  const seed = src === "seed_placeholder" || src === "grok_draft";
  return (
    <span className={`chip src src-${src}`} title={src}>
      {seed ? "⚠ " : ""}
      {SRC_LABEL[src]}
    </span>
  );
}

export function AttributionBars({ items, nameColor }: { items: Contribution[]; nameColor?: string }) {
  if (!items.length) return <p className="muted small">No attributions for this dimension.</p>;
  const max = Math.max(...items.map((c) => Math.abs(c.value)), 0.01);
  return (
    <div className="bars">
      {items.map((c) => (
        <div key={`${c.kind}-${c.id}-${c.process.join()}`} className="bar-row">
          <div className="bar-meta">
            <span style={{ color: nameColor }}>
              {c.id.replaceAll("_", " ")} {c.value >= 0 ? "+" : ""}
              {c.value.toFixed(2)}
            </span>
            {c.process.length > 0 && <span className="chip">{c.process.join(", ")}</span>}
            <ProvenanceChip src={c.src} />
          </div>
          <div className="bar">
            <i style={{ width: `${Math.min(100, (100 * Math.abs(c.value)) / max)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
