import { StyleSheet, type TextStyle } from "react-native";
import { Easing } from "react-native-reanimated";

// "Field Recorder" tokens, see docs/adr/0024-field-recorder-visual-identity.md.
// Every color, size, radius, spacing value, duration and font in the app comes from this file.

export type Scheme = "light" | "dark";

export interface Palette {
  canvas: string;
  surface: string;
  raised: string;
  sunken: string;
  border: string;
  borderStrong: string;
  // Edges of things you can press or tick: secondary button outlines, checkbox borders.
  // At least 3:1 against canvas and surface in both themes. Everything else uses border or borderStrong.
  borderControl: string;
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  ink: string;
  onInk: string;
  // Orange. Means recording or live, and nothing else.
  signal: string;
  onSignal: string;
  signalText: string;
  signalWash: string;
  success: string;
  warning: string;
  danger: string;
  focusRing: string;
  scrim: string;
}

// Paper
const light: Palette = {
  canvas: "#F3F1EC",
  surface: "#FBFAF7",
  raised: "#FFFFFF",
  sunken: "#E9E6DF",
  border: "#D9D5CC",
  borderStrong: "#B9B4A8",
  borderControl: "#878274",
  textPrimary: "#16150F",
  textSecondary: "#57534A",
  textTertiary: "#6E695F",
  ink: "#16150F",
  onInk: "#F3F1EC",
  signal: "#FF4F00",
  onSignal: "#16150F",
  signalText: "#C23A00",
  signalWash: "#FFE6DA",
  success: "#1F7A3A",
  warning: "#8A5A00",
  danger: "#B42318",
  focusRing: "#16150F",
  scrim: "rgba(22, 21, 15, 0.40)",
};

// Studio
const dark: Palette = {
  canvas: "#0E0D0B",
  surface: "#171613",
  raised: "#211F1B",
  sunken: "#080706",
  border: "#2E2B25",
  borderStrong: "#48443B",
  borderControl: "#6F6A5F",
  textPrimary: "#F2EFE8",
  textSecondary: "#B3AEA2",
  textTertiary: "#8C877B",
  ink: "#F2EFE8",
  onInk: "#0E0D0B",
  signal: "#FF5A1A",
  onSignal: "#0E0D0B",
  signalText: "#FF5A1A",
  signalWash: "#2A140A",
  success: "#5BC97A",
  warning: "#E8B04A",
  danger: "#FF7A8A",
  focusRing: "#F2EFE8",
  scrim: "rgba(0, 0, 0, 0.60)",
};

export const palettes: Record<Scheme, Palette> = { light, dark };

export const fonts = {
  serif: "InstrumentSerif_400Regular",
  serifItalic: "InstrumentSerif_400Regular_Italic",
  sans: "InstrumentSans_400Regular",
  sansMedium: "InstrumentSans_500Medium",
  sansSemibold: "InstrumentSans_600SemiBold",
  sansBold: "InstrumentSans_700Bold",
  mono: "GeistMono_400Regular",
  monoMedium: "GeistMono_500Medium",
  urdu: "NotoNastaliqUrdu_400Regular",
  urduMedium: "NotoNastaliqUrdu_500Medium",
} as const;

const tabular: TextStyle["fontVariant"] = ["tabular-nums"];

// Names are the spec's dotted names in camelCase: display.xl is displayXl.
// Instrument Serif is only for 24 pt and up, never for buttons or labels.
// Urdu steps never go in a fixed-height container: Nastaliq with a line height and
// a fixed height leaks memory on iOS.
export const type = {
  displayXl: { fontFamily: fonts.serif, fontSize: 44, lineHeight: 46, letterSpacing: -0.6 },
  displayLg: { fontFamily: fonts.serif, fontSize: 34, lineHeight: 38, letterSpacing: -0.4 },
  displayMd: { fontFamily: fonts.serif, fontSize: 28, lineHeight: 32, letterSpacing: -0.2 },
  displayItalic: { fontFamily: fonts.serifItalic, fontSize: 28, lineHeight: 32, letterSpacing: -0.2 },
  title: { fontFamily: fonts.sansSemibold, fontSize: 20, lineHeight: 26, letterSpacing: -0.2 },
  headline: { fontFamily: fonts.sansSemibold, fontSize: 17, lineHeight: 22, letterSpacing: -0.1 },
  body: { fontFamily: fonts.sans, fontSize: 16, lineHeight: 24, letterSpacing: 0 },
  bodyStrong: { fontFamily: fonts.sansMedium, fontSize: 16, lineHeight: 24, letterSpacing: 0 },
  callout: { fontFamily: fonts.sans, fontSize: 15, lineHeight: 22, letterSpacing: 0 },
  subhead: { fontFamily: fonts.sansMedium, fontSize: 14, lineHeight: 20, letterSpacing: 0 },
  button: { fontFamily: fonts.sansSemibold, fontSize: 16, lineHeight: 20, letterSpacing: 0.1 },
  caption: { fontFamily: fonts.sansMedium, fontSize: 12, lineHeight: 16, letterSpacing: 0.1 },
  label: {
    fontFamily: fonts.monoMedium,
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 0.9,
    textTransform: "uppercase",
  },
  mono: { fontFamily: fonts.mono, fontSize: 13, lineHeight: 18, letterSpacing: 0, fontVariant: tabular },
  codeInput: { fontFamily: fonts.mono, fontSize: 32, lineHeight: 40, letterSpacing: 2, fontVariant: tabular },
  timer: { fontFamily: fonts.mono, fontSize: 56, lineHeight: 60, letterSpacing: -1.5, fontVariant: tabular },
  urduBody: { fontFamily: fonts.urdu, fontSize: 16, lineHeight: 34, letterSpacing: 0, includeFontPadding: false },
  urduTitle: { fontFamily: fonts.urduMedium, fontSize: 20, lineHeight: 42, letterSpacing: 0, includeFontPadding: false },
  urduCaption: { fontFamily: fonts.urdu, fontSize: 13, lineHeight: 28, letterSpacing: 0, includeFontPadding: false },
} satisfies Record<string, TextStyle>;

