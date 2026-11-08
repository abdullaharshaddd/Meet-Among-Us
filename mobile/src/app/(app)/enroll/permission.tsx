import { useEffect, useState } from "react";
import { Linking, Platform, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { getRecordingPermissionsAsync, requestRecordingPermissionsAsync } from "expo-audio";
import { BilingualText, BottomDock, Button, Header, MeterStrip, Screen, Text } from "@/components/ui";
import { layout, space } from "@/theme/tokens";

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

  return (
    <Screen>
      <Header onBack={() => router.back()} />

      <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.lg }}>
        <MeterStrip />

        {isBlocked ? (
          <>
            <BilingualText variant="displayLg">Microphone is turned off</BilingualText>
            <Text variant="body" tone="secondary">
              {Platform.OS === "web"
                ? "Your browser is blocking the microphone. Click the lock icon next to the address bar, allow the microphone, then check again."
                : "Voice enrollment cannot work without the microphone. Open Settings, allow the microphone for this app, then come back and check again."}
            </Text>
          </>
        ) : (
          <>
            <BilingualText variant="displayLg">We need your microphone</BilingualText>
            <Text variant="body" tone="secondary">
              To record your voice we need to use the microphone. Next, your phone will ask for permission.
            </Text>
            <Text variant="body" tone="secondary">
              The microphone is only on while you are recording a passage.
            </Text>
          </>
        )}
      </View>

      <BottomDock aboveTabBar={false}>
        <View style={{ gap: space.sm }}>
          {isBlocked ? (
            <>
              {Platform.OS !== "web" && <Button label="Open settings" size="dock" onPress={() => Linking.openSettings()} />}
              <Button label="Check again" size="dock" variant="secondary" onPress={askForPermission} />
            </>
          ) : (
            <Button label="Allow microphone" size="dock" onPress={askForPermission} />
          )}
        </View>
      </BottomDock>
    </Screen>
  );
}
