import type { ReactNode } from "react";
import { View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useKeyboard } from "@/lib/useKeyboardOffset";
import { useTheme } from "@/theme/ThemeProvider";
import { withAlpha } from "@/theme/colorMix";
import { layout, sizes, space } from "@/theme/tokens";

// The dock floats 12 pt above whatever is under it. A screen with a tab bar already
// sits above the home indicator; a full-screen one has to clear it itself.
function useDockBottom(aboveTabBar: boolean): number {
  const insets = useSafeAreaInsets();
  const keyboard = useKeyboard();

  const base = aboveTabBar && !keyboard.isOpen ? 0 : insets.bottom;

  return (keyboard.isOpen ? 0 : base) + keyboard.lift + space.md;
}

// Padding for the end of a scrolling list, so the last row can scroll clear of the dock.
export function useDockClearance(aboveTabBar = true): number {
  return useDockBottom(aboveTabBar) + sizes.dockHeight + space["2xl"];
}

export interface BottomDockProps {
  children: ReactNode;
  // True on screens that show the tab bar.
  aboveTabBar?: boolean;
}

export function BottomDock({ children, aboveTabBar = true }: BottomDockProps) {
  const { colors } = useTheme();
  const bottom = useDockBottom(aboveTabBar);

  return (
    <View
      pointerEvents="box-none"
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        paddingTop: space["3xl"],
        paddingBottom: bottom,
        paddingHorizontal: layout.screenGutter,
      }}
    >
      {/* The top of the dock fades the list out; below that it is solid, so labels never run into the buttons. */}
      <LinearGradient
        pointerEvents="none"
        colors={[withAlpha(colors.canvas, 0), colors.canvas]}
        style={{ position: "absolute", top: 0, left: 0, right: 0, height: space["3xl"] }}
      />
      <View
        pointerEvents="none"
        style={{ position: "absolute", top: space["3xl"], left: 0, right: 0, bottom: 0, backgroundColor: colors.canvas }}
      />
      {children}
    </View>
  );
}
