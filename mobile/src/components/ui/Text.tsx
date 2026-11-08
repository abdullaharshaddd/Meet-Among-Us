import { Text as RNText, type TextProps as RNTextProps } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { type, type Palette, type TypeStep } from "@/theme/tokens";

const TONES = {
  primary: "textPrimary",
  secondary: "textSecondary",
  tertiary: "textTertiary",
  onInk: "onInk",
  onSignal: "onSignal",
  signal: "signalText",
  success: "success",
  warning: "warning",
  danger: "danger",
} as const satisfies Record<string, keyof Palette>;

export type Tone = keyof typeof TONES;

export function toneColor(colors: Palette, tone: Tone): string {
  return colors[TONES[tone]];
}

const HEADING_STEPS: TypeStep[] = ["displayXl", "displayLg", "displayMd", "title"];

export interface TextProps extends RNTextProps {
  variant?: TypeStep;
  tone?: Tone;
  // For the rare case a component already knows its exact color, like a label on a button fill.
  color?: string;
}

export function Text({ variant = "body", tone = "primary", color, style, ...props }: TextProps) {
  const { colors } = useTheme();
  const isUrdu = variant.startsWith("urdu");

  return (
    <RNText
      accessibilityRole={HEADING_STEPS.includes(variant) ? "header" : undefined}
      style={[
        type[variant],
        { color: color ?? toneColor(colors, tone) },
        isUrdu && { writingDirection: "rtl", textAlign: "right" },
        style,
      ]}
      {...props}
    />
  );
}
