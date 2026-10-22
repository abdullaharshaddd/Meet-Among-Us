import { useEffect, useRef, useState } from "react";
import { View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { Screen, Text, Button, ErrorState, LoadingState } from "@/components";
import {
  useEnrollmentStatus,
  useRequestUploadUrl,
  useSubmitSample,
  useUploadRecording,
  type SubmitSampleResponse,
} from "@/api/enrollment";
import { findPassage, passageNumber, passages } from "@/lib/enrollmentPassages";
import { useEnrollmentDraftStore } from "@/store/enrollmentDraftStore";
import { space } from "@/theme/tokens";

type Phase = "sending" | "failed" | "done";

export default function EnrollmentResultScreen() {
  const router = useRouter();
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

  if (phase === "sending") {
    return (
      <Screen style={{ justifyContent: "center" }}>
        <LoadingState label="Checking your recording…" />
      </Screen>
    );
  }

  if (phase === "failed" || !outcome) {
    const detail = failureMessage ? `\n(${failureMessage})` : "";

    return (
      <Screen style={{ justifyContent: "center", gap: space.lg }}>
        <ErrorState
          title="Upload failed"
          description={`We couldn't send your recording. Check your connection and try again.${detail}`}
        />
        <Button label="Try again" onPress={sendRecording} />
      </Screen>
    );
  }

  if (!outcome.accepted) {
    const recordAgain = () => {
      clearRecording();
      router.replace(`/(app)/enroll/record/${passage.language}`);
    };

    return (
      <Screen style={{ gap: space.lg }}>
        <Text variant="title">Let's try that again</Text>
        <Text variant="body">{outcome.reason_message ?? "This recording wasn't accepted."}</Text>
        {outcome.enrollment_status === "failed" && (
          <Text variant="body" tone="secondary">
            Still not working? Move somewhere quiet and hold your phone about a hand's width from your mouth.
          </Text>
        )}
        <View style={{ flex: 1 }} />
        <Button label="Record again" onPress={recordAgain} />
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
    <Screen style={{ gap: space.lg }}>
      <Text variant="title" tone="success">
        Passage {passageNumber(passage.language)} of {passages.length} accepted
      </Text>
      <Text variant="body" tone="secondary">
        {isFinished || !nextPassage ? "That was the last one." : `Next up: the ${nextPassage.title} passage.`}
      </Text>
      <View style={{ flex: 1 }} />
      <Button label={isFinished ? "Finish" : "Next passage"} onPress={goNext} />
    </Screen>
  );
}
