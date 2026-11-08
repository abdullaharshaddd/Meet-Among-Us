import { Pressable } from "react-native";
import Animated from "react-native-reanimated";
import { useTheme } from "@/theme/ThemeProvider";
import { radii, sizes, space } from "@/theme/tokens";
import { Text } from "./Text";
import { usePressAnimation } from "./usePressAnimation";

export interface CitationChipProps {
  // The meeting name and the moment the answer came from, like "Sprint sync · 12:04".
  label: string;
  onPress: () => void;
}

export function CitationChip({ label, onPress }: CitationChipProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();
  const extraHit = (sizes.hitMin - sizes.chipCitation) / 2;

  return (
    <Pressable
      accessibilityRole="link"
      accessibilityLabel={`Source: ${label}`}
      hitSlop={{ top: extraHit, bottom: extraHit }}
      onPress={onPress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={{ alignSelf: "flex-start" }}
    >
      <Animated.View
        style={[
          {
            height: sizes.chipCitation,
            justifyContent: "center",
            paddingHorizontal: space.md,
            borderRadius: radii.sm,
            backgroundColor: colors.sunken,
          },
          animatedStyle,
        ]}
      >
        <Text variant="mono" tone="secondary" numberOfLines={1}>
          {label}
        </Text>
      </Animated.View>
    </Pressable>
  );
}
