import { dimLabel } from "./sensory";
import type { DimMeta } from "../../contract";

export function SensoryCompare({
  dims,
  meta,
  aName,
  bName,
  aVec,
  bVec,
}: {
  dims: string[];
  meta?: DimMeta[];
  aName: string;
  bName: string;
  aVec: Record<string, number>;
  bVec: Record<string, number>;
}) {
  return (
    <div className="sense-compare">
      <div className="sense-head">
        <span />
        <span>{aName}</span>
        <span>{bName}</span>
      </div>
      {dims.map((id) => (
        <div key={id} className="sense-row">
          <span>{dimLabel(meta, id)}</span>
          <div className="sense-bar">
            <i style={{ width: `${Math.round(100 * Math.min(1, Math.max(0, aVec[id] ?? 0)))}%` }} />
          </div>
          <div className="sense-bar">
            <i style={{ width: `${Math.round(100 * Math.min(1, Math.max(0, bVec[id] ?? 0)))}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DimDots({
  dims,
  meta,
  a,
  b,
}: {
  dims: string[];
  meta?: DimMeta[];
  a: Record<string, number>;
  b: Record<string, number>;
}) {
  return (
    <div className="dim-dots">
      {dims.slice(0, 5).map((id) => {
        const av = Math.min(1, Math.max(0, a[id] ?? 0));
        const bv = Math.min(1, Math.max(0, b[id] ?? 0));
        return (
          <div key={id} className="dim-dot-row">
            <span>{dimLabel(meta, id)}</span>
            <div className="dim-track" aria-hidden="true">
              <i className="dot a" style={{ left: `${av * 100}%` }} />
              <i className="dot b" style={{ left: `${bv * 100}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
