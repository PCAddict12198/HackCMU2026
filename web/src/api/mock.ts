// Mock mode: serves the canonical contract fixtures (contracts/fixtures/api) so the whole UI can be
// built before the API exists. URL knobs: ?mockLatency=300  ?mockError=not_found  ?mockLarge=1
import type { ErrorCode } from "../contract";
import { fixtures } from "../mocks/fixtures";
import { mockExplain, mockShift, mockTwins } from "../mocks/mockMath";
import { ApiError, type TasteSpaceApi } from "./types";

const params = new URLSearchParams(globalThis.location?.search ?? "");
const LATENCY = Number(params.get("mockLatency") ?? 120);
const FORCED = params.get("mockError") as ErrorCode | null;
const LARGE = params.get("mockLarge") === "1";

const space = () => (LARGE ? fixtures.spaceLarge : fixtures.space);

async function respond<T>(endpoint: string, make: () => T): Promise<T> {
  await new Promise((r) => setTimeout(r, LATENCY));
  const applies = FORCED && (FORCED !== "grok_unavailable" || endpoint === "ask") && endpoint !== "health";
  if (applies && FORCED) {
    const e = fixtures.errors[FORCED]?.error ?? { code: FORCED, message: "mock error" };
    throw new ApiError(e.code, `[mock] ${e.message}`);
  }
  return structuredClone(make());
}

export const mockApi: TasteSpaceApi = {
  health: () => respond("health", () => ({ ...fixtures.health, grok_configured: FORCED !== "grok_unavailable" })),
  space: () => respond("space", space),
  twins: (dishId, k = 3) =>
    respond("twins", () =>
      !LARGE && dishId === fixtures.twins.source_id ? fixtures.twins : mockTwins(space(), dishId, k),
    ),
  shift: (req) => respond("shift", () => mockShift(space(), req)),
  explain: (a, b) =>
    respond("explain", () =>
      !LARGE && a === fixtures.explain.a && b === fixtures.explain.b ? fixtures.explain : mockExplain(space(), a, b),
    ),
  recipe: () => respond("recipe", () => fixtures.recipe),
  ask: () => respond("ask", () => fixtures.ask),
};
