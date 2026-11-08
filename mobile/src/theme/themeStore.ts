import { create } from "zustand";
import { preferences } from "@/lib/preferences";
import type { Scheme } from "./tokens";

const THEME_KEY = "meetamongus.theme";

interface ThemeStore {
  // null means "follow the phone's setting".
  override: Scheme | null;
  setOverride: (scheme: Scheme | null) => void;
  hydrate: () => Promise<void>;
}

export const useThemeStore = create<ThemeStore>((set) => ({
  override: null,

  setOverride: (override) => {
    set({ override });
    preferences.set(THEME_KEY, override ?? "system");
  },

  hydrate: async () => {
    const saved = await preferences.get(THEME_KEY);

    if (saved === "light" || saved === "dark") set({ override: saved });
  },
}));
