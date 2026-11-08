import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View, type TextInputProps } from "react-native";
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from "react-native-reanimated";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, motion, opacity, radii, sizes, space, type } from "@/theme/tokens";
import { Text } from "./Text";

export interface InputProps extends Omit<TextInputProps, "style"> {
  label: string;
  error?: string;
  helper?: string;
  // Password-style field with a Show/Hide button.
  secure?: boolean;
}

const ARABIC_SCRIPT = /[؀-ۿ]/;
const LATIN_OR_ARABIC_LETTER = /[A-Za-z؀-ۿ]/;

// The first letter decides the direction, the same rule the bidi algorithm uses.
function startsWithArabicScript(text: string): boolean {
  const firstLetter = text.match(LATIN_OR_ARABIC_LETTER)?.[0];

  return firstLetter !== undefined && ARABIC_SCRIPT.test(firstLetter);
}

export function Input({
  label,
  error,
  helper,
  secure = false,
  multiline = false,
  editable = true,
  value,
  defaultValue,
  onChangeText,
  onFocus,
  onBlur,
  ...props
}: InputProps) {
  const { colors } = useTheme();
  const focus = useSharedValue(0);
  const [isRevealed, setIsRevealed] = useState(false);
  const [typedText, setTypedText] = useState(defaultValue ?? "");
  const [isFocused, setIsFocused] = useState(false);

  const currentText = value ?? typedText;
  const isUrdu = startsWithArabicScript(currentText);
  const hasError = Boolean(error);

  // The ring is its own layer so showing it never moves the field or the text around it.
  const ringStyle = useAnimatedStyle(() => ({ opacity: hasError ? 1 : focus.value }));

  const moveFocus = (to: 0 | 1) => {
    focus.value = withTiming(to, { duration: motion.duration.fast, easing: motion.easing.standard });
  };

  const note = error ?? helper;

  return (
    <View>
      <Text variant="label" tone="secondary" style={styles.label}>
        {label}
      </Text>

      <View
        style={[
          styles.field,
          multiline && styles.multiline,
          {
            backgroundColor: colors.sunken,
            // The focus ring takes over the edge, so the two never draw a double line.
            borderColor: hasError ? colors.danger : isFocused ? "transparent" : colors.borderControl,
            opacity: editable ? 1 : opacity.muted,
          },
        ]}
      >
        <TextInput
          accessibilityLabel={label}
          secureTextEntry={secure && !isRevealed}
          placeholderTextColor={colors.textSecondary}
          selectionColor={colors.ink}
          multiline={multiline}
          editable={editable}
          value={value}
          defaultValue={defaultValue}
          onChangeText={(text) => {
            setTypedText(text);
            onChangeText?.(text);
          }}
          onFocus={(event) => {
            setIsFocused(true);
            moveFocus(1);
            onFocus?.(event);
          }}
          onBlur={(event) => {
            setIsFocused(false);
            moveFocus(0);
            onBlur?.(event);
          }}
          style={[
            styles.input,
            isUrdu ? type.urduBody : type.body,
            { color: colors.textPrimary },
            isUrdu && { textAlign: "right", writingDirection: "rtl" },
            multiline && styles.multilineInput,
          ]}
          {...props}
        />

        {secure && (
          <Pressable
            onPress={() => setIsRevealed(!isRevealed)}
            hitSlop={space.sm}
            accessibilityRole="button"
            accessibilityLabel={isRevealed ? "Hide password" : "Show password"}
            style={styles.reveal}
          >
            <Text variant="subhead">{isRevealed ? "Hide" : "Show"}</Text>
          </Pressable>
        )}

        <Animated.View
          pointerEvents="none"
          style={[styles.ring, { borderColor: hasError ? colors.danger : colors.focusRing }, ringStyle]}
        />
      </View>

      {note && (
        <Text variant="caption" tone={error ? "danger" : "secondary"} style={styles.note} accessibilityLiveRegion="polite">
          {note}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    marginBottom: space.xs,
  },
  // minHeight, not height: Nastaliq must never sit in a fixed-height box.
  field: {
    minHeight: sizes.inputHeight,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: space.md,
    borderRadius: radii.md,
    borderWidth: StyleSheet.hairlineWidth,
  },
  multiline: {
    alignItems: "flex-start",
    minHeight: sizes.inputHeight * 2,
  },
  input: {
    flex: 1,
    paddingVertical: space.sm,
  },
  multilineInput: {
    textAlignVertical: "top",
    paddingVertical: space.md,
  },
  reveal: {
    minHeight: sizes.hitMin,
    justifyContent: "center",
    paddingLeft: space.sm,
  },
  ring: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderWidth: borders.focus,
    borderRadius: radii.md,
  },
  note: {
    marginTop: space.xs,
  },
});
