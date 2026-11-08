import type { ReactNode } from "react";
import { View, type ViewStyle } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/theme/ThemeProvider";

export interface ScreenProps {
  children: ReactNode;
  // Screens that draw their own Header already clear the top inset.
  clearTopInset?: boolean;
  style?: ViewStyle;
}

// The canvas every screen sits on. The bottom inset is left to the dock or the tab bar.
export function Screen({ children, clearTopInset = false, style }: ScreenProps) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  return <View style={[{ flex: 1, backgroundColor: colors.canvas, paddingTop: clearTopInset ? insets.top : 0 }, style]}>{children}</View>;
}
