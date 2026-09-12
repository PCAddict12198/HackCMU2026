import { describe, expect, it } from "vitest";
import { fixtures } from "./fixtures";
import { mockApi } from "../api/mock";
import { mockExplain, mockRecipe, mockShift, mockTwins, projectDelta } from "./mockMath";

describe("mock mode", () => {
  const space = fixtures.space;
  const id = fixtures.twins.source_id;

  it("fixtures are shaped like the contract", () => {
    expect(space.dishes.length).toBeGreaterThan(1);
    expect(space.meta.dim_order).toHaveLength(17);
    expect(fixtures.ask.ui_actions.length).toBeGreaterThan(0);
  });

  it("projectDelta is the engine's linear projection", () => {
    expect(projectDelta(space, {})).toEqual([0, 0, 0]);
    const one = projectDelta(space, { sour: 1 });
    const two = projectDelta(space, { sour: 2 });
    two.forEach((v, i) => expect(v).toBeCloseTo(2 * one[i], 6));
  });

  it("mock shift moves the target and never returns the source dish", () => {
    const res = mockShift(space, { dish_id: id, deltas: { sour: 1.5 }, k: 3 });
    expect(res.target_xyz).not.toEqual(space.dishes.find((d) => d.id === id)!.xyz);
    expect(res.results.map((r) => r.dish_id)).not.toContain(id);
  });

  it("mock twins come from other cuisines in the same course", () => {
    const src = space.dishes.find((d) => d.id === id)!;
    for (const t of mockTwins(space, id).twins) {
      const d = space.dishes.find((x) => x.id === t.dish_id)!;
      expect(d.cuisine).not.toBe(src.cuisine);
      expect(d.course).toBe(src.course);
    }
  });

  it("mockApi serves every endpoint", async () => {
    await expect(mockApi.space()).resolves.toHaveProperty("dishes");
    await expect(mockApi.twins(id)).resolves.toHaveProperty("twins");
    await expect(mockApi.ask({ messages: [{ role: "user", content: "hi" }] })).resolves.toHaveProperty("reply");
  });

  it("?mockLarge=1 serves the 80-dish synthetic catalog", async () => {
    expect(fixtures.spaceLarge.dishes).toHaveLength(80);
    const prev = globalThis.location;
    Object.defineProperty(globalThis, "location", { configurable: true, value: { search: "?mockLarge=1" } });
    try {
      const large = await mockApi.space();
      expect(large.dishes).toHaveLength(80);
      expect(large.meta.build_id).toBe("fixture-large");
    } finally {
      Object.defineProperty(globalThis, "location", { configurable: true, value: prev });
    }
  });

  it("mock explain always has fixture attributions", () => {
    const res = mockExplain(space, id, space.dishes[1].id);
    expect(Object.keys(res.attributions.a).length).toBeGreaterThan(0);
  });

  it("mock recipe neighbors change when the text changes", () => {
    const pasta = mockRecipe(space, { text: "spaghetti pecorino egg black pepper" });
    const mango = mockRecipe(space, { text: "mango sticky rice coconut milk" });
    expect(pasta.neighbors[0]?.dish_id).not.toBe(mango.neighbors[0]?.dish_id);
    expect(mango.neighbors.some((n) => n.dish_id === "mango_sticky_rice")).toBe(true);
  });
});
