import { Redirect, Tabs } from "expo-router";
import { borders, colors, fonts, type } from "@/theme/tokens";
import { useAuthStore } from "@/store/authStore";

// The auth guard: every screen under (app) relies on this redirect instead
// of checking for a token itself.
export default function AppLayout() {
  const accessToken = useAuthStore((s) => s.accessToken);

  if (!accessToken) {
    return <Redirect href="/(auth)/login" />;
  }

  // Text-only tabs — no icon library is installed yet, and label-only tabs
  // still fit the restrained direction. Revisit with icons as a polish
  // pass, not a gap.
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accent.base,
        tabBarInactiveTintColor: colors.text.secondary,
        tabBarStyle: {
          backgroundColor: colors.bg.surface,
          borderTopColor: colors.border.default,
          borderTopWidth: borders.hairline,
        },
        tabBarLabelStyle: { fontFamily: fonts.uiMedium, fontSize: type.caption.size },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Home" }} />
      <Tabs.Screen name="projects" options={{ title: "Projects" }} />
      <Tabs.Screen name="meetings" options={{ title: "Meetings" }} />
      <Tabs.Screen name="enroll" options={{ title: "Enroll" }} />
      <Tabs.Screen name="settings" options={{ title: "Settings" }} />
    </Tabs>
  );
}
