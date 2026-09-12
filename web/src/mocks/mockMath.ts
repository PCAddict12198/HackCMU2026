// Mock-only approximations so every dish is clickable before the real API exists. Results are
// FAKE except projectDelta, which is the engine's real linear projection of a shift in sigma units.
import type {
  Deltas,
  DimId,
  DishPoint,
  ExplainResponse,
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

export function mockExplain(space: SpaceResponse, a: string, b: string): ExplainResponse {
  const A = find(space, a);
  const B = find(space, b);
  const dims = space.meta.dim_order.map((dim) => ({ dim, a: A?.vector[dim] ?? 0, b: B?.vector[dim] ?? 0 }));
  const total = dims.reduce((s, x) => s + (x.a - x.b) ** 2, 0) || 1;
  return {
    a,
    b,
    similarity_pct: 50,
    distance: Math.sqrt(total),
    dims: dims.map((x) => ({ ...x, distance_share: (x.a - x.b) ** 2 / total })),
    attributions: { a: {}, b: {} },
  };
}
