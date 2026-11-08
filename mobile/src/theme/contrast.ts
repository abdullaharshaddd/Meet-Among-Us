function luminance(hex: string): number {
  const channels = [1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16) / 255);

  const [red, green, blue] = channels.map((value) =>
    value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4,
  );

  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

// WCAG contrast ratio between two #RRGGBB colors. Returns null for rgba() values.
export function contrastRatio(foreground: string, background: string): number | null {
  if (!foreground.startsWith("#") || !background.startsWith("#")) return null;

  const [lighter, darker] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);

  return (lighter + 0.05) / (darker + 0.05);
}
