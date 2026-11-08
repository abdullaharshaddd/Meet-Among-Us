import { useEffect, useRef, useState } from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import {
  getRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from "expo-audio";
import {
  AudioLevelMeter,
  BilingualText,
  Badge,
  BottomDock,
  Card,
  CircleButton,
  Header,
  RecordButton,
  Screen,
  Text,
  useDockClearance,
} from "@/components/ui";
import { EnrollProgress } from "@/features/enrollment/EnrollProgress";
import { findPassage, minSpeechSeconds, passageNumber, passages } from "@/lib/enrollmentPassages";
import { playHaptic } from "@/lib/haptics";
import { enrollmentRecordingOptions, formatSeconds, meteringToLevel } from "@/lib/recording";
import { useEnrollmentDraftStore } from "@/store/enrollmentDraftStore";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, radii, sizes, space } from "@/theme/tokens";

const SAVE_ERROR = "The recording could not be saved. Please record this passage again.";

// Decibels below full scale. Louder than this clips, quieter than this is hard to hear.
const TOO_LOUD_DB = -3;
const TOO_QUIET_DB = -45;

export default function RecordPassageScreen() {
  const { language } = useLocalSearchParams<{ language: string }>();
  const passage = findPassage(language);
  const router = useRouter();
  const { colors } = useTheme();
  const dockClearance = useDockClearance(false);

  const recorder = useAudioRecorder(enrollmentRecordingOptions);
  const recorderState = useAudioRecorderState(recorder, 100);
  const setRecording = useEnrollmentDraftStore((state) => state.setRecording);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    getRecordingPermissionsAsync().then((permission) => {
      if (!permission.granted) router.replace(`/(app)/enroll/permission?language=${language}`);
    });
  }, []);

  const isRecording = recorderState.isRecording;
  const reachedTarget = recorderState.durationMillis >= minSpeechSeconds * 1000;

  // One buzz the moment the passage is long enough, not on every update after it.
  const hasBuzzed = useRef(false);
  useEffect(() => {
    if (reachedTarget && !hasBuzzed.current) {
      hasBuzzed.current = true;
      playHaptic("qualityPass");
    }

    if (!isRecording && !reachedTarget) hasBuzzed.current = false;
  }, [reachedTarget, isRecording]);

  if (!passage) {
    return (
      <Screen>
        <Header onBack={() => router.back()} />
        <View style={{ padding: layout.screenGutter }}>
          <Text variant="body" tone="secondary">That passage does not exist.</Text>
        </View>
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

  const decibels = recorderState.metering;
  const level =
    !isRecording || decibels === undefined
      ? { label: "Ready", variant: "outline" as const }
      : decibels > TOO_LOUD_DB
        ? { label: "Too loud", variant: "danger" as const }
        : decibels < TOO_QUIET_DB
          ? { label: "Too quiet", variant: "warning" as const }
          : { label: "Good level", variant: "success" as const };

  return (
    <Screen>
      <Header onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.md, paddingBottom: dockClearance + sizes.recordButton, gap: layout.sectionGap }}>
        <EnrollProgress step={passageNumber(passage.language)} total={passages.length} title={passage.title} />

        <View style={{ gap: space.md }}>
          <Text variant="callout" tone="secondary">
            Read this out loud at your normal pace.
          </Text>
          <Card>
            <BilingualText variant="title" direction={passage.isUrdu ? "rtl" : "ltr"}>
              {passage.text}
            </BilingualText>
          </Card>
        </View>

        <View style={{ gap: space.md }}>
          <View style={{ padding: space.lg, borderRadius: radii.md, backgroundColor: colors.sunken, gap: space.md }}>
            <AudioLevelMeter level={meteringToLevel(decibels)} state={isRecording ? "capturing" : "idle"} />

            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <Text variant="mono" tone="secondary">
                {decibels === undefined || !isRecording ? "— dB" : `${Math.round(decibels)} dB`}
              </Text>
              <Badge label={level.label} variant={level.variant} />
            </View>
          </View>

          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <Text variant="mono" tone={reachedTarget ? "success" : isRecording ? "signal" : "secondary"}>
              {formatSeconds(recorderState.durationMillis)} / {minSpeechSeconds.toFixed(1)}s
            </Text>
            <Text variant="caption" tone={reachedTarget ? "success" : "secondary"}>
              {reachedTarget ? "Long enough. Finish, then stop." : `Keep reading for at least ${minSpeechSeconds} seconds.`}
            </Text>
          </View>
        </View>

        {errorMessage && <Text variant="callout" tone="danger">{errorMessage}</Text>}
      </ScrollView>

      <BottomDock aboveTabBar={false}>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <View style={{ width: sizes.stopButton, alignItems: "center" }}>
            {isRecording && <CircleButton icon="replay" label="Restart" onPress={startOver} />}
          </View>

          <RecordButton isRecording={isRecording} onPress={isRecording ? stopRecording : startRecording} />

          <View style={{ width: sizes.stopButton }} />
        </View>
      </BottomDock>
    </Screen>
  );
}
