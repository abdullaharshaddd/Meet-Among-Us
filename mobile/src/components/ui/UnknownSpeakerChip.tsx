import { Pressable } from "react-native";
import Animated from "react-native-reanimated";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Icon } from "./Icon";
import { Text } from "./Text";
import { usePressAnimation } from "./usePressAnimation";

// Set to false to draw a solid outline instead, if dashed borders look wrong on a device.
// The "?" glyph is what marks the chip as unmatched either way.
const USE_DASHED_OUTLINE = true;

export interface UnknownSpeakerChipProps {
  // The N in "Unknown Speaker N". A label for a voice that matched nobody, not a person.
  number: number;
  // Opens the rename sheet.
  onPress: () => void;
  // Only the preview passes this, to show both outlines side by side.
  outline?: "dashed" | "solid";
}

export function UnknownSpeakerChip({ number, onPress, outline = USE_DASHED_OUTLINE ? "dashed" : "solid" }: UnknownSpeakerChipProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();
  const extraHit = (sizes.hitMin - sizes.chipHeight) / 2;
  const label = `Unknown Speaker ${number}`;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${label}. Tap to rename.`}
      hitSlop={{ top: extraHit, bottom: extraHit }}
      onPress={onPress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={{ alignSelf: "flex-start" }}
    >
      <Animated.View
        style={[
          {
            flexDirection: "row",
            alignItems: "center",
            gap: space.sm,
            minHeight: sizes.chipHeight,
            paddingHorizontal: space.md,
            borderRadius: radii.sm,
            borderWidth: borders.thin,
            borderStyle: outline,
            borderColor: colors.borderStrong,
          },
          animatedStyle,
        ]}
      >
        <Text variant="mono" tone="secondary">
          ?
        </Text>
        <Text variant="subhead">{label}</Text>
        <Icon name="edit" size="sm" color={colors.textSecondary} />
      </Animated.View>
    </Pressable>
  );
}
