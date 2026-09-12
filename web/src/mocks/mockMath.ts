// Mock-only approximations so every dish is clickable before the real API exists. Results are
// FAKE except projectDelta, which is the engine's real linear projection of a shift in sigma units.
import type {
  Contribution,
  Deltas,
  DimId,
  DishPoint,
  ExplainResponse,
  RecipeRequest,
  RecipeResponse,
  ShiftRequest,
  ShiftResponse,
  SpaceResponse,
  TwinsResponse,
  Vec3,
} from "../contract";

export function projectDelta(space: SpaceResponse, deltas: Deltas): Vec3 {
  const { components, weights, scale } = space.pca;
  const out = [0, 0, 0];
  space.meta.dim_order.forEach((dim, k) => {
    const d = deltas[dim] ?? 0;
    if (!d) return;
    for (let i = 0; i < 3; i++) out[i] += scale * components[i][k] * d * Math.sqrt(weights[k]);
  });
  return out as unknown as Vec3;
}

export const dist3 = (a: Vec3, b: Vec3) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const find = (space: SpaceResponse, id: string) => space.dishes.find((d) => d.id === id);
const pct = (rank: number, total: number) => Math.round(1000 * (1 - rank / Math.max(total, 1))) / 10;

function vecDiffs(a: DishPoint, b: DishPoint) {
  const dims = Object.keys(a.vector) as DimId[];
  const diffs = dims
    .map((dim) => ({ dim, delta: (b.vector[dim] ?? 0) - (a.vector[dim] ?? 0) }))
    .sort((x, y) => Math.abs(y.delta) - Math.abs(x.delta));
  const shared = dims
    .filter((d) => Math.min(a.vector[d] ?? 0, b.vector[d] ?? 0) >= 0.2)
    .sort((x, y) => Math.min(b.vector[y] ?? 0, a.vector[y] ?? 0) - Math.min(b.vector[x] ?? 0, a.vector[x] ?? 0));
  return { diffs: diffs.slice(0, 3), shared: shared.slice(0, 5) };
}

export function mockTwins(space: SpaceResponse, dishId: string, k = 3): TwinsResponse {
  const src = find(space, dishId);
  if (!src) return { source_id: dishId, relaxation_level: 0, relaxation_note: "MOCK: unknown dish", twins: [] };
  const pool = space.dishes
    .filter((d) => d.id !== dishId && d.course === src.course && d.cuisine !== src.cuisine)
    .sort((a, b) => dist3(src.xyz, a.xyz) - dist3(src.xyz, b.xyz));
  return {
    source_id: dishId,
    relaxation_level: 0,
    relaxation_note: "MOCK: nearest other-cuisine dishes by 3D distance",
    twins: pool.slice(0, k).map((d, i) => {
      const { diffs, shared } = vecDiffs(src, d);
      return { dish_id: d.id, similarity_pct: pct(i, pool.length), distance: dist3(src.xyz, d.xyz),
               cuisine_distance: 1, shared_dims: shared, diffs };
    }),
  };
}

export function mockShift(space: SpaceResponse, req: ShiftRequest): ShiftResponse {
  const src = find(space, req.dish_id);
  const deltas = (req.deltas ?? {}) as Deltas;
  const d = projectDelta(space, deltas);
  const target = (src ? [src.xyz[0] + d[0], src.xyz[1] + d[1], src.xyz[2] + d[2]] : d) as unknown as Vec3;
  const touched = (Object.keys(deltas) as DimId[]).filter((k) => Math.abs(deltas[k] ?? 0) >= 0.05);
  const pool = space.dishes
    .filter((x) => x.id !== req.dish_id && (!src || x.course === src.course))
    .sort((a, b) => dist3(target, a.xyz) - dist3(target, b.xyz));
  return {
    source_id: req.dish_id,
    target_z: Object.fromEntries(space.meta.dim_order.map((dim) => [dim, deltas[dim] ?? 0])),
    target_xyz: target,
    relaxation_level: 0,
    relaxation_note: "MOCK: nearest to the projected target",
    results: pool.slice(0, req.k ?? 5).map((x, i) => ({
      dish_id: x.id,
      similarity_pct: pct(i, pool.length),
      distance: dist3(target, x.xyz),
      moved: Object.fromEntries(touched.map((dim) => [dim, (x.vector[dim] ?? 0) - (src?.vector[dim] ?? 0)])),
    })),
  };
}

