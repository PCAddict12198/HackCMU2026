import { describe, expect, it } from "vitest";
import { partnerId } from "./demo";

describe("demo walkthrough", () => {
  it("picks a twin that is not the selected dish", () => {
    expect(partnerId("a", "b", ["b", "c"])).toBe("b");
    expect(partnerId("a", null, ["a", "c"])).toBe("c");
    expect(partnerId("a", null, ["a"])).toBeNull();
  });
});
