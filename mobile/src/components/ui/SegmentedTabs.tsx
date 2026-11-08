import { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from "react-native-reanimated";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, motion, radii, sizes, space } from "@/theme/tokens";
import { Text } from "./Text";

export interface SegmentedOption<Key extends string> {
  key: Key;
  label: string;
}

export interface SegmentedTabsProps<Key extends string> {
  options: SegmentedOption<Key>[];
  value: Key;
  onChange: (key: Key) => void;
}

export function SegmentedTabs<Key extends string>({ options, value, onChange }: SegmentedTabsProps<Key>) {
  const { colors } = useTheme();
  const [trackWidth, setTrackWidth] = useState(0);
  const slide = useSharedValue(0);

  const selectedIndex = Math.max(0, options.findIndex((option) => option.key === value));
  const segmentWidth = trackWidth > 0 ? (trackWidth - space.xs * 2) / options.length : 0;

  // The raised pill slides to the chosen segment instead of jumping.
  const pillStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: slide.value }],
  }));

  useEffect(() => {
    if (segmentWidth > 0) slide.value = withSpring(selectedIndex * segmentWidth, motion.spring.chip);
  }, [selectedIndex, segmentWidth, slide]);

  const choose = (key: Key) => {
    if (key === value) return;

    playHaptic("selection");
    onChange(key);
  };

  return (
    <View
      accessibilityRole="tablist"
      onLayout={(event) => setTrackWidth(event.nativeEvent.layout.width)}
      style={{
        flexDirection: "row",
        height: sizes.segmentedHeight,
        padding: space.xs,
        borderRadius: radii.md,
        backgroundColor: colors.sunken,
        borderWidth: borders.hairline,
        borderColor: colors.border,
      }}
    >
      {segmentWidth > 0 && (
        <Animated.View
          pointerEvents="none"
          style={[
            {
              position: "absolute",
              top: space.xs,
              bottom: space.xs,
              left: space.xs,
              width: segmentWidth,
              borderRadius: radii.sm,
              backgroundColor: colors.raised,
              borderWidth: borders.hairline,
              borderColor: colors.borderStrong,
            },
            pillStyle,
          ]}
        />
      )}

      {options.map((option) => {
        const isSelected = option.key === value;

        return (
          <Pressable
            key={option.key}
            accessibilityRole="tab"
            accessibilityState={{ selected: isSelected }}
            accessibilityLabel={option.label}
            onPress={() => choose(option.key)}
            hitSlop={{ top: (sizes.hitMin - sizes.segmentedHeight) / 2, bottom: (sizes.hitMin - sizes.segmentedHeight) / 2 }}
            style={{ flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: space.xxs }}
          >
            <Text
              variant="subhead"
              tone={isSelected ? "primary" : "secondary"}
              numberOfLines={1}
              adjustsFontSizeToFit
              minimumFontScale={0.85}
            >
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
