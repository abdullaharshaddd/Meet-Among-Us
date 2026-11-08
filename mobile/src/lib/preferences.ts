import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

// Small settings that should survive a restart, like the chosen theme. Not for secrets:
// those go through api/tokenStorage. SecureStore is what is installed, and the web has localStorage.
export const preferences = {
  async get(key: string): Promise<string | null> {
    try {
      if (Platform.OS === "web") return window.localStorage.getItem(key);

      return await SecureStore.getItemAsync(key);
    } catch {
      return null;
    }
  },

  async set(key: string, value: string): Promise<void> {
    try {
      if (Platform.OS === "web") {
        window.localStorage.setItem(key, value);
        return;
      }

      await SecureStore.setItemAsync(key, value);
    } catch {
      // A preference that fails to save is not worth interrupting anyone for.
    }
  },
};
