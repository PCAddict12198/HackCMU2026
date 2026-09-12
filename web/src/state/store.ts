import { create } from "zustand";
import { api } from "../api/client";
import type { ChatMessage, Deltas, DimId, HealthResponse, Panel, RecipeResponse, ShiftResponse, SpaceResponse, UiAction, Vec3 } from "../contract";
import { initialUi, reduceUiActions, type UiSlice } from "./uiActions";

interface Store extends UiSlice {
  space: SpaceResponse | null;
  health: HealthResponse | null;
  loadError: unknown;
  shiftResult: ShiftResponse | null;
  recipeStar: RecipeResponse | null;
  focus: Vec3 | null;
  homeTick: number;
  chat: ChatMessage[];
  placeRecipeTick: number;
  load(): Promise<void>;
  select(id: string | null): void;
  setPanel(p: Panel): void;
  setShiftDelta(dim: DimId, v: number): void;
  setShiftDeltas(d: Deltas): void;
  resetShift(): void;
  setShiftResult(r: ShiftResponse | null): void;
  setExplainPair(a: string, b: string): void;
  setHighlights(ids: string[]): void;
  setTwinHighlight(id: string | null): void;
  focusDish(id: string): void;
  setRecipeStar(r: RecipeResponse | null): void;
  resetView(): void;
  bumpPlaceRecipe(): void;
  pushChat(m: ChatMessage): void;
  applyUiActions(actions: UiAction[]): void;
}

const uiOf = (s: Store): UiSlice => ({
  selectedId: s.selectedId,
  panel: s.panel,
  twinHighlight: s.twinHighlight,
  shiftDeltas: s.shiftDeltas,
  explainPair: s.explainPair,
  highlightIds: s.highlightIds,
});

const xyzOf = (s: Store, id: string | null): Vec3 | null =>
  (id && s.space?.dishes.find((d) => d.id === id)?.xyz) || null;

export const useStore = create<Store>()((set, get) => ({
  ...initialUi,
  space: null,
  health: null,
  loadError: null,
  shiftResult: null,
  recipeStar: null,
  focus: null,
  homeTick: 0,
  chat: [],
  placeRecipeTick: 0,

  async load() {
    const [space, health] = await Promise.allSettled([api.space(), api.health()]);
    if (space.status === "rejected") return set({ loadError: space.reason });
    const ids = new Set(space.value.dishes.map((d) => d.id));
    const keep = get().selectedId && ids.has(get().selectedId!) ? get().selectedId : null;
    const first = keep ?? (ids.has("tonkotsu_ramen") ? "tonkotsu_ramen" : space.value.dishes[0]?.id) ?? null;
    set({
      space: space.value,
      health: health.status === "fulfilled" ? health.value : null,
      selectedId: first,
      focus: space.value.dishes.find((d) => d.id === first)?.xyz ?? null,
      loadError: null,
    });
  },
  select: (id) =>
    set((s) => ({
      selectedId: id,
      shiftDeltas: {},
      shiftResult: null,
      twinHighlight: null,
      focus: xyzOf(s, id),
    })),
  setPanel: (panel) => set({ panel }),
  setShiftDelta: (dim, v) => set((s) => ({ shiftDeltas: { ...s.shiftDeltas, [dim]: v } })),
  setShiftDeltas: (shiftDeltas) => set({ shiftDeltas }),
  resetShift: () => set({ shiftDeltas: {}, shiftResult: null }),
  setShiftResult: (shiftResult) => set({ shiftResult }),
  setExplainPair: (a, b) => set({ explainPair: [a, b], panel: "explain" }),
  setHighlights: (highlightIds) => set({ highlightIds }),
  setTwinHighlight: (twinHighlight) => set({ twinHighlight }),
  focusDish: (id) =>
    set((s) => ({
      twinHighlight: id,
      focus: xyzOf(s, id) ?? s.focus,
    })),
  setRecipeStar: (recipeStar) =>
    set({
      recipeStar,
      focus: recipeStar?.xyz ?? null,
      highlightIds: recipeStar?.neighbors.map((n) => n.dish_id) ?? [],
    }),
  resetView: () => set((s) => ({ homeTick: s.homeTick + 1, focus: null })),
  bumpPlaceRecipe: () => set((s) => ({ panel: "recipe", placeRecipeTick: s.placeRecipeTick + 1 })),
  pushChat: (m) => set((s) => ({ chat: [...s.chat, m] })),
  applyUiActions(actions) {
    const known = new Set(get().space?.dishes.map((d) => d.id) ?? []);
    const next = reduceUiActions(uiOf(get()), actions, known);
    set({ ...next, focus: xyzOf({ ...get(), ...next }, next.selectedId) ?? get().focus });
  },
}));

export const useDish = (id: string | null | undefined) =>
  useStore((s) => (id ? s.space?.dishes.find((d) => d.id === id) ?? null : null));
