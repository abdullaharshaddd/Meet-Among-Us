import { View } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, space } from "@/theme/tokens";
import { Text } from "./Text";

// "live" is the orange one and is only for a meeting that is recording right now.
type Variant = "outline" | "live" | "warning" | "success" | "danger";

export interface BadgeProps {
  label: string;
  variant?: Variant;
}

export function Badge({ label, variant = "outline" }: BadgeProps) {
  const { colors } = useTheme();

  const looks = {
    outline: { fill: "transparent", border: colors.borderStrong, text: colors.textSecondary },
    live: { fill: colors.signal, border: colors.signal, text: colors.onSignal },
    warning: { fill: "transparent", border: colors.warning, text: colors.warning },
    success: { fill: "transparent", border: colors.success, text: colors.success },
    danger: { fill: "transparent", border: colors.danger, text: colors.danger },
  }[variant];

  return (
    <View
      accessible
      accessibilityLabel={label}
      style={{
        alignSelf: "flex-start",
        paddingHorizontal: space.sm,
        paddingVertical: space.xxs,
        borderRadius: radii.xs,
        borderWidth: borders.thin,
        borderColor: looks.border,
        backgroundColor: looks.fill,
      }}
    >
      <Text variant="label" color={looks.text}>
        {label}
      </Text>
    </View>
  );
}
