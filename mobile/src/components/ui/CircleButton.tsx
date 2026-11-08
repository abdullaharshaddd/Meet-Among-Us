import { Pressable, View } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, opacity, radii, sizes, space } from "@/theme/tokens";
import { Icon, type IconName } from "./Icon";
import { Text } from "./Text";
import { usePressAnimation } from "./usePressAnimation";
import Animated from "react-native-reanimated";

export interface CircleButtonProps {
  icon: IconName;
  label: string;
  onPress: () => void;
  disabled?: boolean;
}

// A 56 pt outlined round button with a small label under it, for the secondary controls in a dock.
export function CircleButton({ icon, label, onPress, disabled = false }: CircleButtonProps) {
  const { colors } = useTheme();
  const { animatedStyle, onPressIn, onPressOut } = usePressAnimation();

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={{ alignItems: "center", gap: space.sm, width: sizes.stopButton }}
    >
      <Animated.View
        style={[
          {
            width: sizes.dockSecondary,
            height: sizes.dockSecondary,
            borderRadius: radii.pill,
            alignItems: "center",
            justifyContent: "center",
            borderWidth: borders.thin,
            borderColor: colors.borderControl,
            opacity: disabled ? opacity.muted : 1,
          },
          animatedStyle,
        ]}
      >
        <Icon name={icon} size="lg" />
      </Animated.View>
      <View>
        <Text variant="label" tone="secondary">
          {label}
        </Text>
      </View>
    </Pressable>
  );
}
