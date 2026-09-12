/** Saturated food colors so nodes read on ivory, not muddy pastels. */
export const CUISINE_COLORS: Record<string, string> = {
  japanese: "#E24B3A",
  chinese: "#F08C14",
  korean: "#E0356F",
  thai: "#2DB85A",
  vietnamese: "#12B3A0",
  indian: "#F0B400",
  levantine: "#7CB81A",
  italian: "#E23A28",
  french: "#C44A8A",
  mexican: "#FF6E14",
};

export const cuisineColor = (c: string) => CUISINE_COLORS[c] ?? "#C4A574";

export const CUISINE_PLATES: Record<string, [string, string, string]> = {
  japanese: ["#E7C9A8", "#C45C4A", "#4A3F36"],
  chinese: ["#E8B56A", "#C45C3E", "#6B2A1A"],
  korean: ["#E8A0B0", "#B84A6A", "#6A2038"],
  thai: ["#C5D9A4", "#5A9A62", "#E07A32"],
  vietnamese: ["#B7D9C8", "#2F8F82", "#C45C4A"],
  indian: ["#F0C35A", "#D4782A", "#8B3A1A"],
  levantine: ["#D4E0A8", "#7A9A45", "#C45C3E"],
  italian: ["#E8C4B0", "#C45C3E", "#6F8F5A"],
  french: ["#E8D4C4", "#8B5E73", "#C4A574"],
  mexican: ["#F0C07A", "#E07A32", "#5A9A62"],
};

export const plateColors = (cuisine: string): [string, string, string] =>
  CUISINE_PLATES[cuisine] ?? ["#E8DCC8", "#A39886", "#6F8F5A"];
