import { useState } from "react";
import { View } from "react-native";
import { GoogleSignin, isSuccessResponse } from "@react-native-google-signin/google-signin";
import { Button, Text } from "@/components/ui";
import { space } from "@/theme/tokens";

// Asks Google again and hands back a fresh ID token, without creating a new session. Used to confirm it is really
// the person before something permanent, for an account that signed up with Google.
export function GoogleReauthButton({ onToken, disabled }: { onToken: (idToken: string) => void; disabled?: boolean }) {
  const [error, setError] = useState<string | null>(null);

  const onPress = async () => {
    setError(null);

    try {
      await GoogleSignin.hasPlayServices();
      const response = await GoogleSignin.signIn();

      if (!isSuccessResponse(response)) return;

      if (response.data.idToken) onToken(response.data.idToken);
      else setError("Google didn't return a token. Try again.");
    } catch {
      setError("Google sign-in failed. Try again.");
    }
  };

  return (
    <View style={{ gap: space.xs }}>
      <Button label="Confirm with Google" variant="secondary" disabled={disabled} onPress={onPress} />
      {error && (
        <Text variant="caption" tone="danger">
          {error}
        </Text>
      )}
    </View>
  );
}
