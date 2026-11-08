// Temporary. Keeps screens that haven't been redesigned yet running on the new fonts
// and Studio colors, in the old token shape. Deleted together with src/components/*
// once no screen imports from there.
import { borders as newBorders, fonts as newFonts, palettes } from "./tokens";

const studio = palettes.dark;

export const colors = {
  bg: { canvas: studio.canvas, surface: studio.surface, raised: studio.raised },
  border: { subtle: studio.border, default: studio.border, strong: studio.borderStrong },
  text: {
    primary: studio.textPrimary,
    secondary: studio.textSecondary,
    tertiary: studio.textTertiary,
    disabled: studio.borderStrong,
    onAccent: studio.onInk,
  },
  accent: {
    base: studio.ink,
    hover: studio.ink,
    pressed: studio.textSecondary,
    subtle: studio.sunken,
    border: studio.borderStrong,
  },
  state: {
    recording: studio.signal,
    uploading: studio.textSecondary,
    success: studio.success,
    warning: studio.warning,
    danger: studio.danger,
  },
  destructive: { fill: studio.danger, pressed: studio.danger, text: studio.onInk },
  focus: studio.textSecondary,
} as const;

export const fonts = {
  ui: newFonts.sans,
  uiMedium: newFonts.sansMedium,
  uiSemibold: newFonts.sansSemibold,
  uiBold: newFonts.sansBold,
  mono: newFonts.mono,
  monoMedium: newFonts.monoMedium,
  urdu: newFonts.urdu,
  urduMedium: newFonts.urduMedium,
} as const;

export const type = {
  hero: { size: 40, lineHeight: 46, weight: "uiBold", tracking: -0.9 },
  display: { size: 32, lineHeight: 38, weight: "uiSemibold", tracking: -0.6 },
  title: { size: 24, lineHeight: 30, weight: "uiSemibold", tracking: -0.3 },
  heading: { size: 19, lineHeight: 26, weight: "uiMedium", tracking: -0.1 },
  body: { size: 15, lineHeight: 22, weight: "ui", tracking: 0 },
  bodyStrong: { size: 15, lineHeight: 22, weight: "uiMedium", tracking: 0 },
  label: { size: 13, lineHeight: 18, weight: "uiMedium", tracking: 0.1 },
  caption: { size: 12, lineHeight: 16, weight: "ui", tracking: 0.1 },
  mono: { size: 13, lineHeight: 18, weight: "mono", tracking: 0 },
  monoSmall: { size: 11, lineHeight: 16, weight: "mono", tracking: 0 },
  urdu: { size: 17, lineHeight: 36, weight: "urdu", tracking: 0 },
} as const;

export const space = {
  none: 0,
  hair: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  screen: 20,
  xl: 24,
  xxl: 32,
  section: 40,
  xxxl: 48,
  huge: 64,
} as const;

export const radii = { sm: 8, md: 12, lg: 16, xl: 24, pill: 999 } as const;

export const borders = { hairline: newBorders.thin, focus: newBorders.focus } as const;

export const touch = { min: 44 } as const;

export const elevation = {
  one: { backgroundColor: studio.surface, borderWidth: borders.hairline, borderColor: studio.border },
  two: {
    backgroundColor: studio.raised,
    borderWidth: borders.hairline,
    borderColor: studio.borderStrong,
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 24,
    elevation: 8,
  },
} as const;
