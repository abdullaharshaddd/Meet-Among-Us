import { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { Screen, Text, Avatar, Button, Card } from "@/components";
import { useAuthStore } from "@/store/authStore";
import { useLogout } from "@/api/auth";
import { useEnrollmentStatus, useResetEnrollment } from "@/api/enrollment";
import { space } from "@/theme/tokens";

export default function SettingsScreen() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { data: enrollment } = useEnrollmentStatus();
  const resetEnrollment = useResetEnrollment();
  const [isConfirming, setIsConfirming] = useState(false);
  const [resetFailed, setResetFailed] = useState(false);

  const hasVoiceprint = enrollment !== undefined && enrollment.enrollment_status !== "not_started";

  const reEnroll = async () => {
    setResetFailed(false);

    try {
      await resetEnrollment.mutateAsync();
    } catch {
      setResetFailed(true);
      return;
    }

    setIsConfirming(false);
    router.push("/(app)/enroll");
  };

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

      {hasVoiceprint && !isConfirming && (
        <Button label="Re-enroll my voice" variant="secondary" onPress={() => setIsConfirming(true)} />
      )}

      {isConfirming && (
        <Card level={2} style={{ gap: space.md }}>
          <Text variant="heading">Delete your voiceprint?</Text>
          <Text variant="body" tone="secondary">
            This deletes your current voiceprint and recordings. You will need to record all three passages again before joining meetings.
          </Text>
          {resetFailed && <Text variant="body" tone="danger">We couldn't delete it. Check your connection and try again.</Text>}
          <Button label="Delete and re-enroll" variant="destructive" loading={resetEnrollment.isPending} onPress={reEnroll} />
          <Button label="Cancel" variant="ghost" onPress={() => setIsConfirming(false)} />
        </Card>
      )}

      <Button label="Sign out" variant="secondary" onPress={logout} />
    </Screen>
  );
}
