import { useEffect } from "react";
import type { DimensionValue } from "react-native";
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { useTheme } from "@/theme/ThemeProvider";
import { motion, opacity, radii } from "@/theme/tokens";

export interface SkeletonProps {
  width?: DimensionValue;
  height: number;
  radius?: number;
}

// A grey placeholder that breathes while content loads. Under reduced motion it stays still.
export function Skeleton({ width = "100%", height, radius = radii.sm }: SkeletonProps) {
  const { colors } = useTheme();
  const reducedMotion = useReducedMotion();
  const level = useSharedValue(1);

  useEffect(() => {
    if (reducedMotion) {
      level.value = 1;
      return;
    }

    const breathe = withSequence(
      withTiming(opacity.muted, { duration: motion.duration.slow * 2, easing: motion.easing.standard }),
      withTiming(1, { duration: motion.duration.slow * 2, easing: motion.easing.standard }),
    );

    level.value = withRepeat(breathe, -1);

    return () => cancelAnimation(level);
  }, [reducedMotion, level]);

  const style = useAnimatedStyle(() => ({ opacity: level.value }));

  return (
    <Animated.View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[{ width, height, borderRadius: radius, backgroundColor: colors.border }, style]}
    />
  );
}
