import { useRouter } from "expo-router";
import { View } from "react-native";
import { Screen, Text, Card, Button, EmptyState } from "@/components";
import { useAuthStore } from "@/store/authStore";
import { space } from "@/theme/tokens";

export default function HomeScreen() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  // `user` is null right after a cold restart (not persisted — see
  // authStore.ts) — treat "unknown" the same as "not complete" so this
  // never falsely tells someone they're enrolled.
  const needsEnrollment = user?.enrollment_status !== "complete";

  return (
    <Screen style={{ gap: space.lg }}>
      <Text variant="title">{user ? `Welcome, ${user.display_name}` : "Welcome back"}</Text>

      {needsEnrollment && (
        <Card style={{ gap: space.sm }}>
          <Text variant="heading">Finish voice enrollment</Text>
          <Text variant="body" tone="secondary">
            Record three short passages so meetings can recognize your voice. You can browse everything else in the meantime.
          </Text>
          <Button label="Start enrollment" variant="secondary" onPress={() => router.push("/(app)/enroll")} />
        </Card>
      )}

      <View style={{ flex: 1, justifyContent: "center" }}>
        <EmptyState glyph="▢" title="No workspaces yet" description="Create or join a workspace — coming in Phase 2." />
      </View>
    </Screen>
  );
}
