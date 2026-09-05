import { Redirect, Stack } from "expo-router";
import { useAuthStore } from "@/store/authStore";

// The mirror of (app)/_layout.tsx's guard: once login/signup/Google
// sign-in sets a session, this redirects you into (app) automatically —
// no screen has to call router.replace by hand.
export default function AuthLayout() {
  const accessToken = useAuthStore((s) => s.accessToken);

  if (accessToken) {
    return <Redirect href="/(app)" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