function mockAttribs(dish: DishPoint | undefined): Record<string, Contribution[]> {
  if (!dish) return {};
  const out: Record<string, Contribution[]> = {};
  for (const [dim, value] of Object.entries(dish.vector)) {
    if (value < 0.12) continue;
    out[dim] = [{ kind: "ingredient", id: dish.id, value, src: "fixture", process: [] }];
  }
  return out;
}

export function mockExplain(space: SpaceResponse, a: string, b: string): ExplainResponse {
  const A = find(space, a);
  const B = find(space, b);
  const dims = space.meta.dim_order.map((dim) => ({ dim, a: A?.vector[dim] ?? 0, b: B?.vector[dim] ?? 0 }));
  const total = dims.reduce((s, x) => s + (x.a - x.b) ** 2, 0) || 1;
  const rank = Math.max(0, space.dishes.findIndex((d) => d.id === b));
  return {
    a,
    b,
    similarity_pct: pct(rank, space.dishes.length),
    distance: Math.sqrt(total),
    dims: dims.map((x) => ({ ...x, distance_share: (x.a - x.b) ** 2 / total })),
    attributions: { a: mockAttribs(A), b: mockAttribs(B) },
  };
}

const STOP = new Set([
  "the",
  "and",
  "with",
  "for",
  "tsp",
  "tbsp",
  "cup",
  "cups",
  "gram",
  "grams",
  "pinch",
  "into",
  "this",
  "that",
  "your",
]);

function tokens(s: string): string[] {
  return s
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 2 && !STOP.has(t) && !/^\d+$/.test(t));
}

function dishHay(d: DishPoint): string {
  return `${d.name} ${d.id.replaceAll("_", " ")} ${d.blurb} ${d.cuisine} ${d.format.replaceAll("_", " ")}`.toLowerCase();
}

/** Mock-only: place a recipe by word overlap with the catalog. Not the engine. */
export function mockRecipe(space: SpaceResponse, req: RecipeRequest): RecipeResponse {
  const rawLines = req.text
    .split(/\n+/)
    .map((l) => l.trim())
    .filter(Boolean);
  const lines = (rawLines.length ? rawLines : ["(empty recipe)"]).map((raw) => {
    const ts = tokens(raw);
    const hit = space.dishes.find((d) => {
      const hay = dishHay(d);
      return ts.some((t) => hay.includes(t));
    });
    return {
      raw,
      status: hit ? ("fuzzy" as const) : ("unmatched" as const),
      ingredient_id: hit ? hit.id : null,
      grams: null,
      confidence: hit ? 0.55 : 0,
      process: [] as RecipeResponse["lines"][number]["process"],
      note: hit ? `MOCK: closest catalog dish “${hit.name}”` : "MOCK: no catalog word on this line",
    };
  });
  const allTok = tokens(req.text);
  const scored = space.dishes
    .map((d) => {
      const hay = dishHay(d);
      const s = allTok.reduce((n, t) => n + (hay.includes(t) ? (d.name.toLowerCase().includes(t) ? 3 : 1) : 0), 0);
      return { d, s };
    })
    .sort((a, b) => b.s - a.s || dist3(a.d.xyz, [0, 0, 0] as unknown as Vec3) - dist3(b.d.xyz, [0, 0, 0] as unknown as Vec3));
  const top = (scored[0]?.s ? scored.filter((x) => x.s > 0) : scored).slice(0, 5);
  const used = top.length ? top : scored.slice(0, 5);
  const n = Math.max(used.length, 1);
  const xyz = used
    .reduce((acc, x) => [acc[0] + x.d.xyz[0], acc[1] + x.d.xyz[1], acc[2] + x.d.xyz[2]], [0, 0, 0])
    .map((v) => v / n) as unknown as Vec3;
  const vector = Object.fromEntries(
    space.meta.dim_order.map((dim) => [dim, used.reduce((s, x) => s + (x.d.vector[dim] ?? 0), 0) / n]),
  );
  const attributions: Record<string, Contribution[]> = {};
  const matched = lines.filter((l) => l.status !== "unmatched").length;
  const dessertHint = allTok.some((t) => ["sugar", "cream", "mango", "sweet", "milk", "custard", "cake"].includes(t));
  return {
    name: req.name?.trim() || "Your recipe",
    course: req.course ?? (dessertHint ? "dessert" : "savory"),
    lines,
    coverage: { matched, total: lines.length },
    used_grok: false,
    vector,
    xyz,
    neighbors: used.map((x, i) => ({
      dish_id: x.d.id,
      similarity_pct: pct(i, Math.max(space.dishes.length - 1, 1)),
      distance: dist3(xyz, x.d.xyz),
    })),
    attributions,
  };
}

