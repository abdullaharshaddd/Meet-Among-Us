import { Redirect, useRouter } from "expo-router";
import { View } from "react-native";
import { Screen, Text, Card, Button, ErrorState, LoadingState } from "@/components";
import { useEnrollmentStatus } from "@/api/enrollment";
import { passages } from "@/lib/enrollmentPassages";
import { space } from "@/theme/tokens";

export default function EnrollIntroScreen() {
  const router = useRouter();
  const { data: status, isLoading, isError, refetch } = useEnrollmentStatus();

  if (isLoading) {
    return (
      <Screen style={{ justifyContent: "center" }}>
        <LoadingState />
      </Screen>
    );
  }

  if (isError || !status) {
    return (
      <Screen style={{ justifyContent: "center" }}>
        <ErrorState description="We couldn't load your enrollment status. Check your connection." onRetry={refetch} />
      </Screen>
    );
  }

  if (status.enrollment_status === "complete") {
    return <Redirect href="/(app)/enroll/done" />;
  }

  const acceptedCount = status.passages.filter((passage) => passage.state === "accepted").length;
  const nextPassage = passages.find(
    (passage) => status.passages.find((item) => item.language === passage.language)?.state !== "accepted",
  );
  const isStarted = acceptedCount > 0;

  return (
    <Screen style={{ gap: space.lg }}>
      <Text variant="title">Set up your voice</Text>
      <Text variant="body" tone="secondary">
        You will read three short passages out loud: one in English, one in Urdu, and one that mixes both. It takes about two minutes.
      </Text>

      <Card style={{ gap: space.md }}>
        <View style={{ gap: space.xs }}>
          <Text variant="bodyStrong">What we keep</Text>
          <Text variant="body" tone="secondary">
            A voiceprint: a list of numbers that describes how your voice sounds. The numbers cannot be turned back into audio. We also keep your three practice recordings, private to your account, until you delete your voiceprint.
          </Text>
        </View>
        <View style={{ gap: space.xs }}>
          <Text variant="bodyStrong">What it is for</Text>
          <Text variant="body" tone="secondary">
            Labelling who spoke in your meetings, so the transcript shows your name next to your words.
          </Text>
        </View>
        <View style={{ gap: space.xs }}>
          <Text variant="bodyStrong">Your control</Text>
          <Text variant="body" tone="secondary">You can delete your voiceprint at any time from Settings.</Text>
        </View>
      </Card>

      {isStarted && (
        <Text variant="label" tone="secondary">
          {acceptedCount} of {passages.length} passages done
        </Text>
      )}

      <View style={{ flex: 1 }} />

      <Button
        label={isStarted ? "Continue" : "Start"}
        onPress={() => router.push(`/(app)/enroll/record/${nextPassage?.language ?? "en"}`)}
      />
    </Screen>
  );
}
