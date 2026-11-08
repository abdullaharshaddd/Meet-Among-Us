import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";
import { useColorScheme } from "react-native";
import { StatusBar } from "expo-status-bar";
import * as SystemUI from "expo-system-ui";
import { floating, palettes, type Palette, type Scheme } from "./tokens";
import { useThemeStore } from "./themeStore";

export interface Theme {
  scheme: Scheme;
  isDark: boolean;
  colors: Palette;
  // The shadow for things that float: docks, sheets, toasts.
  shadow: (typeof floating)[Scheme];
}

function buildTheme(scheme: Scheme): Theme {
  return {
    scheme,
    isDark: scheme === "dark",
    colors: palettes[scheme],
    shadow: floating[scheme],
  };
}

const ThemeContext = createContext<Theme>(buildTheme("dark"));

// Follows the phone's light/dark setting unless the user picked Paper or Studio in the app.
export function ThemeProvider({ children }: { children: ReactNode }) {
  const systemScheme = useColorScheme();
  const override = useThemeStore((state) => state.override);

  // Studio is the fallback when the phone doesn't say.
  const scheme: Scheme = override ?? (systemScheme === "light" ? "light" : "dark");

  const theme = useMemo(() => buildTheme(scheme), [scheme]);

  // Paints the native window behind the app, so overscroll and keyboard
  // transitions never flash a different color than the screen.
  useEffect(() => {
    SystemUI.setBackgroundColorAsync(theme.colors.canvas);
  }, [theme]);

  // Status bar icons follow the chosen theme, not the phone's, otherwise an
  // in-app override would leave dark icons on a dark screen.
  return (
    <ThemeContext.Provider value={theme}>
      <StatusBar style={theme.isDark ? "light" : "dark"} />
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): Theme {
  return useContext(ThemeContext);
}
