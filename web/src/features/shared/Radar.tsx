type Series = { label: string; color: string; values: number[] };

export function Radar({ axes, series }: { axes: string[]; series: Series[] }) {
  const n = axes.length;
  if (!n) return null;
  const cx = 92;
  const cy = 92;
  const r = 68;
  const pt = (i: number, v: number): [number, number] => {
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return [cx + r * v * Math.cos(a), cy + r * v * Math.sin(a)];
  };
  const ring = (scale: number) =>
    axes
      .map((_, i) => pt(i, scale).join(","))
      .join(" ");
  return (
    <svg className="radar" viewBox="0 0 184 210" role="img" aria-label="flavor radar">
      {[0.25, 0.5, 0.75, 1].map((s) => (
        <polygon key={s} points={ring(s)} className="radar-grid" />
      ))}
      {axes.map((label, i) => {
        const [x, y] = pt(i, 1.18);
        return (
          <g key={label}>
            <line x1={cx} y1={cy} x2={pt(i, 1)[0]} y2={pt(i, 1)[1]} className="radar-spoke" />
            <text x={x} y={y} textAnchor="middle" dominantBaseline="middle" className="radar-axis">
              {label}
            </text>
          </g>
        );
      })}
      {series.map((s) => (
        <polygon
          key={s.label}
          points={s.values.map((v, i) => pt(i, Math.min(Math.max(v, 0), 1)).join(",")).join(" ")}
          fill={s.color}
          fillOpacity={0.22}
          stroke={s.color}
          strokeWidth={1.5}
        />
      ))}
      {series.map((s, i) => (
        <text key={s.label} x={10} y={200 - (series.length - 1 - i) * 10} className="radar-axis" fill={s.color}>
          {s.label}
        </text>
      ))}
    </svg>
  );
}

export function radarAxes(
  a: Record<string, number>,
  b: Record<string, number>,
  order: string[],
  k = 8,
): string[] {
  return [...order]
    .sort((x, y) => Math.max(b[y] ?? 0, a[y] ?? 0) - Math.max(b[x] ?? 0, a[x] ?? 0))
    .slice(0, k);
}
