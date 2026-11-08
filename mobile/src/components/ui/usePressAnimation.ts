import { Extrapolation, interpolate, useAnimatedStyle, useSharedValue, withSpring } from "react-native-reanimated";
import { motion } from "@/theme/tokens";

// Shared by everything that can be pressed. Reanimated's default reduce-motion
// setting makes the spring snap instead of bounce for people who asked for less motion.
export function usePressAnimation() {
  const pressed = useSharedValue(0);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: interpolate(pressed.value, [0, 1], [1, motion.pressOpacity], Extrapolation.CLAMP),
    transform: [{ scale: interpolate(pressed.value, [0, 1], [1, motion.pressScale], Extrapolation.CLAMP) }],
  }));

  const onPressIn = () => {
    pressed.value = withSpring(1, motion.spring.press);
  };

  const onPressOut = () => {
    pressed.value = withSpring(0, motion.spring.press);
  };

  return { animatedStyle, onPressIn, onPressOut };
}
