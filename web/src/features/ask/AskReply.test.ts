import { describe, expect, it } from "vitest";
import { flattenAskReply } from "./AskReply";

describe("AskReply", () => {
  it("strips markdown markers for a readable fallback", () => {
    expect(flattenAskReply("**Pho bo** is brothy\n- spicy\n## Next")).toContain("Pho bo is brothy");
    expect(flattenAskReply("- spicy")).toContain("• spicy");
  });
});
