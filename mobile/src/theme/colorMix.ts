// Turns a #RRGGBB token into the same color at a given opacity. Gradients need this:
// fading to "transparent" goes through gray, fading to the same color at 0 does not.
export function withAlpha(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  const red = parseInt(value.slice(0, 2), 16);
  const green = parseInt(value.slice(2, 4), 16);
  const blue = parseInt(value.slice(4, 6), 16);

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
