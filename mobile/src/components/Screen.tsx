import { SafeAreaView } from "react-native-safe-area-context";
import { StyleSheet, type ViewProps } from "react-native";
import { colors, space } from "@/theme/tokens";

// Every screen's canvas background + safe-area + padding, in one place
// instead of the same three style lines repeated per screen.
export function Screen({ style, ...props }: ViewProps) {
  return <SafeAreaView style={[styles.screen, style]} {...props} />;
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg.canvas,
    padding: space.lg,
  },
});
