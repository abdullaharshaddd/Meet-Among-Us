import { Redirect, Tabs } from "expo-router";
import { TabBar } from "@/components/ui";
import { useTheme } from "@/theme/ThemeProvider";
import { useAuthStore } from "@/store/authStore";

// The auth guard: every screen under (app) relies on this redirect instead
// of checking for a token itself.
export default function AppLayout() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const { colors } = useTheme();

  if (!accessToken) {
    return <Redirect href="/(auth)/login" />;
  }

  // Four tabs. The other routes live in the same navigator so they can go full screen,
  // but they have no tab of their own and the bar hides itself on them.
  return (
    <Tabs
      tabBar={(props) => <TabBar {...props} />}
      screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: colors.canvas } }}
    >
      <Tabs.Screen name="meetings" />
      <Tabs.Screen name="tasks" />
      <Tabs.Screen name="assistant" />
      <Tabs.Screen name="settings" />
      <Tabs.Screen name="index" options={{ href: null }} />
      <Tabs.Screen name="live" options={{ href: null }} />
      <Tabs.Screen name="enroll" options={{ href: null }} />
      <Tabs.Screen name="workspaces" options={{ href: null }} />
    </Tabs>
  );
}
