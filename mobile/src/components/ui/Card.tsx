import type { ReactNode } from "react";
import { Pressable, View, type ViewProps } from "react-native";
import Animated from "react-native-reanimated";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, space } from "@/theme/tokens";
import { usePressAnimation } from "./usePressAnimation";

// "live" is the orange-washed card for a meeting that is recording right now.
type Variant = "default" | "live" | "raised";

export interface CardProps extends Omit<ViewProps, "children"> {
  children: ReactNode;
  variant?: Variant;
  // Turn off when the content brings its own padding, like a list of rows.
  padded?: boolean;
  // Giving the card an onPress makes the whole card a button.
  onPress?: () => void;
  accessibilityLabel?: string;
}

export function Card({ children, variant = "default", padded = true, onPress, accessibilityLabel, style, ...props }: CardProps) {
  const { colors, shadow } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();

  const variantStyle = {
    default: { backgroundColor: colors.surface, borderWidth: borders.hairline, borderColor: colors.border },
    live: { backgroundColor: colors.signalWash, borderWidth: 0 },
    raised: { backgroundColor: colors.raised, borderWidth: borders.hairline, borderColor: colors.border, ...shadow },
  }[variant];

  const cardStyle = [variantStyle, { borderRadius: radii.md, padding: padded ? space.lg : 0 }, style];

  if (!onPress) {
    return (
      <View style={cardStyle} {...props}>
        {children}
      </View>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
    >
      <Animated.View style={[cardStyle, animatedStyle]} {...props}>
        {children}
      </Animated.View>
    </Pressable>
  );
}
