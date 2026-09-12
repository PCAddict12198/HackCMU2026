import { describe, expect, it } from "vitest";
import { fixtures } from "../../mocks/fixtures";
import { recommendedDishIds } from "./recommendedDishes";

describe("recommendedDishIds", () => {
  const known = new Set(["kimchi_jjigae", "tom_yum_goong", "pho_bo", "chana_masala", "tabbouleh", "tonkotsu_ramen"]);

  it("uses the last highlight_dishes list from the ask fixture", () => {
    const ids = recommendedDishIds(fixtures.ask, known);
    expect(ids).toEqual(["kimchi_jjigae", "tom_yum_goong", "pho_bo", "chana_masala", "tabbouleh"]);
  });

  it("ignores unknown ids", () => {
    expect(recommendedDishIds(fixtures.ask, new Set(["pho_bo"]))).toEqual(["pho_bo"]);
  });
});
