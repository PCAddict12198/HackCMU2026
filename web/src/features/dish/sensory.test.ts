import { describe, expect, it } from "vitest";
import { matchDishes, pickByDim, topDimIds } from "./sensory";
import type { DishPoint } from "../../contract";

const dish = (id: string, vector: Record<string, number>, name = id): DishPoint =>
  ({
    id,
    name,
    cuisine: "japanese",
    course: "savory",
    format: "noodles",
    tier: "core",
    confidence: "reviewed",
    blurb: `${name} bowl`,
    xyz: [0, 0, 0],
    vector,
  }) as DishPoint;

describe("sensory helpers", () => {
  it("picks the strongest dimensions without inventing values", () => {
    expect(topDimIds({ rich: 0.9, umami: 0.8, brothy: 0.7, sweet: 0.1 }, 3)).toEqual(["rich", "umami", "brothy"]);
  });

  it("picks the dish with the highest actual dim value", () => {
    const a = dish("a", { spicy: 0.2 });
    const b = dish("b", { spicy: 0.9 });
    expect(pickByDim([a, b], "spicy")?.id).toBe("b");
  });

  it("matches dishes by name from the catalog", () => {
    const ramen = dish("tonkotsu_ramen", { rich: 1 }, "Tonkotsu ramen");
    const pho = dish("pho_bo", { brothy: 1 }, "Pho bo");
    expect(matchDishes("ramen", [ramen, pho]).map((d) => d.id)).toEqual(["tonkotsu_ramen"]);
  });
});
