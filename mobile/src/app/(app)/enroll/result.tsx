import { useEffect, useRef, useState } from "react";
import { View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { BilingualText, BottomDock, Button, Header, Icon, LoadingDots, MeterStrip, Screen, Text } from "@/components/ui";
import {
  useEnrollmentStatus,
  useRequestUploadUrl,
  useSubmitSample,
  useUploadRecording,
  type SubmitSampleResponse,
} from "@/api/enrollment";
import { EnrollProgress } from "@/features/enrollment/EnrollProgress";
import { findPassage, passageNumber, passages } from "@/lib/enrollmentPassages";
import { playHaptic } from "@/lib/haptics";
import { useEnrollmentDraftStore } from "@/store/enrollmentDraftStore";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, space } from "@/theme/tokens";

type Phase = "sending" | "failed" | "done";

export default function EnrollmentResultScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const language = useEnrollmentDraftStore((state) => state.language);
  const fileUri = useEnrollmentDraftStore((state) => state.fileUri);
  const clearRecording = useEnrollmentDraftStore((state) => state.clearRecording);

  const requestUploadUrl = useRequestUploadUrl();
  const uploadRecording = useUploadRecording();
  const submitSample = useSubmitSample();
  const { data: status } = useEnrollmentStatus();

  const [phase, setPhase] = useState<Phase>("sending");
  const [outcome, setOutcome] = useState<SubmitSampleResponse | null>(null);
  const [failureMessage, setFailureMessage] = useState("");
  const hasStarted = useRef(false);

  const passage = findPassage(language ?? undefined);

  const sendRecording = async () => {
    if (!language || !fileUri) return;

    setPhase("sending");

    try {
      const upload = await requestUploadUrl.mutateAsync(language);
      await uploadRecording.mutateAsync({ uploadUrl: upload.upload_url, fileUri });
      const result = await submitSample.mutateAsync({ language, audioKey: upload.audio_key });

      setOutcome(result);
      setPhase("done");

      if (result.accepted) playHaptic("qualityPass");
    } catch (error) {
      setFailureMessage(error instanceof Error ? error.message : "");
      setPhase("failed");
    }
  };

  // The ref stops React's dev-mode double effect from uploading the same file twice.
  useEffect(() => {
    if (hasStarted.current) return;

    hasStarted.current = true;
    sendRecording();
  }, []);

  if (!passage || !fileUri) {
    return <Redirect href="/(app)/enroll" />;
  }

  const progress = <EnrollProgress step={passageNumber(passage.language)} total={passages.length} title={passage.title} />;

  if (phase === "sending") {
    return (
      <Screen>
        <Header />
        <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.md, gap: space["3xl"] }}>
          {progress}
          <View style={{ gap: space.lg }}>
            <MeterStrip />
            <BilingualText variant="displayLg">Checking your recording</BilingualText>
            <LoadingDots color={colors.textSecondary} />
          </View>
        </View>
      </Screen>
    );
  }

  if (phase === "failed" || !outcome) {
    const detail = failureMessage ? ` (${failureMessage})` : "";

    return (
      <Screen>
        <Header />
        <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.md, gap: space["3xl"] }}>
          {progress}
          <View style={{ gap: space.md }}>
            <BilingualText variant="displayLg">Upload failed</BilingualText>
            <Text variant="body" tone="secondary">
              We couldn't send your recording. Check your connection and try again.{detail}
            </Text>
          </View>
        </View>

        <BottomDock aboveTabBar={false}>
          <Button label="Try again" size="dock" onPress={sendRecording} />
        </BottomDock>
      </Screen>
    );
  }

  if (!outcome.accepted) {
    const recordAgain = () => {
      clearRecording();
      router.replace(`/(app)/enroll/record/${passage.language}`);
    };

    return (
      <Screen>
        <Header onBack={recordAgain} />
        <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.md, gap: space["3xl"] }}>
          {progress}
          <View style={{ gap: space.md }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
              <Icon name="warning" size="md" color={colors.warning} />
              <Text variant="label" tone="warning">
                Not accepted
              </Text>
            </View>
            <BilingualText variant="displayLg">Let's try that again</BilingualText>
            <Text variant="body">{outcome.reason_message ?? "This recording wasn't accepted."}</Text>
            {outcome.enrollment_status === "failed" && (
              <Text variant="callout" tone="secondary">
                Still not working? Move somewhere quiet and hold your phone about a hand's width from your mouth.
              </Text>
            )}
          </View>
        </View>

        <BottomDock aboveTabBar={false}>
          <Button label="Try again" size="dock" onPress={recordAgain} />
        </BottomDock>
      </Screen>
    );
  }

  const nextPassage = passages.find(
    (item) =>
      item.language !== passage.language &&
      status?.passages.find((entry) => entry.language === item.language)?.state !== "accepted",
  );
  const isFinished = outcome.enrollment_status === "complete" || !nextPassage;

  const goNext = () => {
    clearRecording();

    if (isFinished || !nextPassage) {
      router.replace("/(app)/enroll/done");
      return;
    }

    router.replace(`/(app)/enroll/record/${nextPassage.language}`);
  };

  return (
    <Screen>
      <Header />
      <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.md, gap: space["3xl"] }}>
        {progress}
        <View style={{ gap: space.md }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
            <Icon name="check" size="md" color={colors.success} />
            <Text variant="label" tone="success">
              Accepted
            </Text>
          </View>
          <BilingualText variant="displayLg">
            {`Passage ${passageNumber(passage.language)} of ${passages.length} accepted`}
          </BilingualText>
          <Text variant="body" tone="secondary">
            {isFinished || !nextPassage ? "That was the last one." : `Next up: the ${nextPassage.title} passage.`}
          </Text>
        </View>
      </View>

      <BottomDock aboveTabBar={false}>
        <Button label={isFinished ? "Finish" : "Next passage →"} size="dock" onPress={goNext} />
      </BottomDock>
    </Screen>
  );
}
