import { useEffect, useRef, useState } from "react";
import { Pressable, View } from "react-native";
import Animated, { Easing, ReduceMotion, cancelAnimation, useSharedValue, withTiming } from "react-native-reanimated";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { motion, radii, sizes, space } from "@/theme/tokens";
import { ProgressRing } from "./ProgressRing";
import { Text } from "./Text";
import { usePressAnimation } from "./usePressAnimation";

export interface StopButtonProps {
  // Called once the button has been held for the full time.
  onComplete: () => void;
}

const HINT_MILLISECONDS = 1800;
const RING_DIAMETER = sizes.stopButton + sizes.progressRingGap * 2;

// Ending a meeting can't be undone, so a tap only shows a hint and the person has to hold.
export function StopButton({ onComplete }: StopButtonProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();
  const progress = useSharedValue(0);
  const holdTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hintTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const didComplete = useRef(false);
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    return () => {
      if (holdTimer.current) clearTimeout(holdTimer.current);
      if (hintTimer.current) clearTimeout(hintTimer.current);
    };
  }, []);

  const complete = () => {
    didComplete.current = true;
    playHaptic("recordStop");
    onComplete();
  };

  const startHold = () => {
    onPressIn();
    didComplete.current = false;

    // The ring is a progress indicator, so it keeps filling even when other motion is reduced.
    progress.value = withTiming(1, { duration: motion.holdToEnd, easing: Easing.linear, reduceMotion: ReduceMotion.Never });
    holdTimer.current = setTimeout(complete, motion.holdToEnd);
  };

  const endHold = () => {
    onPressOut();

    if (holdTimer.current) clearTimeout(holdTimer.current);
    if (didComplete.current) return;

    cancelAnimation(progress);
    progress.value = withTiming(0, { duration: motion.duration.fast, reduceMotion: ReduceMotion.Never });

    setShowHint(true);
    if (hintTimer.current) clearTimeout(hintTimer.current);
    hintTimer.current = setTimeout(() => setShowHint(false), HINT_MILLISECONDS);
  };

  return (
    <View style={{ alignItems: "center", gap: space.sm }}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="End meeting"
        accessibilityHint="Hold to end the meeting"
        accessibilityActions={[{ name: "activate", label: "End meeting" }]}
        onAccessibilityAction={complete}
        onPressIn={startHold}
        onPressOut={endHold}
        style={{ width: RING_DIAMETER, height: RING_DIAMETER, alignItems: "center", justifyContent: "center" }}
      >
        <ProgressRing
          progress={progress}
          diameter={RING_DIAMETER}
          thickness={sizes.progressRing}
          color={colors.signal}
          trackColor={colors.border}
        />

        <Animated.View
          style={[
            {
              width: sizes.stopButton,
              height: sizes.stopButton,
              borderRadius: sizes.stopButton / 2,
              backgroundColor: colors.ink,
              alignItems: "center",
              justifyContent: "center",
            },
            animatedStyle,
          ]}
        >
          <View style={{ width: space["2xl"], height: space["2xl"], borderRadius: radii.sm, backgroundColor: colors.onInk }} />
        </Animated.View>
      </Pressable>

      {/* Always in the layout, so showing the hint never moves the button. */}
      <Text variant="label" tone="primary" style={{ opacity: showHint ? 1 : 0 }}>
        Hold to end
      </Text>
    </View>
  );
}
