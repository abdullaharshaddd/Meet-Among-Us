import { useEffect } from "react";
import { View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { useAudioPlayer, useAudioPlayerStatus } from "expo-audio";
import { BilingualText, BottomDock, Button, CircleButton, Header, Screen, Text } from "@/components/ui";
import { findPassage } from "@/lib/enrollmentPassages";
import { useEnrollmentDraftStore } from "@/store/enrollmentDraftStore";
import { layout, space } from "@/theme/tokens";

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
    <Screen>
      <Header onBack={recordAgain} />

      <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.lg }}>
        <BilingualText variant="displayLg">Listen back</BilingualText>
        <Text variant="body" tone="secondary">
          Check that your voice is clear and you read the whole {passage.title} passage. You can record it again if not.
        </Text>
      </View>

      <BottomDock aboveTabBar={false}>
        <View style={{ gap: space.sm }}>
          <View style={{ flexDirection: "row", alignItems: "flex-start", gap: space.lg }}>
            <CircleButton
              icon={playerStatus.playing ? "pause" : "play"}
              label={playerStatus.playing ? "Pause" : "Replay"}
              onPress={togglePlayback}
            />
            <View style={{ flex: 1 }}>
              <Button label="Use this recording" size="dock" onPress={useRecording} />
            </View>
          </View>
          <Button label="Record again" variant="ghost" onPress={recordAgain} />
        </View>
      </BottomDock>
    </Screen>
  );
}
