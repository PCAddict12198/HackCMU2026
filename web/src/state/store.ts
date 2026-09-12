// App state (zustand). Panels fetch their own data; the store holds what several features share.
import { create } from "zustand";
import { api, errorMessage } from "../api/client";
import type { ChatMessage, DimId, HealthResponse, Panel, ShiftResponse, SpaceResponse, UiAction } from "../contract";
import { initialUi, reduceUiActions, type UiSlice } from "./uiActions";

interface Store extends UiSlice {
  space: SpaceResponse | null;
  health: HealthResponse | null;
  loadError: string | null;
  shiftResult: ShiftResponse | null;
  chat: ChatMessage[];
  load(): Promise<void>;
  select(id: string | null): void;
  setPanel(p: Panel): void;
  setShiftDelta(dim: DimId, v: number): void;
  resetShift(): void;
  setShiftResult(r: ShiftResponse | null): void;
  setExplainPair(a: string, b: string): void;
  setHighlights(ids: string[]): void;
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

export const useStore = create<Store>()((set, get) => ({
  ...initialUi,
  space: null,
  health: null,
  loadError: null,
  shiftResult: null,
  chat: [],

  async load() {
    const [space, health] = await Promise.allSettled([api.space(), api.health()]);
    if (space.status === "rejected") return set({ loadError: errorMessage(space.reason) });
    set({
      space: space.value,
      health: health.status === "fulfilled" ? health.value : null,
      selectedId: get().selectedId ?? space.value.dishes[0]?.id ?? null,
      loadError: null,
    });
  },
  select: (id) => set({ selectedId: id, shiftDeltas: {}, shiftResult: null, twinHighlight: null }),
  setPanel: (panel) => set({ panel }),
  setShiftDelta: (dim, v) => set((s) => ({ shiftDeltas: { ...s.shiftDeltas, [dim]: v } })),
  resetShift: () => set({ shiftDeltas: {}, shiftResult: null }),
  setShiftResult: (shiftResult) => set({ shiftResult }),
  setExplainPair: (a, b) => set({ explainPair: [a, b], panel: "explain" }),
  setHighlights: (highlightIds) => set({ highlightIds }),
  pushChat: (m) => set((s) => ({ chat: [...s.chat, m] })),
  applyUiActions(actions) {
    const known = new Set(get().space?.dishes.map((d) => d.id) ?? []);
    set(reduceUiActions(uiOf(get()), actions, known));
  },
}));

export const useDish = (id: string | null | undefined) =>
  useStore((s) => (id ? s.space?.dishes.find((d) => d.id === id) ?? null : null));
