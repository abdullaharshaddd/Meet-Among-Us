import { Redirect, useRouter } from "expo-router";
import { ScrollView, View } from "react-native";
import { BilingualText, BottomDock, Button, Card, Header, MeterStrip, Screen, Skeleton, Text, useDockClearance } from "@/components/ui";
import { useEnrollmentStatus } from "@/api/enrollment";
import { passages } from "@/lib/enrollmentPassages";
import { layout, space } from "@/theme/tokens";

export default function EnrollIntroScreen() {
  const router = useRouter();
  const { data: status, isLoading, isError, refetch } = useEnrollmentStatus();
  const dockClearance = useDockClearance(false);

  if (isLoading) {
    return (
      <Screen>
        <Header onBack={() => router.back()} />
        <View style={{ padding: layout.screenGutter, gap: space.md }}>
          <Skeleton height={space["4xl"]} width="70%" />
          <Skeleton height={space.lg} />
          <Skeleton height={space.lg} width="80%" />
        </View>
      </Screen>
    );
  }

  if (isError || !status) {
    return (
      <Screen>
        <Header onBack={() => router.back()} />
        <View style={{ padding: layout.screenGutter, gap: space.lg }}>
          <BilingualText variant="displayMd">Couldn't load your enrollment</BilingualText>
          <Text variant="callout" tone="secondary">
            We couldn't load your enrollment status. Check your connection.
          </Text>
          <Button label="Try again" onPress={() => refetch()} />
        </View>
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
    <Screen>
      <Header onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: dockClearance, gap: layout.sectionGap }}>
        <View style={{ gap: space.lg }}>
          <MeterStrip />
          <BilingualText variant="displayLg">Set up your voice</BilingualText>
          <Text variant="body" tone="secondary">
            You will read three short passages out loud: one in English, one in Urdu, and one that mixes both. It takes about two minutes.
          </Text>
        </View>

        <Card style={{ gap: space.lg }}>
          <View style={{ gap: space.xs }}>
            <Text variant="label" tone="secondary">
              What we keep
            </Text>
            <Text variant="body">
              A voiceprint: a list of numbers that describes how your voice sounds. The numbers cannot be turned back into audio. We also keep your three practice recordings, private to your account, until you delete your voiceprint.
            </Text>
          </View>
          <View style={{ gap: space.xs }}>
            <Text variant="label" tone="secondary">
              What it is for
            </Text>
            <Text variant="body">
              Labelling who spoke in your meetings, so the transcript shows your name next to your words.
            </Text>
          </View>
          <View style={{ gap: space.xs }}>
            <Text variant="label" tone="secondary">
              Your control
            </Text>
            <Text variant="body">You can delete your voiceprint at any time from Settings.</Text>
          </View>
        </Card>

        {isStarted && (
          <Text variant="label" tone="secondary">
            {acceptedCount} of {passages.length} passages done
          </Text>
        )}
      </ScrollView>

      <BottomDock aboveTabBar={false}>
        <Button
          label={isStarted ? "Continue" : "Start"}
          size="dock"
          onPress={() => router.push(`/(app)/enroll/record/${nextPassage?.language ?? "en"}`)}
        />
      </BottomDock>
    </Screen>
  );
}
