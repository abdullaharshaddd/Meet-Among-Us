import { useEffect, useState } from "react";
import { Platform, View } from "react-native";
import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import * as SplashScreen from "expo-splash-screen";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAppFonts } from "@/theme/fonts";
import { ToastProvider } from "@/components/ui";
import { ThemeProvider, useTheme } from "@/theme/ThemeProvider";
import { useThemeStore } from "@/theme/themeStore";
import { borders, sizes } from "@/theme/tokens";
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
      useThemeStore.getState().hydrate();
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
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <PhoneFrame>
            <ToastProvider>
              <Stack screenOptions={{ headerShown: false }} />
            </ToastProvider>
          </PhoneFrame>
        </QueryClientProvider>
      </ThemeProvider>
    </GestureHandlerRootView>
  );
}

// On the web the app is a phone-width column with the canvas color around it. Phones are untouched.
function PhoneFrame({ children }: { children: React.ReactNode }) {
  const { colors } = useTheme();

  if (Platform.OS !== "web") return <>{children}</>;

  return (
    <View style={{ flex: 1, alignItems: "center", backgroundColor: colors.canvas }}>
      <View
        style={{
          flex: 1,
          width: "100%",
          maxWidth: sizes.screenMaxWidth,
          borderLeftWidth: borders.hairline,
          borderRightWidth: borders.hairline,
          borderColor: colors.border,
        }}
      >
        {children}
      </View>
    </View>
  );
}
