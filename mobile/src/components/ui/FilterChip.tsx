import { Pressable, View } from "react-native";
import Animated from "react-native-reanimated";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Text } from "./Text";
import { usePressAnimation } from "./usePressAnimation";

export interface FilterChipProps {
  label: string;
  selected: boolean;
  onPress: () => void;
  // Shown after the label, like "Overdue 3".
  count?: number;
}

export function FilterChip({ label, selected, onPress, count }: FilterChipProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();
  const extraHit = (sizes.hitMin - sizes.chipHeight) / 2;

  const handlePress = () => {
    if (!selected) playHaptic("selection");
    onPress();
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={count === undefined ? label : `${label}, ${count}`}
      accessibilityState={{ selected }}
      hitSlop={{ top: extraHit, bottom: extraHit }}
      onPress={handlePress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
    >
      <Animated.View
        style={[
          {
            flexDirection: "row",
            alignItems: "center",
            gap: space.sm,
            height: sizes.chipHeight,
            paddingHorizontal: space.lg,
            borderRadius: radii.sm,
            backgroundColor: selected ? colors.ink : "transparent",
            borderWidth: borders.thin,
            borderColor: selected ? colors.ink : colors.borderControl,
          },
          animatedStyle,
        ]}
      >
        <Text variant="subhead" color={selected ? colors.onInk : colors.textPrimary}>
          {label}
        </Text>
        {count !== undefined && (
          <View>
            <Text variant="mono" color={selected ? colors.onInk : colors.textSecondary}>
              {count}
            </Text>
          </View>
        )}
      </Animated.View>
    </Pressable>
  );
}
