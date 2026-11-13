import { Pressable, View } from "react-native";
import Animated, { useAnimatedStyle, withTiming, type SharedValue } from "react-native-reanimated";
import { BottomDock, Text } from "@/components/ui";
import { useTheme } from "@/theme/ThemeProvider";
import { motion, radii, sizes, space } from "@/theme/tokens";

export interface MeetingsDockProps {
  isEnrolled: boolean;
  isScrollingDown: SharedValue<boolean>;
  onStart: () => void;
  onEnroll: () => void;
}

// A centred Start pill. Scrolling down shrinks it to a dot. There is no Join: the host adds people to a meeting,
// and it appears in their list.
export function MeetingsDock({ isEnrolled, isScrollingDown, onStart, onEnroll }: MeetingsDockProps) {
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

  return (
    <BottomDock>
      {!isEnrolled && (
        <Pressable
          accessibilityRole="link"
          accessibilityLabel="Enroll your voice so your speech is named in meetings"
          onPress={onEnroll}
          style={{ alignSelf: "center", minHeight: sizes.hitMin, justifyContent: "center", paddingBottom: space.xs }}
        >
          <Text variant="caption" tone="secondary" style={{ textAlign: "center" }}>
            Enroll your voice so your speech is named in meetings.{" "}
            <Text variant="caption" style={{ textDecorationLine: "underline" }}>
              Enroll now
            </Text>
          </Text>
        </Pressable>
      )}

      <View style={{ height: sizes.pillHeight, alignItems: "center", justifyContent: "center" }}>
        <Pressable accessibilityRole="button" accessibilityLabel="New meeting" onPress={onStart}>
          <Animated.View
            style={[
              { height: sizes.pillHeight, borderRadius: radii.pill, alignItems: "center", justifyContent: "center", overflow: "hidden", backgroundColor: colors.ink },
              pillStyle,
            ]}
          >
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <View style={{ width: space.md, height: space.md, borderRadius: radii.pill, backgroundColor: colors.onInk }} />
              <Animated.View style={[{ overflow: "hidden" }, labelStyle]}>
                <Text variant="button" color={colors.onInk} numberOfLines={1}>
                  New meeting
                </Text>
              </Animated.View>
            </View>
          </Animated.View>
        </Pressable>
      </View>
    </BottomDock>
  );
}
