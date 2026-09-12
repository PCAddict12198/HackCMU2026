import { describe, expect, it } from "vitest";
import { DEMO_SOURCE_ID, DEMO_TWIN_ID, explainPairForDemo, partnerId, startDishId } from "./demo";

describe("demo walkthrough", () => {
  it("picks a twin that is not the selected dish", () => {
    expect(partnerId("a", "b", ["b", "c"])).toBe("b");
    expect(partnerId("a", null, ["a", "c"])).toBe("c");
    expect(partnerId("a", null, ["a"])).toBeNull();
  });

  it("starts on pho_bo when the catalog has it", () => {
    expect(startDishId(new Set([DEMO_SOURCE_ID, "tonkotsu_ramen"]))).toBe(DEMO_SOURCE_ID);
    expect(startDishId(new Set(["tonkotsu_ramen"]))).toBe("tonkotsu_ramen");
    expect(startDishId(new Set(["fx_000"]))).toBeNull();
  });

  it("explains pho vs pozole when both exist, else the loaded twin", () => {
    expect(explainPairForDemo(new Set([DEMO_SOURCE_ID, DEMO_TWIN_ID]), "x", null, ["y"])).toEqual([
      DEMO_SOURCE_ID,
      DEMO_TWIN_ID,
    ]);
    expect(explainPairForDemo(new Set([DEMO_SOURCE_ID]), DEMO_SOURCE_ID, null, ["tom_yum_goong"])).toEqual([
      DEMO_SOURCE_ID,
      "tom_yum_goong",
    ]);
  });
});
