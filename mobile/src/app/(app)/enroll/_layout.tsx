import { Stack } from "expo-router";
import { colors } from "@/theme/legacy";

export default function EnrollLayout() {
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg.canvas } }} />;
}
