import { Platform } from "react-native";
import { motion } from "@/theme/tokens";

export type HapticKind =
  | "recordStart"
  | "recordStop"
  | "pauseResume"
  | "selection"
  | "confirm"
  | "destructive"
  | "qualityPass";

type HapticsModule = typeof import("expo-haptics");

let haptics: HapticsModule | null | undefined;

// Loaded on first use instead of imported at the top. A development build made
// before expo-haptics was added doesn't contain the native half, and importing
// it there would crash the whole app on start. This way it just stays silent.
function loadHaptics(): HapticsModule | null {
  if (Platform.OS === "web") return null;

  if (haptics === undefined) {
    try {
      haptics = require("expo-haptics") as HapticsModule;
    } catch {
      haptics = null;
    }
  }

  return haptics;
}

const quietly = (result: Promise<void>) => result.catch(() => {});

export function playHaptic(kind: HapticKind) {
  const module = loadHaptics();
  if (!module) return;

  switch (kind) {
    case "recordStart":
      quietly(module.impactAsync(module.ImpactFeedbackStyle.Heavy));
      setTimeout(() => quietly(module.notificationAsync(module.NotificationFeedbackType.Success)), motion.duration.hapticGap);
      break;
    case "recordStop":
      quietly(module.impactAsync(module.ImpactFeedbackStyle.Medium));
      break;
    case "pauseResume":
      quietly(module.impactAsync(module.ImpactFeedbackStyle.Light));
      break;
    case "selection":
      quietly(module.selectionAsync());
      break;
    case "confirm":
    case "qualityPass":
      quietly(module.notificationAsync(module.NotificationFeedbackType.Success));
      break;
    case "destructive":
      quietly(module.notificationAsync(module.NotificationFeedbackType.Warning));
      break;
  }
}
