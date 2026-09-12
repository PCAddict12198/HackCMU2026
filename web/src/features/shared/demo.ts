/** Demo walkthrough ids from docs/demo/demo_script.md (real core build). */
export const DEMO_SOURCE_ID = "pho_bo";
export const DEMO_TWIN_ID = "pozole_rojo";

export function partnerId(
  selectedId: string | null,
  twinHighlight: string | null,
  highlightIds: string[],
): string | null {
  return [twinHighlight, ...highlightIds].find((id): id is string => !!id && id !== selectedId) ?? null;
}

export function startDishId(ids: Set<string>): string | null {
  for (const id of [DEMO_SOURCE_ID, "tonkotsu_ramen"]) if (ids.has(id)) return id;
  return null;
}

export function explainPairForDemo(
  ids: Set<string>,
  selectedId: string | null,
  twinHighlight: string | null,
  highlightIds: string[],
): [string, string] | null {
  if (ids.has(DEMO_SOURCE_ID) && ids.has(DEMO_TWIN_ID)) return [DEMO_SOURCE_ID, DEMO_TWIN_ID];
  const b = partnerId(selectedId, twinHighlight, highlightIds);
  if (selectedId && b) return [selectedId, b];
  return null;
}
