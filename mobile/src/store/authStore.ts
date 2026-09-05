import { create } from "zustand";
import { tokenStorage } from "@/api/tokenStorage";
import type { CurrentUserResponse } from "@/api/authTypes";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  // Populated from whatever login/signup/Google sign-in already returns.
  // Not persisted — there's no GET /auth/me yet to refetch it on cold
  // start, so this resets to null on app relaunch until that lands.
  user: CurrentUserResponse | null;
  isHydrated: boolean;
  hydrate: () => Promise<void>;
  setSession: (accessToken: string, refreshToken: string, user?: CurrentUserResponse) => void;
  clearTokens: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isHydrated: false,

  hydrate: async () => {
    const { accessToken, refreshToken } = await tokenStorage.load();
    set({ accessToken, refreshToken, isHydrated: true });
  },

  setSession: (accessToken, refreshToken, user) => {
    tokenStorage.save(accessToken, refreshToken); // fire-and-forget persist
    set((state) => ({ accessToken, refreshToken, user: user ?? state.user }));
  },

  clearTokens: () => {
    tokenStorage.clear();
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));
