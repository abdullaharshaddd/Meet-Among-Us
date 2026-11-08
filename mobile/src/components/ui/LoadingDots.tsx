import { useEffect } from "react";
import { View } from "react-native";
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { motion, opacity, radii, sizes, space } from "@/theme/tokens";

const DOT_COUNT = 3;

function Dot({ index, color }: { index: number; color: string }) {
  const reducedMotion = useReducedMotion();
  const dotOpacity = useSharedValue(reducedMotion ? 1 : opacity.dim);

  useEffect(() => {
    if (reducedMotion) {
      dotOpacity.value = 1;
      return;
    }

    const pulse = withSequence(
      withTiming(1, { duration: motion.duration.base, easing: motion.easing.standard }),
      withTiming(opacity.dim, { duration: motion.duration.base, easing: motion.easing.standard }),
    );

    dotOpacity.value = withDelay(index * motion.duration.fast, withRepeat(pulse, -1));

    return () => cancelAnimation(dotOpacity);
  }, [reducedMotion, index, dotOpacity]);

  const style = useAnimatedStyle(() => ({ opacity: dotOpacity.value }));

  return (
    <Animated.View
      style={[{ width: sizes.loadingDot, height: sizes.loadingDot, borderRadius: radii.pill, backgroundColor: color }, style]}
    />
  );
}

// Three dots that pulse one after another. Under reduced motion they sit still.
export function LoadingDots({ color }: { color: string }) {
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: space.xs }}>
      {Array.from({ length: DOT_COUNT }, (_, index) => (
        <Dot key={index} index={index} color={color} />
      ))}
    </View>
  );
}
