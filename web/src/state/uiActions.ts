// The ONE place UI actions from /api/ask change the app. Pure + tested. Unknown dish ids and unknown
// action types are ignored (actions carry ids only; numbers are always refetched from the engine).
import type { Deltas, Panel, UiAction } from "../contract";

export interface UiSlice {
  selectedId: string | null;
  panel: Panel;
  twinHighlight: string | null;
  shiftDeltas: Deltas;
  explainPair: [string, string] | null;
  highlightIds: string[];
}

export const initialUi: UiSlice = {
  selectedId: null,
  panel: "twins",
  twinHighlight: null,
  shiftDeltas: {},
  explainPair: null,
  highlightIds: [],
};

export function reduceUiAction(s: UiSlice, a: UiAction, known: Set<string>): UiSlice {
  const ok = (id: string | null | undefined): id is string => !!id && known.has(id);
  switch (a.type) {
    case "select_dish":
      return ok(a.dish_id) ? { ...s, selectedId: a.dish_id } : s;
    case "show_twins":
      return ok(a.dish_id)
        ? { ...s, selectedId: a.dish_id, twinHighlight: ok(a.highlight_dish_id) ? a.highlight_dish_id : null }
        : s;
    case "set_shift":
      return ok(a.dish_id) ? { ...s, selectedId: a.dish_id, shiftDeltas: { ...(a.deltas as Deltas) } } : s;
    case "explain_pair":
      return ok(a.a) && ok(a.b) ? { ...s, explainPair: [a.a, a.b] } : s;
    case "open_panel":
      return { ...s, panel: a.panel };
    case "highlight_dishes":
      return { ...s, highlightIds: a.dish_ids.filter((id) => known.has(id)) };
    default:
      return s; // forward compatible: ignore action types this build doesn't know
  }
}

export const reduceUiActions = (s: UiSlice, actions: UiAction[], known: Set<string>): UiSlice =>
  actions.reduce((acc, a) => reduceUiAction(acc, a, known), s);
