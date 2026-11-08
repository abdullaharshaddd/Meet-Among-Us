import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { View } from "react-native";
import Animated, { FadeInUp, FadeOutUp } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, motion, radii, sizes, space } from "@/theme/tokens";
import { Icon } from "./Icon";
import { Text } from "./Text";

interface ToastItem {
  id: number;
  message: string;
}

interface ToastContextValue {
  show: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({ show: () => {} });

// One toast at a time at the top of the screen, so it never covers a dock.
export function ToastProvider({ children }: { children: ReactNode }) {
  const { colors, shadow } = useTheme();
  const insets = useSafeAreaInsets();
  const [toast, setToast] = useState<ToastItem | null>(null);
  const nextId = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = useCallback((message: string) => {
    if (timer.current) clearTimeout(timer.current);

    nextId.current += 1;
    setToast({ id: nextId.current, message });

    timer.current = setTimeout(() => setToast(null), motion.toastDuration);
  }, []);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}

      <View
        pointerEvents="none"
        style={{
          position: "absolute",
          top: insets.top + space.md,
          left: layout.screenGutter,
          right: layout.screenGutter,
          alignItems: "center",
        }}
      >
        {toast && (
          <Animated.View
            key={toast.id}
            entering={FadeInUp.duration(motion.duration.base)}
            exiting={FadeOutUp.duration(motion.duration.fast)}
            accessibilityLiveRegion="polite"
            style={[
              {
                flexDirection: "row",
                alignItems: "center",
                gap: space.sm,
                maxWidth: sizes.screenMaxWidth,
                paddingVertical: space.md,
                paddingHorizontal: space.lg,
                borderRadius: radii.lg,
                backgroundColor: colors.ink,
              },
              shadow,
            ]}
          >
            <Icon name="check" size="sm" color={colors.onInk} />
            <Text variant="subhead" color={colors.onInk} style={{ flexShrink: 1 }}>
              {toast.message}
            </Text>
          </Animated.View>
        )}
      </View>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext);
}
