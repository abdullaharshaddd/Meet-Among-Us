import { Pressable, View } from "react-native";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes } from "@/theme/tokens";
import { Icon } from "./Icon";

export interface CheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
}

export function Checkbox({ checked, onChange, label }: CheckboxProps) {
  const { colors } = useTheme();
  const extraHit = (sizes.hitMin - sizes.checkbox) / 2;

  const toggle = () => {
    playHaptic("selection");
    onChange(!checked);
  };

  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityLabel={label}
      accessibilityState={{ checked }}
      hitSlop={{ top: extraHit, bottom: extraHit, left: extraHit, right: extraHit }}
      onPress={toggle}
    >
      <View
        style={{
          width: sizes.checkbox,
          height: sizes.checkbox,
          alignItems: "center",
          justifyContent: "center",
          borderRadius: radii.xs,
          borderWidth: borders.thin,
          borderColor: checked ? colors.ink : colors.borderControl,
          backgroundColor: checked ? colors.ink : "transparent",
        }}
      >
        {checked && <Icon name="check" size="sm" color={colors.onInk} />}
      </View>
    </Pressable>
  );
}
