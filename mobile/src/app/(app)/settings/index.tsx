import { View } from "react-native";
import { Screen, Text, Avatar, Button } from "@/components";
import { useAuthStore } from "@/store/authStore";
import { useLogout } from "@/api/auth";
import { space } from "@/theme/tokens";

export default function SettingsScreen() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  return (
    <Screen style={{ gap: space.xl }}>
      <View style={{ alignItems: "center", gap: space.md }}>
        <Avatar name={user?.display_name ?? "?"} imageUrl={user?.avatar_url} size="lg" />
        <View style={{ alignItems: "center" }}>
          <Text variant="heading">{user?.display_name ?? "—"}</Text>
          <Text variant="body" tone="secondary">
            {user?.email ?? "—"}
          </Text>
        </View>
      </View>

      <Button label="Sign out" variant="secondary" onPress={logout} />
    </Screen>
  );
}
