import { describe, expect, it } from "vitest";
import type { UiAction } from "../contract";
import { fixtures } from "../mocks/fixtures";
import { initialUi, reduceUiAction, reduceUiActions } from "./uiActions";

const known = new Set(["a", "b", "c"]);

describe("uiActions reducer", () => {
  it("handles every action type", () => {
    let s = reduceUiAction(initialUi, { type: "select_dish", dish_id: "a" }, known);
    expect(s.selectedId).toBe("a");
    s = reduceUiAction(s, { type: "show_twins", dish_id: "b", highlight_dish_id: "c" }, known);
    expect([s.selectedId, s.twinHighlight]).toEqual(["b", "c"]);
    s = reduceUiAction(s, { type: "set_shift", dish_id: "a", deltas: { rich: -0.8, sour: 1.2 } }, known);
    expect(s.shiftDeltas).toEqual({ rich: -0.8, sour: 1.2 });
    s = reduceUiAction(s, { type: "explain_pair", a: "a", b: "c" }, known);
    expect(s.explainPair).toEqual(["a", "c"]);
    s = reduceUiAction(s, { type: "open_panel", panel: "shift" }, known);
    expect(s.panel).toBe("shift");
    s = reduceUiAction(s, { type: "highlight_dishes", dish_ids: ["a", "zzz"] }, known);
    expect(s.highlightIds).toEqual(["a"]);
  });

  it("ignores unknown dish ids and unknown action types", () => {
    expect(reduceUiAction(initialUi, { type: "select_dish", dish_id: "nope" }, known)).toBe(initialUi);
    const future = { type: "teleport", to: "a" } as unknown as UiAction;
    expect(reduceUiAction(initialUi, future, known)).toBe(initialUi);
  });

  it("applies the canonical ask fixture", () => {
    const ids = new Set(fixtures.space.dishes.map((d) => d.id));
    const s = reduceUiActions(initialUi, fixtures.ask.ui_actions, ids);
    expect(s.selectedId).not.toBeNull();
  });
});
