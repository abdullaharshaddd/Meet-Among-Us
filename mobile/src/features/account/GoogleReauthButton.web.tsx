import { View } from "react-native";
import { Button, Text } from "@/components/ui";
import { space } from "@/theme/tokens";

// Google sign-in is a native module with no web version, the same as the login button.
export function GoogleReauthButton({ disabled }: { onToken: (idToken: string) => void; disabled?: boolean }) {
  return (
    <View style={{ gap: space.xs }}>
      <Button label="Confirm with Google" variant="secondary" disabled />
      <Text variant="caption" tone="secondary">
        Confirming with Google is available in the Android app. On the web, use your password.
      </Text>
    </View>
  );
}
