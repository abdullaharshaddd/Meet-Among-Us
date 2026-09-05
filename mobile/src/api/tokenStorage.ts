import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

const ACCESS_KEY = "meetamongus.accessToken";
const REFRESH_KEY = "meetamongus.refreshToken";

// expo-secure-store has no web implementation and throws there — this repo
// gets tested via `expo start --web` during development, so web silently
// behaves as "always logged out" instead of crashing.
const isWeb = Platform.OS === "web";

export const tokenStorage = {
  async load(): Promise<{ accessToken: string | null; refreshToken: string | null }> {
    if (isWeb) return { accessToken: null, refreshToken: null };
    const [accessToken, refreshToken] = await Promise.all([
      SecureStore.getItemAsync(ACCESS_KEY),
      SecureStore.getItemAsync(REFRESH_KEY),
    ]);
    return { accessToken, refreshToken };
  },

  async save(accessToken: string, refreshToken: string): Promise<void> {
    if (isWeb) return;
    await Promise.all([
      SecureStore.setItemAsync(ACCESS_KEY, accessToken),
      SecureStore.setItemAsync(REFRESH_KEY, refreshToken),
    ]);
  },

  async clear(): Promise<void> {
    if (isWeb) return;
    await Promise.all([SecureStore.deleteItemAsync(ACCESS_KEY), SecureStore.deleteItemAsync(REFRESH_KEY)]);
  },
};
