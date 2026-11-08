import { useRouter } from "expo-router";
import { View } from "react-native";
import { BilingualText, BottomDock, Button, MeterStrip, Screen, Text } from "@/components/ui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { layout, space } from "@/theme/tokens";

export default function EnrollmentDoneScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  return (
    <Screen>
      <View style={{ flex: 1, justifyContent: "center", paddingHorizontal: layout.screenGutter, paddingTop: insets.top, gap: space.lg }}>
        <MeterStrip />
        <BilingualText variant="displayLg">You're enrolled</BilingualText>
        <Text variant="body" tone="secondary">
          Your voiceprint is saved. In meetings, your words will be labelled with your name. You can delete it any time from Settings.
        </Text>
      </View>

      <BottomDock aboveTabBar={false}>
        <Button label="Back to meetings" size="dock" onPress={() => router.replace("/(app)/meetings")} />
      </BottomDock>
    </Screen>
  );
}
