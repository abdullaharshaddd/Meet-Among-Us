import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/authStore";
import { api, unwrap } from "./client";
import type { LoginRequest, SignupRequest } from "./authTypes";

export function useSignup() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (body: SignupRequest) => unwrap(await api.POST("/auth/signup", { body })),
    onSuccess: (data) => setSession(data.access_token, data.refresh_token, data.user),
  });
}

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (body: LoginRequest) => unwrap(await api.POST("/auth/login", { body })),
    onSuccess: (data) => setSession(data.access_token, data.refresh_token, data.user),
  });
}

export function useGoogleSignIn() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (idToken: string) => unwrap(await api.POST("/auth/google", { body: { id_token: idToken } })),
    onSuccess: (data) => setSession(data.access_token, data.refresh_token, data.user),
  });
}

export function useLogout() {
  const clearTokens = useAuthStore((s) => s.clearTokens);
  const queryClient = useQueryClient();
  return () => {
    const { refreshToken } = useAuthStore.getState();
    if (refreshToken) {
      // Best-effort: revokes the token server-side so it can't be replayed,
      // but local logout must succeed even offline — nothing awaits this,
      // and a failure here is silent by design (see auth_service.logout).
      api.POST("/auth/logout", { body: { refresh_token: refreshToken } }).catch(() => {});
    }
    clearTokens();
    queryClient.clear(); // drop any cached server state tied to the old session
  };
}
