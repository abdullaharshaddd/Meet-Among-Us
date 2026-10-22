import { useRouter } from "expo-router";
import { View } from "react-native";
import { Screen, Text, Card, Button, Badge, EmptyState } from "@/components";
import { useEnrollmentStatus, type EnrollmentStatus } from "@/api/enrollment";
import { passages } from "@/lib/enrollmentPassages";
import { useAuthStore } from "@/store/authStore";
import { space } from "@/theme/tokens";

const BADGES: Record<EnrollmentStatus, { label: string; variant: "neutral" | "uploading" | "success" | "warning" }> = {
  not_started: { label: "Not started", variant: "neutral" },
  in_progress: { label: "In progress", variant: "uploading" },
  complete: { label: "Enrolled", variant: "success" },
  failed: { label: "Needs another try", variant: "warning" },
};

const BUTTON_LABELS: Record<EnrollmentStatus, string> = {
  not_started: "Start enrollment",
  in_progress: "Continue enrollment",
  complete: "View enrollment",
  failed: "Try again",
};

export default function HomeScreen() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const { data: status } = useEnrollmentStatus();

  const acceptedCount = status?.passages.filter((passage) => passage.state === "accepted").length ?? 0;

  return (
    <Screen style={{ gap: space.lg }}>
      <Text variant="title">{user ? `Welcome, ${user.display_name}` : "Welcome back"}</Text>

      {status && (
        <Card style={{ gap: space.sm }}>
          <Text variant="heading">Voice enrollment</Text>
          <Badge label={BADGES[status.enrollment_status].label} variant={BADGES[status.enrollment_status].variant} />
          <Text variant="body" tone="secondary">
            {status.enrollment_status === "complete"
              ? "Meetings can recognize your voice."
              : `${acceptedCount} of ${passages.length} passages done. You can browse everything else in the meantime.`}
          </Text>
          <Button
            label={BUTTON_LABELS[status.enrollment_status]}
            variant="secondary"
            onPress={() => router.push("/(app)/enroll")}
          />
        </Card>
      )}

      <View style={{ flex: 1, justifyContent: "center" }}>
        <EmptyState glyph="▢" title="No workspaces yet" description="Create or join a workspace — coming in Phase 2." />
      </View>
    </Screen>
  );
}
