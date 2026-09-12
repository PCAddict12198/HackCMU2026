import { create } from "zustand";
import { api } from "../api/client";
import type { ChatMessage, Course, Deltas, DimId, DishFormat, HealthResponse, Panel, RecipeResponse, ShiftResponse, SpaceResponse, UiAction, Vec3 } from "../contract";
import { SAMPLE_RECIPE } from "../features/recipe/constants";
import { startDishId } from "../features/shared/demo";
import { initialUi, reduceUiActions, type UiSlice } from "./uiActions";

interface Store extends UiSlice {
  space: SpaceResponse | null;
  health: HealthResponse | null;
  loadError: unknown;
  shiftResult: ShiftResponse | null;
  recipeStar: RecipeResponse | null;
  recipeMapped: RecipeResponse | null;
  recipeText: string;
  recipeCourse: Course | "";
  recipeFormat: DishFormat | "";
  focus: Vec3 | null;
  homeTick: number;
  chat: ChatMessage[];
  placeRecipeTick: number;
  loadSeq: number;
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
  setRecipeMapped(r: RecipeResponse | null): void;
  setRecipeText(text: string): void;
  setRecipeCourse(course: Course | ""): void;
  setRecipeFormat(format: DishFormat | ""): void;
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
  recipeMapped: null,
  recipeText: SAMPLE_RECIPE,
  recipeCourse: "",
  recipeFormat: "",
  focus: null,
  homeTick: 0,
  chat: [],
  placeRecipeTick: 0,
  loadSeq: 0,

  async load() {
    const seq = get().loadSeq + 1;
    set({ loadSeq: seq });
    const [space, health] = await Promise.allSettled([api.space(), api.health()]);
    if (get().loadSeq !== seq) return;
    if (space.status === "rejected") return set({ loadError: space.reason });
    const ids = new Set(space.value.dishes.map((d) => d.id));
    const keep = get().selectedId && ids.has(get().selectedId!) ? get().selectedId : null;
    const first = keep ?? startDishId(ids) ?? space.value.dishes[0]?.id ?? null;
    set({
      space: space.value,
      health: health.status === "fulfilled" ? health.value : null,
      selectedId: first,
      focus: null,
      highlightIds: [],
      twinHighlight: null,
      shiftResult: null,
      loadError: null,
    });
  },
  select: (id) =>
    set((s) => ({
      selectedId: id,
      shiftDeltas: {},
      shiftResult: null,
      twinHighlight: null,
      highlightIds: id ? s.highlightIds : [],
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
  setRecipeMapped: (recipeMapped) => set({ recipeMapped }),
  setRecipeText: (recipeText) => set({ recipeText }),
  setRecipeCourse: (recipeCourse) => set({ recipeCourse }),
  setRecipeFormat: (recipeFormat) => set({ recipeFormat }),
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
