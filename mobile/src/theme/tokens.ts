// Design tokens. Never hardcode a hex color, font name, size, or spacing value
// outside this file — every screen and component imports from here so the
// whole app can be restyled in one place. See docs/adr/0005-ibm-plex-typeface.md
// for why this is IBM Plex, not the General Sans in the original design system doc.

export const colors = {
  bg: {
    canvas: "#0D1117", // level 0 — screen background
    surface: "#161B22", // level 1 — cards, inputs, list rows
    raised: "#1C2128", // level 2 — modals, dropdowns, sheets
  },
  border: {
    subtle: "#21262D",
    default: "#30363D",
    strong: "#3D444D",
  },
  text: {
    primary: "#E6EDF3",
    secondary: "#8B949E",
    tertiary: "#6E7681",
    disabled: "#484F58",
    onAccent: "#04120F", // text sitting on a solid accent-teal fill
  },
  accent: {
    base: "#14B8A6",
    hover: "#2DD4BF",
    pressed: "#0D9488",
    subtle: "rgba(20, 184, 166, 0.12)", // tinted fill, e.g. selected row
    border: "rgba(20, 184, 166, 0.32)",
  },
  // Recording (red) and danger (red) share a hue on purpose — they're told
  // apart by form, never by shade: recording is always a filled dot + label,
  // danger is always a destructive button or an error border. Don't add a
  // second red to "fix" this; add the missing dot or border instead.
  state: {
    recording: "#F85149",
    uploading: "#58A6FF",
    success: "#3FB950",
    warning: "#D29922",
    danger: "#DA3633",
  },
  // Focus obeys the same rule as recording: teal means "this is what's
  // active right now," and a focused field is exactly that.
  focus: "rgba(20, 184, 166, 0.55)",
} as const;

export const fonts = {
  ui: "IBMPlexSans_400Regular",
  uiMedium: "IBMPlexSans_500Medium",
  uiSemibold: "IBMPlexSans_600SemiBold",
  mono: "IBMPlexMono_400Regular",
  // Nastaliq's calligraphic ascenders/descenders are tall relative to its
  // em box — Latin line-height ratios clip them on Android. Always pair
  // this font with type.urdu's lineHeight ratio, not a UI type step.
  urdu: "NotoNastaliqUrdu_400Regular",
} as const;

// Named steps, not raw sizes — a screen picks `type.body`, never a number.
// {size, lineHeight} in px, weight names a fonts.* key above.
export const type = {
  display: { size: 32, lineHeight: 38, weight: "uiSemibold" },
  title: { size: 24, lineHeight: 30, weight: "uiSemibold" },
  heading: { size: 19, lineHeight: 26, weight: "uiMedium" },
  body: { size: 15, lineHeight: 22, weight: "ui" },
  bodyStrong: { size: 15, lineHeight: 22, weight: "uiMedium" },
  label: { size: 13, lineHeight: 18, weight: "uiMedium" },
  caption: { size: 12, lineHeight: 16, weight: "ui" },
  mono: { size: 13, lineHeight: 18, weight: "mono" },
  monoSmall: { size: 11, lineHeight: 16, weight: "mono" },
  // Nastaliq needs ~2.1x its size in line-height or ascenders clip — far
  // more than any Latin step above. Kept separate rather than folding into
  // `body`, since a mixed-script line still needs the Latin metric for its
  // Latin half (see Urdu.tsx, which applies this only to the Urdu run).
  urdu: { size: 17, lineHeight: 36, weight: "urdu" },
} as const;

// Base-4 scale. Reach for these, not arbitrary padding numbers.
export const space = {
  none: 0,
  hair: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
  huge: 64,
} as const;

export const radii = {
  sm: 6,
  md: 10,
  lg: 14,
  pill: 999,
} as const;

export const borders = {
  hairline: 1,
  focus: 2,
} as const;

// Exactly two elevation levels, per the design direction — a third means
// the layout has a hierarchy problem, not a missing token.
export const elevation = {
  one: {
    backgroundColor: colors.bg.surface,
    borderWidth: borders.hairline,
    borderColor: colors.border.subtle,
  },
  two: {
    backgroundColor: colors.bg.raised,
    borderWidth: borders.hairline,
    borderColor: colors.border.default,
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.32,
    shadowRadius: 24,
    elevation: 8, // Android shadow fallback
  },
} as const;

export const motion = {
  duration: { fast: 120, base: 180, slow: 280 },
} as const;

// Apple/Android's shared accessible touch-target floor. Every interactive
// component measures against this, not just the ones that look small.
export const touch = {
  min: 44,
} as const;
