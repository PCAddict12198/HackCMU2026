export const CUISINE_COLORS: Record<string, string> = {
  japanese: "#e07a78",
  chinese: "#e0a15a",
  korean: "#d46a92",
  thai: "#6cbc7a",
  vietnamese: "#4db8a4",
  indian: "#d9ae4a",
  levantine: "#9bc45a",
  italian: "#6aa8e0",
  french: "#9b86d9",
  mexican: "#e08a4a",
};

export const cuisineColor = (c: string) => CUISINE_COLORS[c] ?? "#c8c0b6";
