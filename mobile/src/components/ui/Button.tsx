import { useState } from "react";
import { Pressable, StyleSheet, View, type GestureResponderEvent, type PressableProps } from "react-native";
import Animated from "react-native-reanimated";
import { playHaptic, type HapticKind } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Icon, type IconName } from "./Icon";
import { LoadingDots } from "./LoadingDots";
import { Text } from "./Text";
import { usePressAnimation } from "./usePressAnimation";

// "signal" is the record button's orange and is for recording only.
type Variant = "primary" | "secondary" | "ghost" | "signal" | "dangerText";
type Size = "dock" | "md" | "sm";

export interface ButtonProps extends Omit<PressableProps, "children" | "style"> {
  label: string;
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  loading?: boolean;
  // Defaults to full width, except for small buttons that sit inline.
  fullWidth?: boolean;
  // Off by default. A buzz belongs to the outcome (saved, deleted), so the caller picks it.
  haptic?: HapticKind;
}

const HEIGHTS: Record<Size, number> = { dock: sizes.dockHeight, md: sizes.buttonMd, sm: sizes.buttonSm };

export function Button({
  label,
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  fullWidth = size !== "sm",
  haptic,
  disabled = false,
  onPress,
  onFocus,
  onBlur,
  ...props
}: ButtonProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();
  const [isFocused, setIsFocused] = useState(false);

  const looks = disabled
    ? { fill: colors.sunken, text: colors.textTertiary, border: colors.border }
    : {
        primary: { fill: colors.ink, text: colors.onInk, border: undefined },
        secondary: { fill: "transparent", text: colors.textPrimary, border: colors.borderControl },
        ghost: { fill: "transparent", text: colors.textPrimary, border: undefined },
        signal: { fill: colors.signal, text: colors.onSignal, border: undefined },
        dangerText: { fill: "transparent", text: colors.danger, border: undefined },
      }[variant];

  const height = HEIGHTS[size];
  const extraHit = Math.max(0, (sizes.hitMin - height) / 2);

  const handlePress = (event: GestureResponderEvent) => {
    if (haptic) playHaptic(haptic);
    onPress?.(event);
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      hitSlop={{ top: extraHit, bottom: extraHit }}
      onPress={handlePress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      onFocus={(event) => {
        setIsFocused(true);
        onFocus?.(event);
      }}
      onBlur={(event) => {
        setIsFocused(false);
        onBlur?.(event);
      }}
      style={fullWidth ? undefined : styles.shrink}
      {...props}
    >
      <Animated.View
        style={[
          styles.base,
          {
            height,
            backgroundColor: looks.fill,
            borderWidth: !looks.border ? 0 : disabled ? borders.hairline : borders.thin,
            borderColor: looks.border,
          },
          animatedStyle,
        ]}
      >
        {/* Kept in the layout while loading so the button doesn't change width. */}
        <View style={[styles.content, loading && styles.hidden]}>
          {icon && <Icon name={icon} color={looks.text} />}
          <Text variant="button" color={looks.text}>
            {label}
          </Text>
        </View>

        {loading && (
          <View style={styles.loading}>
            <LoadingDots color={looks.text} />
          </View>
        )}

        {isFocused && <View pointerEvents="none" style={[styles.focusRing, { borderColor: colors.focusRing }]} />}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  shrink: {
    alignSelf: "flex-start",
  },
  base: {
    paddingHorizontal: space.xl,
    borderRadius: radii.lg,
    alignItems: "center",
    justifyContent: "center",
  },
  content: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
  },
  hidden: {
    opacity: 0,
  },
  loading: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  focusRing: {
    position: "absolute",
    top: -space.xs,
    left: -space.xs,
    right: -space.xs,
    bottom: -space.xs,
    borderWidth: borders.focus,
    borderRadius: radii.lg + space.xs,
  },
});
