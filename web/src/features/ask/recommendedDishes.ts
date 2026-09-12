import type { AskResponse } from "../../contract";

function addId(ids: string[], known: Set<string>, id?: string | null) {
  if (id && known.has(id) && !ids.includes(id)) ids.push(id);
}

function idsFromToolResult(result: unknown, known: Set<string>, ids: string[]) {
  if (!result || typeof result !== "object") return;
  const r = result as Record<string, unknown>;
  addId(ids, known, typeof r.source_id === "string" ? r.source_id : null);
  for (const key of ["twins", "results", "neighbors"] as const) {
    const list = r[key];
    if (!Array.isArray(list)) continue;
    for (const row of list) {
      if (row && typeof row === "object" && "dish_id" in row && typeof row.dish_id === "string") {
        addId(ids, known, row.dish_id);
      }
    }
  }
}

/** Dish ids Grok actually recommended this turn (engine ids only). */
export function recommendedDishIds(res: AskResponse, known: Set<string>): string[] {
  const ids: string[] = [];
  const highlights = res.ui_actions.filter((a) => a.type === "highlight_dishes");
  const last = highlights.at(-1);
  if (last && last.type === "highlight_dishes") {
    for (const id of last.dish_ids) addId(ids, known, id);
  }
  for (const a of res.ui_actions) {
    if (a.type === "show_twins") addId(ids, known, a.highlight_dish_id);
  }
  if (!ids.length) {
    for (const a of res.ui_actions) {
      if (a.type === "explain_pair") {
        addId(ids, known, a.a);
        addId(ids, known, a.b);
      }
      if (a.type === "select_dish" || a.type === "set_shift" || a.type === "show_twins") addId(ids, known, a.dish_id);
    }
  }
  if (!ids.length) {
    for (const t of res.tool_trace) {
      if (t.ok) idsFromToolResult(t.result, known, ids);
    }
  }
  return ids.slice(0, 6);
}
