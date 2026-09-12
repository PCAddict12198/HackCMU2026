export function partnerId(
  selectedId: string | null,
  twinHighlight: string | null,
  highlightIds: string[],
): string | null {
  return [twinHighlight, ...highlightIds].find((id): id is string => !!id && id !== selectedId) ?? null;
}
