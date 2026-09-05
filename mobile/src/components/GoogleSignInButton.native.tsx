import { useState } from "react";
import { View } from "react-native";
import { GoogleSignin, isErrorWithCode, isSuccessResponse, statusCodes } from "@react-native-google-signin/google-signin";
import { GOOGLE_CLIENT_ID_WEB } from "@/config/env";
import { useGoogleSignIn } from "@/api/auth";
import { space } from "@/theme/tokens";
import { Button } from "./Button";
import { Text } from "./Text";

if (!GOOGLE_CLIENT_ID_WEB) {
  console.warn("EXPO_PUBLIC_GOOGLE_CLIENT_ID_WEB is not set — Google Sign-In will fail to configure.");
}

// Configured once at module scope — this file is Google Sign-In's only
// consumer, so setup lives next to its use rather than in the root layout.
// `webClientId` (not an Android client ID) is what makes Google mint the ID
// token audienced to the web client even on Android — see
// docs/adr/0003-own-jwt-not-supabase-auth.md on the backend.
GoogleSignin.configure({ webClientId: GOOGLE_CLIENT_ID_WEB });

export function GoogleSignInButton() {
  const googleSignIn = useGoogleSignIn();
  const [localError, setLocalError] = useState<string | null>(null);

  const onPress = async () => {
    setLocalError(null);
    try {
      await GoogleSignin.hasPlayServices();
      const response = await GoogleSignin.signIn();
      if (!isSuccessResponse(response)) return; // user cancelled — not an error

      if (!response.data.idToken) {
        setLocalError("Google didn't return a sign-in token. Try again.");
        return;
      }
      await googleSignIn.mutateAsync(response.data.idToken);
    } catch (err) {
      if (isErrorWithCode(err) && err.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        setLocalError("Google Play Services isn't available on this device.");
        return;
      }
      setLocalError("Google Sign-In failed. Try again.");
    }
  };

  return (
    <View style={{ gap: space.xs }}>
      <Button label="Continue with Google" variant="secondary" loading={googleSignIn.isPending} onPress={onPress} />
      {localError && (
        <Text variant="caption" tone="danger">
          {localError}
        </Text>
      )}
    </View>
  );
}
