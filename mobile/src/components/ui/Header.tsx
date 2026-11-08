import type { ReactNode } from "react";
import { Pressable, View } from "react-native";
import Animated, { Extrapolation, interpolate, useAnimatedStyle, type SharedValue } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, sizes, space } from "@/theme/tokens";
import { Icon, type IconName } from "./Icon";
import { Text } from "./Text";

// How far the list scrolls before the small title has fully replaced the large one.
const COLLAPSE_START = 28;
const COLLAPSE_END = 64;

export interface HeaderProps {
  // The small title in the bar. It fades in as the large title scrolls away.
  title?: string;
  onBack?: () => void;
  // Replaces the back arrow, like the workspace switcher on Meetings.
  leading?: ReactNode;
  // At most one action on the right.
  action?: { icon: IconName; label: string; onPress: () => void };
  scrollY?: SharedValue<number>;
}

export function Header({ title, onBack, leading, action, scrollY }: HeaderProps) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const titleStyle = useAnimatedStyle(() => ({
    opacity: scrollY ? interpolate(scrollY.value, [COLLAPSE_START, COLLAPSE_END], [0, 1], Extrapolation.CLAMP) : 0,
  }));

  const edgeStyle = useAnimatedStyle(() => ({
    opacity: scrollY ? interpolate(scrollY.value, [0, COLLAPSE_START], [0, 1], Extrapolation.CLAMP) : 0,
  }));

  return (
    <View style={{ paddingTop: insets.top, backgroundColor: colors.canvas }}>
      <View
        style={{
          height: sizes.headerBar,
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          paddingHorizontal: layout.screenGutter,
        }}
      >
        <View style={{ minWidth: sizes.hitMin, alignItems: "flex-start", justifyContent: "center", flexShrink: 1 }}>
          {leading ??
            (onBack && (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Back"
                onPress={onBack}
                hitSlop={space.sm}
                style={{ width: sizes.hitMin, height: sizes.hitMin, justifyContent: "center" }}
              >
                <Icon name="back" size="lg" />
              </Pressable>
            ))}
        </View>

        <Animated.View pointerEvents="none" style={[{ position: "absolute", left: 0, right: 0, alignItems: "center" }, titleStyle]}>
          <Text variant="headline" numberOfLines={1} style={{ maxWidth: "55%" }}>
            {title}
          </Text>
        </Animated.View>

        <View style={{ minWidth: sizes.hitMin, alignItems: "flex-end", justifyContent: "center" }}>
          {action && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={action.label}
              onPress={action.onPress}
              hitSlop={space.sm}
              style={{ width: sizes.hitMin, height: sizes.hitMin, alignItems: "flex-end", justifyContent: "center" }}
            >
              <Icon name={action.icon} size="lg" />
            </Pressable>
          )}
        </View>
      </View>

      <Animated.View style={[{ height: borders.hairline, backgroundColor: colors.border }, edgeStyle]} />
    </View>
  );
}

// The big title that sits at the top of the scrolling content and scrolls away.
export function LargeTitle({ children, subtitle }: { children: string; subtitle?: string }) {
  return (
    <View style={{ gap: space.xs, paddingBottom: space.lg }}>
      <Text variant="displayXl" accessibilityRole="header">
        {children}
      </Text>
      {subtitle && (
        <Text variant="callout" tone="secondary">
          {subtitle}
        </Text>
      )}
    </View>
  );
}
