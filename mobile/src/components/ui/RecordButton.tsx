import { useEffect } from "react";
import { Pressable } from "react-native";
import Animated, { interpolate, useAnimatedStyle, useSharedValue, withSpring } from "react-native-reanimated";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { motion, radii, sizes } from "@/theme/tokens";
import { usePressAnimation } from "./usePressAnimation";

export interface RecordButtonProps {
  isRecording: boolean;
  onPress: () => void;
  disabled?: boolean;
}

const STOPPED_SCALE = 0.62;
const STOPPED_RADIUS = radii.lg;

// The orange circle. While recording it shrinks into a rounded square, the usual "tap to stop" shape.
// The buzz is built in, so every recording control feels the same.
export function RecordButton({ isRecording, onPress, disabled = false }: RecordButtonProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();
  const morph = useSharedValue(isRecording ? 1 : 0);

  useEffect(() => {
    morph.value = withSpring(isRecording ? 1 : 0, motion.spring.recordMorph);
  }, [isRecording, morph]);

  const shapeStyle = useAnimatedStyle(() => ({
    borderRadius: interpolate(morph.value, [0, 1], [sizes.recordButton / 2, STOPPED_RADIUS]),
    transform: [{ scale: interpolate(morph.value, [0, 1], [1, STOPPED_SCALE]) }],
  }));

  const handlePress = () => {
    playHaptic(isRecording ? "recordStop" : "recordStart");
    onPress();
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={isRecording ? "Stop recording" : "Start recording"}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={handlePress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={{ width: sizes.recordButton, height: sizes.recordButton, alignItems: "center", justifyContent: "center" }}
    >
      <Animated.View style={[{ width: sizes.recordButton, height: sizes.recordButton }, animatedStyle]}>
        <Animated.View
          style={[
            { width: sizes.recordButton, height: sizes.recordButton, backgroundColor: disabled ? colors.sunken : colors.signal },
            shapeStyle,
          ]}
        />
      </Animated.View>
    </Pressable>
  );
}
