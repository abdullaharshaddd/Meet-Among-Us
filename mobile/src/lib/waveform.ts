// A fixed, believable-looking audio shape. Not random, so the same screen always draws the same
// strip, and people who asked for less motion see a real-looking shape instead of a blank bar.
export function staticWaveform(count: number): number[] {
  return Array.from({ length: count }, (_, index) => {
    const wave = Math.abs(Math.sin(index * 0.35)) * 0.5 + Math.abs(Math.sin(index * 0.9 + 1)) * 0.3;

    return Math.min(1, 0.15 + wave);
  });
}
