// Mock mode: serves the canonical contract fixtures (contracts/fixtures/api) so the whole UI can be
// built before the API exists. URL knobs: ?mockLatency=300  ?mockError=not_found  ?mockLarge=1
// mockError is panel-only (twins/shift/explain/recipe/ask). Space + health always load the catalog.
import type { ErrorCode } from "../contract";
import { fixtures } from "../mocks/fixtures";
import { mockExplain, mockRecipe, mockShift, mockTwins } from "../mocks/mockMath";
import { ApiError, type TasteSpaceApi } from "./types";

function qs() {
  return new URLSearchParams(globalThis.location?.search ?? "");
}

const space = () => (qs().get("mockLarge") === "1" ? fixtures.spaceLarge : fixtures.space);

async function respond<T>(endpoint: string, make: () => T): Promise<T> {
  const params = qs();
  const latency = Number(params.get("mockLatency") ?? 120);
  const forced = params.get("mockError");
  await new Promise((r) => setTimeout(r, Number.isFinite(latency) ? latency : 120));
  const panelOnly = endpoint !== "health" && endpoint !== "space";
  if (forced && panelOnly) {
    if (forced === "network") throw new ApiError("network", "[mock] network unreachable");
    if (forced === "grok_unavailable" && endpoint !== "ask") {
      /* Ask tab hides; other panels keep working */
    } else if (forced === "grok_unavailable" || fixtures.errors[forced as ErrorCode]) {
      const code = forced as ErrorCode;
      const e = fixtures.errors[code]?.error ?? { code, message: "mock error" };
      throw new ApiError(e.code, `[mock] ${e.message}`);
    }
  }
  return structuredClone(make());
}

export const mockApi: TasteSpaceApi = {
  health: () =>
    respond("health", () => ({
      ...fixtures.health,
      grok_configured: qs().get("mockError") !== "grok_unavailable",
    })),
  space: () => respond("space", space),
  twins: (dishId, k = 3) =>
    respond("twins", () =>
      qs().get("mockLarge") !== "1" && dishId === fixtures.twins.source_id ? fixtures.twins : mockTwins(space(), dishId, k),
    ),
  shift: (req) => respond("shift", () => mockShift(space(), req)),
  explain: (a, b) =>
    respond("explain", () =>
      qs().get("mockLarge") !== "1" && a === fixtures.explain.a && b === fixtures.explain.b
        ? fixtures.explain
        : mockExplain(space(), a, b),
    ),
  recipe: (req) => respond("recipe", () => mockRecipe(space(), req)),
  ask: () => respond("ask", () => fixtures.ask),
};
