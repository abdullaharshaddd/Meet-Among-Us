import { useRouter } from "expo-router";
import { View } from "react-native";
import { Screen, Text, Button } from "@/components";
import { space } from "@/theme/tokens";

export default function EnrollmentDoneScreen() {
  const router = useRouter();

  return (
    <Screen style={{ gap: space.lg, justifyContent: "center" }}>
      <View style={{ gap: space.sm }}>
        <Text variant="title" tone="success">You're enrolled</Text>
        <Text variant="body" tone="secondary">
          Your voiceprint is saved. In meetings, your words will be labelled with your name. You can delete it any time from Settings.
        </Text>
      </View>
      <Button label="Back to home" onPress={() => router.replace("/(app)")} />
    </Screen>
  );
}
