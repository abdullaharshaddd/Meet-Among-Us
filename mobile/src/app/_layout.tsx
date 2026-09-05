import { useEffect, useState } from "react";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAppFonts } from "@/theme/fonts";
import { useAuthStore } from "@/store/authStore";

// Held open until fonts AND the stored session resolve, so nothing ever
// paints with the system fallback font or flashes "logged out" before the
// real token loads.
SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient();

export default function RootLayout() {
  const fontsLoaded = useAppFonts();
  const isHydrated = useAuthStore((s) => s.isHydrated);
  const [hydrationStarted, setHydrationStarted] = useState(false);

  useEffect(() => {
    if (!hydrationStarted) {
      setHydrationStarted(true);
      useAuthStore.getState().hydrate();
    }
  }, [hydrationStarted]);

  const ready = fontsLoaded && isHydrated;

  useEffect(() => {
    if (ready) {
      SplashScreen.hideAsync();
    }
  }, [ready]);

  if (!ready) {
    return null;
  }

  // No auth-guard logic here — that lives in (app)/_layout.tsx, one level
  // down, so this stays a plain provider shell.
  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerShown: false }} />
    </QueryClientProvider>
  );
}
