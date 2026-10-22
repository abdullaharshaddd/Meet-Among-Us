import { useEffect, useState } from "react";
import { View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import {
  getRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from "expo-audio";
import { Screen, Text, Mono, Urdu, Card, Button, AudioLevelMeter } from "@/components";
import { findPassage, passageNumber, passages } from "@/lib/enrollmentPassages";
import { enrollmentRecordingOptions, formatSeconds, meteringToLevel } from "@/lib/recording";
import { useEnrollmentDraftStore } from "@/store/enrollmentDraftStore";
import { space } from "@/theme/tokens";

const SAVE_ERROR = "The recording could not be saved. Please record this passage again.";

export default function RecordPassageScreen() {
  const { language } = useLocalSearchParams<{ language: string }>();
  const passage = findPassage(language);
  const router = useRouter();

  const recorder = useAudioRecorder(enrollmentRecordingOptions);
  const recorderState = useAudioRecorderState(recorder, 100);
  const setRecording = useEnrollmentDraftStore((state) => state.setRecording);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    getRecordingPermissionsAsync().then((permission) => {
      if (!permission.granted) router.replace(`/(app)/enroll/permission?language=${language}`);
    });
  }, []);

  if (!passage) {
    return (
      <Screen style={{ justifyContent: "center" }}>
        <Text variant="body" tone="secondary">That passage does not exist.</Text>
      </Screen>
    );
  }

  const startRecording = async () => {
    setErrorMessage(null);

    try {
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
    } catch {
      setErrorMessage("We couldn't start the microphone. Close other apps that use it and try again.");
    }
  };

  const stopRecording = async () => {
    try {
      await recorder.stop();
      await setAudioModeAsync({ allowsRecording: false });
    } catch {
      setErrorMessage(SAVE_ERROR);
      return;
    }

    if (!recorder.uri) {
      setErrorMessage(SAVE_ERROR);
      return;
    }

    setRecording(passage.language, recorder.uri);
    router.push("/(app)/enroll/review");
  };

  const startOver = async () => {
    await recorder.stop();
  };

  const isRecording = recorderState.isRecording;

  return (
    <Screen style={{ gap: space.lg }}>
      <View style={{ gap: space.xs }}>
        <Text variant="label" tone="secondary">
          Passage {passageNumber(passage.language)} of {passages.length} · {passage.title}
        </Text>
        <Text variant="body" tone="secondary">Read this out loud at your normal pace.</Text>
      </View>

      <Card style={{ gap: space.md }}>
        {passage.isUrdu ? <Urdu>{passage.text}</Urdu> : <Text variant="heading">{passage.text}</Text>}
      </Card>

      <View style={{ gap: space.sm }}>
        <AudioLevelMeter level={meteringToLevel(recorderState.metering)} state={isRecording ? "capturing" : "idle"} />
        <Mono tone={isRecording ? "recording" : "secondary"}>{formatSeconds(recorderState.durationMillis)}</Mono>
      </View>

      {errorMessage && <Text variant="body" tone="danger">{errorMessage}</Text>}

      <View style={{ flex: 1 }} />

      {isRecording ? (
        <View style={{ gap: space.sm }}>
          <Button label="Stop and review" onPress={stopRecording} />
          <Button label="Start over" variant="secondary" onPress={startOver} />
        </View>
      ) : (
        <Button label="Start recording" onPress={startRecording} />
      )}
    </Screen>
  );
}
