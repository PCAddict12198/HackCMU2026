import type { Deltas, DimId, ErrorCode, ProvenanceSrc, ToolTrace } from "../../contract";

export const closerThan = (pct: number) => `Closer in taste than ${Math.round(pct)}% of dish pairs`;

export const prettyId = (id: string) => id.replaceAll("_", " ");

export function shiftFormula(dishId: string, deltas: Deltas): string {
  const terms = (Object.entries(deltas) as [DimId, number | undefined][])
    .filter((entry): entry is [DimId, number] => entry[1] != null && Math.abs(entry[1]) >= 0.05)
    .map(([dim, v]) => `${v < 0 ? "-" : "+"} ${Math.abs(v).toFixed(1)} e_${dim}`);
  return terms.length ? `target = z_${dishId} ${terms.join(" ")}` : `target = z_${dishId}`;
}

export function movedBits(moved: Record<string, number>): string {
  return Object.entries(moved)
    .filter(([, v]) => Math.abs(v) >= 0.01)
    .map(([dim, v]) => `${dim} ${v >= 0 ? "+" : ""}${v.toFixed(2)}`)
    .join(", ");
}

export const SRC_LABEL: Record<NonNullable<ProvenanceSrc>, string> = {
  usda: "USDA",
  scoville: "Scoville",
  literature: "literature",
  team: "team",
  grok_reviewed: "Grok reviewed",
  grok_draft: "Grok draft",
  seed_placeholder: "seed (placeholder)",
  fixture: "fixture",
};

export function formatToolStory(t: ToolTrace): string {
  const args = t.args ?? {};
  if (t.tool === "find_twins") return "Looked for flavor twins";
  if (t.tool === "explain_pair") return "Compared two dishes in TasteSpace";
  if (t.tool === "search_dishes" && typeof args.query === "string") return `Searched for “${args.query}”`;
  if (t.tool === "shift_taste") return "Moved your craving through TasteSpace";
  return "Used TasteSpace";
}

export function formatToolCall(t: ToolTrace): string {
  const args = t.args ?? {};
  if (t.tool === "find_twins" && typeof args.dish_id === "string") return `find_twins(${args.dish_id})`;
  if (t.tool === "explain_pair" && typeof args.a === "string" && typeof args.b === "string") {
    return `explain_pair(${args.a}, ${args.b})`;
  }
  if (t.tool === "search_dishes" && typeof args.query === "string") return `search_dishes(${args.query})`;
  if (t.tool === "shift_taste") {
    const id = typeof args.dish_id === "string" ? args.dish_id : "?";
    return `shift_taste(${id})`;
  }
  return `${t.tool}()`;
}

export function friendlyError(code: ErrorCode | "network"): { title: string; hint: string; retry: boolean } {
  switch (code) {
    case "validation_error":
      return { title: "That request was invalid", hint: "Check the selected dish or slider values.", retry: false };
    case "not_found":
      return { title: "Dish not in this space", hint: "Pick another star. This id is missing from the current build.", retry: false };
    case "not_ready":
      return { title: "Engine still building", hint: "The flavor space is not ready yet. Retry in a moment.", retry: true };
    case "grok_unavailable":
      return { title: "Ask is offline", hint: "Grok is not configured on the server. Other panels still work.", retry: false };
    case "grok_failed":
      return { title: "Grok failed that turn", hint: "The model call errored. Retry the same question.", retry: true };
    case "internal":
      return { title: "Something broke in the engine", hint: "Retry, or switch back to mock mode if this is a demo.", retry: true };
    case "network":
      return { title: "Cannot reach the API", hint: "Is `make api` running? Mock mode does not need it.", retry: true };
  }
}
