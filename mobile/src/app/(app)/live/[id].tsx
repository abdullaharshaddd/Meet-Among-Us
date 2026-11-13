import { View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Button, EmptyState, Header, Screen } from "@/components/ui";
import { layout } from "@/theme/tokens";

// Recording is built by a teammate (docs/handoff/recording-upload.md). Until it lands this screen says so, and shows
// no timer, level meter or sync numbers, since none of them would be real.
export default function RecordingPlaceholderScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  return (
    <Screen>
      <Header title="Recording" onBack={() => router.back()} />

      <View style={{ paddingHorizontal: layout.screenGutter, gap: layout.sectionGap }}>
        <EmptyState
          title="Recording is being built"
          description="This screen will record the meeting from your microphone and upload it. It isn't ready yet. Until it is, the developers can attach a recording to this meeting by script, and it is processed the same way."
        />
        <Button label="Back to the meeting" variant="secondary" onPress={() => router.replace({ pathname: "/(app)/meetings/[id]", params: { id } })} />
      </View>
    </Screen>
  );
}
