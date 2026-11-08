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

interface Slot {
  x: number;
  width: number;
}

export function SegmentedTabs<Key extends string>({ options, value, onChange }: SegmentedTabsProps<Key>) {
  const { colors } = useTheme();
  // Each segment is as wide as its label needs, with the spare room shared out evenly,
  // so "Action items" never gets squeezed. The raised pill follows the measured slots.
  const [slots, setSlots] = useState<Record<string, Slot>>({});
  const slideX = useSharedValue(0);
  const slideWidth = useSharedValue(0);
  const hasPlaced = useSharedValue(false);

  const slot = slots[value];

  useEffect(() => {
    if (!slot) return;

    // The first placement is instant, so the pill doesn't slide in from the corner.
    if (!hasPlaced.value) {
      slideX.value = slot.x + space.xxs;
      slideWidth.value = slot.width - space.xxs * 2;
      hasPlaced.value = true;
      return;
    }

    slideX.value = withSpring(slot.x + space.xxs, motion.spring.chip);
    slideWidth.value = withSpring(slot.width - space.xxs * 2, motion.spring.chip);
  }, [slot, slideX, slideWidth, hasPlaced]);

  const pillStyle = useAnimatedStyle(() => ({
    width: slideWidth.value,
    transform: [{ translateX: slideX.value }],
  }));

  const choose = (key: Key) => {
    if (key === value) return;

    playHaptic("selection");
    onChange(key);
  };

  const extraHit = (sizes.hitMin - sizes.segmentedHeight) / 2;

  return (
    <View
      accessibilityRole="tablist"
      style={{
        flexDirection: "row",
        height: sizes.segmentedHeight,
        borderRadius: radii.md,
        backgroundColor: colors.sunken,
        borderWidth: borders.hairline,
        borderColor: colors.border,
      }}
    >
      {slot && (
        <Animated.View
          pointerEvents="none"
          style={[
            {
              position: "absolute",
              top: space.xs,
              bottom: space.xs,
              left: 0,
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
            onLayout={(event) => {
              const { x, width } = event.nativeEvent.layout;
              const known = slots[option.key];

              if (!known || known.x !== x || known.width !== width) setSlots((current) => ({ ...current, [option.key]: { x, width } }));
            }}
            hitSlop={{ top: extraHit, bottom: extraHit }}
            style={{ flexGrow: 1, flexShrink: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: space.sm }}
          >
            <Text variant="subhead" tone={isSelected ? "primary" : "secondary"} numberOfLines={1}>
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
