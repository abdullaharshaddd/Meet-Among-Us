import { Pressable, View } from "react-native";
import Animated, { useAnimatedProps, useAnimatedStyle, withTiming, type SharedValue } from "react-native-reanimated";
import { BottomDock, Button, Text } from "@/components/ui";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, motion, radii, sizes, space } from "@/theme/tokens";

export interface MeetingsDockProps {
  isEnrolled: boolean;
  isScrollingDown: SharedValue<boolean>;
  onStart: () => void;
  onJoin: () => void;
  onEnroll: () => void;
}

// A centred Start pill with Join on its left. Scrolling down shrinks the pill to a dot and hides Join.
export function MeetingsDock({ isEnrolled, isScrollingDown, onStart, onJoin, onEnroll }: MeetingsDockProps) {
  const { colors } = useTheme();

  const pillStyle = useAnimatedStyle(() => ({
    width: withTiming(isScrollingDown.value ? sizes.pillHeight : sizes.startPillWidth, { duration: motion.duration.base, easing: motion.easing.standard }),
  }));

  // The label gives up its width too, so the dot ends up centred in the small circle.
  const labelStyle = useAnimatedStyle(() => ({
    opacity: withTiming(isScrollingDown.value ? 0 : 1, { duration: motion.duration.fast }),
    maxWidth: withTiming(isScrollingDown.value ? 0 : sizes.startPillWidth, { duration: motion.duration.base }),
    marginLeft: withTiming(isScrollingDown.value ? 0 : space.sm, { duration: motion.duration.base }),
  }));

  const joinStyle = useAnimatedStyle(() => ({
    opacity: withTiming(isScrollingDown.value ? 0 : 1, { duration: motion.duration.fast }),
  }));

  const joinProps = useAnimatedProps(() => ({
    pointerEvents: isScrollingDown.value ? ("none" as const) : ("auto" as const),
  }));

  return (
    <BottomDock>
      {!isEnrolled && (
        <Pressable
          accessibilityRole="link"
          accessibilityLabel="Enroll your voice to start or join meetings"
          onPress={onEnroll}
          style={{ alignSelf: "center", minHeight: sizes.hitMin, justifyContent: "center", paddingBottom: space.xs }}
        >
          <Text variant="caption" tone="secondary" style={{ textAlign: "center" }}>
            Enroll your voice to start or join a meeting.{" "}
            <Text variant="caption" style={{ textDecorationLine: "underline" }}>
              Enroll now
            </Text>
          </Text>
        </Pressable>
      )}

      <View style={{ height: sizes.pillHeight, alignItems: "center", justifyContent: "center" }}>
        <Animated.View animatedProps={joinProps} style={[{ position: "absolute", left: 0 }, joinStyle]}>
          <Button label="Join" variant="ghost" size="dock" fullWidth={false} disabled={!isEnrolled} onPress={onJoin} />
        </Animated.View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Start meeting"
          accessibilityState={{ disabled: !isEnrolled }}
          accessibilityHint={isEnrolled ? undefined : "Enroll your voice first"}
          disabled={!isEnrolled}
          onPress={onStart}
        >
          <Animated.View
            style={[
              {
                height: sizes.pillHeight,
                borderRadius: radii.pill,
                alignItems: "center",
                justifyContent: "center",
                overflow: "hidden",
                backgroundColor: isEnrolled ? colors.signal : colors.sunken,
                borderWidth: isEnrolled ? 0 : borders.hairline,
                borderColor: colors.border,
              },
              pillStyle,
            ]}
          >
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <View
                style={{
                  width: space.md,
                  height: space.md,
                  borderRadius: radii.pill,
                  backgroundColor: isEnrolled ? colors.onSignal : colors.textTertiary,
                }}
              />
              <Animated.View style={[{ overflow: "hidden" }, labelStyle]}>
                <Text variant="button" color={isEnrolled ? colors.onSignal : colors.textTertiary} numberOfLines={1}>
                  Start meeting
                </Text>
              </Animated.View>
            </View>
          </Animated.View>
        </Pressable>
      </View>
    </BottomDock>
  );
}
