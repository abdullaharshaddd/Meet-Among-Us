import { Text as RNText, type TextProps as RNTextProps } from "react-native";
import { colors, fonts, type } from "@/theme/tokens";

type Variant = keyof typeof type;
type Tone =
  | "primary"
  | "secondary"
  | "tertiary"
  | "disabled"
  | "onAccent"
  | "accent"
  | "recording"
  | "uploading"
  | "success"
  | "warning"
  | "danger";

// The single place tone names resolve to a color — add a tone here, never
// a hex literal at a call site.
function toneColor(tone: Tone): string {
  switch (tone) {
    case "accent":
      return colors.accent.base;
    case "recording":
      return colors.state.recording;
    case "uploading":
      return colors.state.uploading;
    case "success":
      return colors.state.success;
    case "warning":
      return colors.state.warning;
    case "danger":
      return colors.state.danger;
    default:
      return colors.text[tone];
  }
}

export interface TextProps extends RNTextProps {
  variant?: Variant;
  tone?: Tone;
}

// The mechanism that enforces "no inline hex, no inline font size": a screen
// picks a named variant and tone, never a number or a color.
export function Text({ variant = "body", tone = "primary", style, ...props }: TextProps) {
  const step = type[variant];
  return (
    <RNText
      style={[
        {
          fontFamily: fonts[step.weight],
          fontSize: step.size,
          lineHeight: step.lineHeight,
          color: toneColor(tone),
        },
        style,
      ]}
      {...props}
    />
  );
}

export function Mono(props: Omit<TextProps, "variant"> & { small?: boolean }) {
  const { small, ...rest } = props;
  return <Text variant={small ? "monoSmall" : "mono"} {...rest} />;
}

// Wraps Urdu in Unicode directional isolates (FSI/PDI) so a Nastaliq run
// embedded in an English sentence doesn't drag neighbouring LTR punctuation
// into itself — React Native has no CSS `unicode-bidi: isolate` to reach for.
const FSI = "⁨";
const PDI = "⁩";

export function Urdu({ tone = "primary", style, children, ...props }: Omit<TextProps, "variant">) {
  const step = type.urdu;
  const isolated = typeof children === "string" ? `${FSI}${children}${PDI}` : children;
  return (
    <RNText
      style={[
        {
          fontFamily: fonts.urdu,
          fontSize: step.size,
          lineHeight: step.lineHeight,
          color: toneColor(tone),
          writingDirection: "rtl",
          textAlign: "right",
        },
        style,
      ]}
      {...props}
    >
      {isolated}
    </RNText>
  );
}
