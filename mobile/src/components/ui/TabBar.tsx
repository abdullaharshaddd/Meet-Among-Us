import { Pressable, View } from "react-native";
import type { BottomTabBarProps } from "expo-router/build/react-navigation/bottom-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useKeyboard } from "@/lib/useKeyboardOffset";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Icon, type IconName } from "./Icon";
import { Text } from "./Text";

interface TabEntry {
  route: string;
  label: string;
  icon: IconName;
}

// Four tabs. Enrollment is reached from the Meetings prompt and from Settings, not from here.
const TABS: TabEntry[] = [
  { route: "meetings", label: "Meetings", icon: "tabMeetings" },
  { route: "tasks", label: "Tasks", icon: "tabTasks" },
  { route: "assistant", label: "Assistant", icon: "tabAssistant" },
  { route: "settings", label: "Settings", icon: "tabSettings" },
];

export function TabBar({ state, navigation }: BottomTabBarProps) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const keyboard = useKeyboard();

  const focusedRoute = state.routes[state.index];
  const isTabRoute = TABS.some((tab) => tab.route === focusedRoute.name);

  // Full-screen flows (live recording, enrollment) and the open keyboard hide the bar.
  if (!isTabRoute || keyboard.isOpen) return null;

  return (
    <View
      style={{
        flexDirection: "row",
        height: sizes.tabBarHeight + insets.bottom,
        paddingBottom: insets.bottom,
        backgroundColor: colors.canvas,
        borderTopWidth: borders.hairline,
        borderTopColor: colors.border,
      }}
    >
      {TABS.map((tab) => {
        const route = state.routes.find((item) => item.name === tab.route);
        if (!route) return null;

        const isSelected = focusedRoute.name === tab.route;

        const onPress = () => {
          const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });

          if (!isSelected && !event.defaultPrevented) {
            playHaptic("selection");
            navigation.navigate(route.name);
          }
        };

        return (
          <Pressable
            key={tab.route}
            accessibilityRole="tab"
            accessibilityLabel={tab.label}
            accessibilityState={{ selected: isSelected }}
            onPress={onPress}
            style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.xs, minHeight: sizes.hitMin }}
          >
            <Icon name={tab.icon} size="lg" color={isSelected ? colors.ink : colors.textTertiary} />

            <Text variant="label" tone={isSelected ? "primary" : "secondary"}>
              {tab.label}
            </Text>

            <View
              style={{
                width: sizes.tabIndicatorWidth,
                height: sizes.tabIndicatorHeight,
                borderRadius: radii.pill,
                backgroundColor: isSelected ? colors.ink : "transparent",
              }}
            />
          </Pressable>
        );
      })}
    </View>
  );
}