export type TypeStep = keyof typeof type;

export const space = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  "2xl": 24,
  "3xl": 32,
  "4xl": 40,
  "5xl": 56,
  "6xl": 72,
} as const;

export const layout = {
  screenGutter: 20,
  cardGap: 12,
  sectionGap: 32,
} as const;

export const radii = {
  xs: 4, // badges
  sm: 6, // chips
  md: 10, // cards, inputs
  lg: 14, // buttons, composer
  xl: 22, // sheet top corners
  pill: 999,
} as const;

export const borders = {
  hairline: StyleSheet.hairlineWidth,
  thin: 1,
  focus: 2,
} as const;

// Cards are flat with a hairline. Only things that float above the page cast a shadow.
export const floating = {
  light: { shadowColor: "#000000", shadowOpacity: 0.1, shadowRadius: 24, shadowOffset: { width: 0, height: 8 }, elevation: 8 },
  dark: { shadowColor: "#000000", shadowOpacity: 0.4, shadowRadius: 24, shadowOffset: { width: 0, height: 8 }, elevation: 8 },
} as const;

export const sizes = {
  hitMin: 44,
  dockHeight: 56,
  inputHeight: 52,
  segmentedHeight: 40,
  chipHeight: 36,
  tabBarHeight: 64, // plus the bottom safe-area inset
  recordButton: 72,
  stopButton: 88,
  dockSecondary: 56,
  avatarSm: 24,
  avatarMd: 40,
  buttonMd: 48,
  buttonSm: 40, // drawn at 40 but given a 44 hit area with hitSlop
  loadingDot: 6,
  speakerDot: 8,
  meterHeightEnroll: 96,
  meterHeightLive: 160,
  icon: { sm: 16, md: 20, lg: 24 },
  startPillWidth: 184,
  chipCitation: 32,
  tabIndicatorWidth: 16,
  tabIndicatorHeight: 2,
  grabHandleWidth: 36,
  grabHandleHeight: 4,
  progressRing: 3,
  progressRingGap: 8,
  meterBar: 3,
  meterGap: 2,
  checkbox: 22,
  swipeAction: 88,
  screenMaxWidth: 430,
  avatarLg: 64,
  headerBar: 52,
  pillHeight: 56,
  skeletonCard: 112,
} as const;

// Ratios of the window, for things that scale with the screen.
export const ratios = {
  sheetMaxHeight: 0.85,
  bubbleMaxWidth: 0.82,
  peakLevel: 0.95, // -3 dBFS on the meter's -60..0 dB scale: (-3 + 60) / 60
} as const;

export const opacity = {
  dim: 0.3, // the resting state of a pulsing dot
  muted: 0.5, // a disabled field
} as const;

export const motion = {
  duration: { instant: 90, fast: 140, base: 220, slow: 340, meterFrame: 50, hapticGap: 150 },
  easing: {
    standard: Easing.bezier(0.2, 0, 0, 1),
    exit: Easing.bezier(0.3, 0, 1, 1),
  },
  spring: {
    press: { damping: 18, stiffness: 320, mass: 0.6 },
    sheet: { damping: 22, stiffness: 220, overshootClamping: true },
    recordMorph: { damping: 14, stiffness: 180 },
    chip: { damping: 20, stiffness: 260 },
  },
  sheetDismiss: { distance: 120, velocity: 800 },
  toastDuration: 2400,
  holdToEnd: 600,
  pressScale: 0.97,
  pressOpacity: 0.92,
} as const;
