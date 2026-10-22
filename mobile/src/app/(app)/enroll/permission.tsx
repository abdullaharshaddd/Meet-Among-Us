import { useEffect, useState } from "react";
import { Linking, Platform, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { getRecordingPermissionsAsync, requestRecordingPermissionsAsync } from "expo-audio";
import { Screen, Text, Button } from "@/components";
import { space } from "@/theme/tokens";

export default function MicrophonePermissionScreen() {
  const { language } = useLocalSearchParams<{ language: string }>();
  const router = useRouter();
  const [isBlocked, setIsBlocked] = useState(false);

  const goToRecording = () => router.replace(`/(app)/enroll/record/${language ?? "en"}`);

  useEffect(() => {
    getRecordingPermissionsAsync().then((permission) => {
      if (permission.granted) goToRecording();
      if (!permission.granted && !permission.canAskAgain) setIsBlocked(true);
    });
  }, []);

  const askForPermission = async () => {
    const permission = await requestRecordingPermissionsAsync();

    if (permission.granted) {
      goToRecording();
      return;
    }

    setIsBlocked(true);
  };

  if (isBlocked) {
    return (
      <Screen style={{ gap: space.lg, justifyContent: "center" }}>
        <Text variant="title">Microphone is turned off</Text>
        <Text variant="body" tone="secondary">
          {Platform.OS === "web"
            ? "Your browser is blocking the microphone. Click the lock icon next to the address bar, allow the microphone, then check again."
            : "Voice enrollment cannot work without the microphone. Open Settings, allow the microphone for this app, then come back and check again."}
        </Text>
        {Platform.OS !== "web" && <Button label="Open settings" onPress={() => Linking.openSettings()} />}
        <Button label="Check again" variant="secondary" onPress={askForPermission} />
      </Screen>
    );
  }

  return (
    <Screen style={{ gap: space.lg, justifyContent: "center" }}>
      <Text variant="title">We need your microphone</Text>
      <View style={{ gap: space.sm }}>
        <Text variant="body" tone="secondary">
          To record your voice we need to use the microphone. Next, your phone will ask for permission.
        </Text>
        <Text variant="body" tone="secondary">The microphone is only on while you are recording a passage.</Text>
      </View>
      <Button label="Allow microphone" onPress={askForPermission} />
    </Screen>
  );
}
