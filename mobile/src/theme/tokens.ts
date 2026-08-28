// Design tokens from CLAUDE.md. Never hardcode a hex color or font name outside
// this file — every screen imports from here so the app can be restyled in one place.

export const colors = {
  canvas: "#0D1117",
  surface: "#161B22",
  border: "#30363D",
  textPrimary: "#E6EDF3",
  textSecondary: "#8B949E",
  accent: "#14B8A6",
} as const;

export const fonts = {
  display: "GeneralSans-Regular", // Fontshare .otf, loaded manually — see mobile setup notes
  displayMedium: "GeneralSans-Medium",
  mono: "IBMPlexMono_400Regular", // via @expo-google-fonts/ibm-plex-mono
  urdu: "NotoNastaliqUrdu_400Regular", // via @expo-google-fonts/noto-nastaliq-urdu, RTL
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const radii = {
  sm: 6,
  md: 12,
  lg: 20,
  full: 999,
} as const;
