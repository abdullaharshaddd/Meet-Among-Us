import { useEffect } from "react";
import { View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { useAudioPlayer, useAudioPlayerStatus } from "expo-audio";
import { Screen, Text, Button } from "@/components";
import { findPassage } from "@/lib/enrollmentPassages";
import { useEnrollmentDraftStore } from "@/store/enrollmentDraftStore";
import { space } from "@/theme/tokens";

export default function ReviewRecordingScreen() {
  const router = useRouter();
  const language = useEnrollmentDraftStore((state) => state.language);
  const fileUri = useEnrollmentDraftStore((state) => state.fileUri);

  const player = useAudioPlayer(fileUri);
  const playerStatus = useAudioPlayerStatus(player);

  // The player stays at the end after playing, so rewind or the next press does nothing.
  useEffect(() => {
    if (playerStatus.didJustFinish) player.seekTo(0);
  }, [playerStatus.didJustFinish]);

  const passage = findPassage(language ?? undefined);

  if (!passage || !fileUri) {
    return <Redirect href="/(app)/enroll" />;
  }

  const togglePlayback = () => {
    if (playerStatus.playing) {
      player.pause();
      return;
    }

    player.play();
  };

  const recordAgain = () => {
    player.pause();
    router.replace(`/(app)/enroll/record/${passage.language}`);
  };

  const useRecording = () => {
    player.pause();
    router.push("/(app)/enroll/result");
  };

  return (
    <Screen style={{ gap: space.lg }}>
      <Text variant="title">Listen back</Text>
      <Text variant="body" tone="secondary">
        Check that your voice is clear and you read the whole {passage.title} passage. You can record it again if not.
      </Text>

      <Button label={playerStatus.playing ? "Pause" : "Play recording"} variant="secondary" onPress={togglePlayback} />

      <View style={{ flex: 1 }} />

      <View style={{ gap: space.sm }}>
        <Button label="Use this recording" onPress={useRecording} />
        <Button label="Record again" variant="secondary" onPress={recordAgain} />
      </View>
    </Screen>
  );
}
