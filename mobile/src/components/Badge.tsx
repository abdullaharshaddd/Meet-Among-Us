import { View, StyleSheet } from "react-native";
import { colors, radii, space } from "@/theme/tokens";
import { Text } from "./Text";

type Variant = "neutral" | "accent" | "recording" | "uploading" | "success" | "warning";

const DOT: Record<Variant, string> = {
  neutral: colors.text.tertiary,
  accent: colors.accent.base,
  recording: colors.state.recording,
  uploading: colors.state.uploading,
  success: colors.state.success,
  warning: colors.state.warning,
};

export interface BadgeProps {
  label: string;
  variant?: Variant;
}

// A dot, not a filled pill — a badge is a status label people read many
// times per session (meeting status, upload progress); a colored dot costs
// less visual weight than a filled background repeated down a list.
export function Badge({ label, variant = "neutral" }: BadgeProps) {
  return (
    <View style={styles.row}>
      <View style={[styles.dot, { backgroundColor: DOT[variant] }]} />
      <Text variant="label" tone="secondary">
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.xs,
    alignSelf: "flex-start",
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: radii.pill,
  },
});
