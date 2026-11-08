import { View } from "react-native";
import Animated, { Extrapolation, interpolate, useAnimatedStyle, type SharedValue } from "react-native-reanimated";

export interface ProgressRingProps {
  // 0 to 1.
  progress: SharedValue<number>;
  diameter: number;
  thickness: number;
  color: string;
  trackColor: string;
}

// A circular progress ring made only of Views, so it needs no SVG library. Two half-circle
// windows each show half of a circle whose top and right borders are colored. Turning that
// circle slides the colored arc into view: the right window fills first, then the left.
export function ProgressRing({ progress, diameter, thickness, color, trackColor }: ProgressRingProps) {
  const half = diameter / 2;

  const rightTurn = useAnimatedStyle(() => ({
    transform: [{ rotate: `${interpolate(progress.value, [0, 0.5], [-135, 45], Extrapolation.CLAMP)}deg` }],
  }));

  const leftTurn = useAnimatedStyle(() => ({
    transform: [{ rotate: `${interpolate(progress.value, [0.5, 1], [45, 225], Extrapolation.CLAMP)}deg` }],
  }));

  const arc = {
    position: "absolute",
    top: 0,
    width: diameter,
    height: diameter,
    borderRadius: half,
    borderWidth: thickness,
    borderColor: "transparent",
    borderTopColor: color,
    borderRightColor: color,
  } as const;

  return (
    <View pointerEvents="none" style={{ position: "absolute", width: diameter, height: diameter }}>
      <View
        style={{
          position: "absolute",
          width: diameter,
          height: diameter,
          borderRadius: half,
          borderWidth: thickness,
          borderColor: trackColor,
        }}
      />

      <View style={{ position: "absolute", left: half, top: 0, width: half, height: diameter, overflow: "hidden" }}>
        <Animated.View style={[arc, { left: -half }, rightTurn]} />
      </View>

      <View style={{ position: "absolute", left: 0, top: 0, width: half, height: diameter, overflow: "hidden" }}>
        <Animated.View style={[arc, { left: 0 }, leftTurn]} />
      </View>
    </View>
  );
}
