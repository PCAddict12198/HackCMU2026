import { describe, expect, it } from "vitest";
import { closerThan, formatToolCall, friendlyError, movedBits, shiftFormula } from "./copy";

describe("copy", () => {
  it("never says percent similar", () => {
    expect(closerThan(93.4)).toBe("Closer in taste than 93% of dish pairs");
    expect(closerThan(93.4).toLowerCase()).not.toContain("similar");
  });

  it("builds the shift HOW formula from deltas", () => {
    expect(shiftFormula("tonkotsu_ramen", { rich: -0.8, sour: 1.2 })).toBe(
      "target = z_tonkotsu_ramen - 0.8 e_rich + 1.2 e_sour",
    );
  });

  it("formats moved dims", () => {
    expect(movedBits({ sour: 0.31, rich: -0.8 })).toBe("sour +0.31, rich -0.80");
  });

  it("formats grok tool traces", () => {
    expect(
      formatToolCall({
        call_id: "c0",
        tool: "find_twins",
        args: { dish_id: "tonkotsu_ramen", k: 3 },
        ok: true,
        result: {},
        error: null,
      }),
    ).toBe("find_twins(tonkotsu_ramen)");
  });

  it("covers every error code", () => {
    const codes = [
      "validation_error",
      "not_found",
      "not_ready",
      "grok_unavailable",
      "grok_failed",
      "internal",
      "network",
    ] as const;
    for (const c of codes) expect(friendlyError(c).title.length).toBeGreaterThan(0);
  });
});
