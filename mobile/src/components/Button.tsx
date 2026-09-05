import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, type PressableProps } from "react-native";
import { borders, colors, radii, space, touch } from "@/theme/tokens";
import { Text } from "./Text";

type Variant = "primary" | "secondary" | "ghost" | "destructive";

export interface ButtonProps extends Omit<PressableProps, "children" | "style"> {
  label: string;
  variant?: Variant;
  loading?: boolean;
}

const FILLS: Record<Variant, { bg: string; bgPressed: string; border?: string; text: string }> = {
  primary: { bg: colors.accent.base, bgPressed: colors.accent.pressed, text: colors.text.onAccent },
  secondary: {
    bg: colors.bg.surface,
    bgPressed: colors.bg.raised,
    border: colors.border.default,
    text: colors.text.primary,
  },
  ghost: { bg: "transparent", bgPressed: colors.bg.surface, text: colors.text.primary },
  destructive: { bg: colors.state.danger, bgPressed: "#B62822", text: colors.text.primary },
};

// Buttons name the action ("Create account"), never "Submit" — enforced by
// convention, not code: `label` is required so nobody forgets to pass one.
export function Button({ label, variant = "primary", loading = false, disabled, onFocus, onBlur, ...props }: ButtonProps) {
  const [focused, setFocused] = useState(false);
  const fill = FILLS[variant];
  const isDisabled = disabled || loading;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      disabled={isDisabled}
      onFocus={(e) => {
        setFocused(true);
        onFocus?.(e);
      }}
      onBlur={(e) => {
        setFocused(false);
        onBlur?.(e);
      }}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: pressed ? fill.bgPressed : fill.bg,
          borderWidth: fill.border ? borders.hairline : 0,
          borderColor: fill.border,
          opacity: isDisabled && !loading ? 0.4 : 1,
        },
        focused && styles.focusRing,
      ]}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={fill.text} />
      ) : (
        <Text variant="bodyStrong" style={{ color: fill.text }}>
          {label}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: touch.min,
    paddingHorizontal: space.lg,
    borderRadius: radii.md,
    alignItems: "center",
    justifyContent: "center",
  },
  focusRing: {
    borderWidth: borders.focus,
    borderColor: colors.focus,
  },
});
