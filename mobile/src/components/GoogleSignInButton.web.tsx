import { View } from "react-native";
import { space } from "@/theme/tokens";
import { Button } from "./Button";
import { Text } from "./Text";

// @react-native-google-signin/google-signin is a native module with no web
// implementation — this stub keeps the layout consistent on web (used only
// for dev-time preview here) without pulling the package into the web
// bundle. The real target is the Android dev client — see Task 4.
export function GoogleSignInButton() {
  return (
    <View style={{ gap: space.xs }}>
      <Button label="Continue with Google" variant="secondary" disabled />
      <Text variant="caption" tone="tertiary">
        Available in the Android app.
      </Text>
    </View>
  );
}
