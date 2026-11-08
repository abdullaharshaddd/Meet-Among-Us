import { useEffect, useState, type ReactNode } from "react";
import { KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, View, useWindowDimensions } from "react-native";
import { Gesture, GestureDetector, GestureHandlerRootView } from "react-native-gesture-handler";
import Animated, { runOnJS, useAnimatedStyle, useSharedValue, withSpring, withTiming } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, motion, radii, ratios, sizes, space } from "@/theme/tokens";
import { Text } from "./Text";

export interface BottomSheetProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}

export function BottomSheet({ visible, onClose, title, children }: BottomSheetProps) {
  const { colors, shadow } = useTheme();
  const insets = useSafeAreaInsets();
  const { height: windowHeight } = useWindowDimensions();

  // Stays mounted until the slide-out finishes, then lets go of the native modal.
  const [isMounted, setIsMounted] = useState(visible);
  const offset = useSharedValue(windowHeight);
  const scrim = useSharedValue(0);

  useEffect(() => {
    if (visible) {
      setIsMounted(true);
      offset.value = withSpring(0, motion.spring.sheet);
      scrim.value = withTiming(1, { duration: motion.duration.base });
      return;
    }

    scrim.value = withTiming(0, { duration: motion.duration.fast });
    offset.value = withTiming(windowHeight, { duration: motion.duration.base, easing: motion.easing.exit }, (finished) => {
      if (finished) runOnJS(setIsMounted)(false);
    });
  }, [visible, windowHeight, offset, scrim]);

  const drag = Gesture.Pan()
    .onUpdate((event) => {
      offset.value = Math.max(0, event.translationY);
    })
    .onEnd((event) => {
      if (event.translationY > motion.sheetDismiss.distance || event.velocityY > motion.sheetDismiss.velocity) {
        runOnJS(onClose)();
        return;
      }

      offset.value = withSpring(0, motion.spring.sheet);
    });

  const sheetStyle = useAnimatedStyle(() => ({ transform: [{ translateY: offset.value }] }));
  const scrimStyle = useAnimatedStyle(() => ({ opacity: scrim.value }));

  if (!isMounted) return null;

  return (
    <Modal visible transparent animationType="none" statusBarTranslucent onRequestClose={onClose}>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <Animated.View style={[{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: colors.scrim }, scrimStyle]}>
          <Pressable accessibilityLabel="Close" onPress={onClose} style={{ flex: 1 }} />
        </Animated.View>

        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          pointerEvents="box-none"
          style={{ flex: 1, justifyContent: "flex-end", alignItems: "center" }}
        >
          <Animated.View
            accessibilityViewIsModal
            style={[
              {
                width: "100%",
                maxWidth: sizes.screenMaxWidth,
                maxHeight: windowHeight * ratios.sheetMaxHeight,
                backgroundColor: colors.raised,
                borderTopLeftRadius: radii.xl,
                borderTopRightRadius: radii.xl,
                borderWidth: borders.hairline,
                borderBottomWidth: 0,
                borderColor: colors.border,
              },
              shadow,
              sheetStyle,
            ]}
          >
            <GestureDetector gesture={drag}>
              <View style={{ alignItems: "center", paddingTop: space.md, paddingBottom: space.sm, gap: space.md }}>
                <View
                  style={{
                    width: sizes.grabHandleWidth,
                    height: sizes.grabHandleHeight,
                    borderRadius: radii.pill,
                    backgroundColor: colors.borderStrong,
                  }}
                />
                {title && (
                  <Text variant="title" style={{ alignSelf: "flex-start", paddingHorizontal: layout.screenGutter }}>
                    {title}
                  </Text>
                )}
              </View>
            </GestureDetector>

            <ScrollView
              keyboardShouldPersistTaps="handled"
              contentContainerStyle={{
                paddingHorizontal: layout.screenGutter,
                paddingTop: space.sm,
                paddingBottom: insets.bottom + space.lg,
                gap: space.md,
              }}
            >
              {children}
            </ScrollView>
          </Animated.View>
        </KeyboardAvoidingView>
      </GestureHandlerRootView>
    </Modal>
  );
}
