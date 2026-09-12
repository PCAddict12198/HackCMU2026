import type { DimMeta, DishPoint } from "../../contract";

export function dimLabel(dims: DimMeta[] | undefined, id: string): string {
  return dims?.find((d) => d.id === id)?.label ?? id.replaceAll("_", " ");
}

export function topDimIds(vector: Record<string, number>, n = 3, min = 0.32): string[] {
  return Object.entries(vector)
    .sort((a, b) => b[1] - a[1])
    .filter(([, v]) => v >= min)
    .slice(0, n)
    .map(([id]) => id);
}

export function topLabels(vector: Record<string, number>, dims: DimMeta[] | undefined, n = 3): string[] {
  return topDimIds(vector, n).map((id) => dimLabel(dims, id));
}

export function pickByDim(dishes: DishPoint[], dim: string): DishPoint | null {
  if (!dishes.length) return null;
  return [...dishes].sort((a, b) => (b.vector[dim] ?? 0) - (a.vector[dim] ?? 0))[0] ?? null;
}

export function matchDishes(query: string, dishes: DishPoint[], limit = 8): DishPoint[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const tokens = q.split(/\s+/).filter((t) => t.length > 1);
  const scored = dishes
    .map((d) => {
      const name = d.name.toLowerCase();
      const hay = `${name} ${d.id.replaceAll("_", " ")} ${d.cuisine} ${d.blurb} ${d.format.replaceAll("_", " ")}`.toLowerCase();
      let s = 0;
      if (name === q || d.id.replaceAll("_", " ") === q) s += 20;
      if (name.startsWith(q)) s += 12;
      if (name.split(/\s+/).some((w) => w.startsWith(q))) s += 6;
      if (hay.includes(q)) s += 8;
      for (const t of tokens) {
        if (name.includes(t)) s += 3;
        else if (hay.includes(t)) s += 2;
      }
      return { d, s };
    })
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s || a.d.name.localeCompare(b.d.name));
  return scored.slice(0, limit).map((x) => x.d);
}

export const CRAVINGS: { id: string; label: string; dim: string }[] = [
  { id: "comforting", label: "Comforting", dim: "rich" },
  { id: "fresh", label: "Fresh", dim: "herbal" },
  { id: "spicy", label: "Spicy", dim: "spicy" },
  { id: "rich", label: "Rich", dim: "rich" },
  { id: "sweet", label: "Sweet", dim: "sweet" },
  { id: "smoky", label: "Smoky", dim: "smoky" },
  { id: "bright", label: "Bright & acidic", dim: "sour" },
];
