export const CUISINE_COLORS: Record<string, string> = {
  japanese: "#ff6b6b",
  chinese: "#f59f00",
  korean: "#e64980",
  thai: "#51cf66",
  vietnamese: "#20c997",
  indian: "#fab005",
  levantine: "#94d82d",
  italian: "#4dabf7",
  french: "#9775fa",
  mexican: "#ff922b",
};

export const cuisineColor = (c: string) => CUISINE_COLORS[c] ?? "#ced4da";
