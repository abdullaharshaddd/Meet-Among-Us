import { useState } from "react";
import { TextInput, View, StyleSheet, type TextInputProps } from "react-native";
import { borders, colors, fonts, radii, space, touch, type } from "@/theme/tokens";
import { Text } from "./Text";

export interface TextFieldProps extends Omit<TextInputProps, "style"> {
  label: string;
  error?: string;
  helper?: string;
  secure?: boolean;
}

// Errors here are per-field and specific ("must be 8+ characters"), not a
// generic banner — the copy rule from the auth screens applies to every
// field, not just login/signup.
export function TextField({ label, error, helper, secure, onFocus, onBlur, ...props }: TextFieldProps) {
  const [focused, setFocused] = useState(false);

  return (
    <View>
      <Text variant="label" tone="secondary" style={styles.label}>
        {label}
      </Text>
      <TextInput
        secureTextEntry={secure}
        placeholderTextColor={colors.text.tertiary}
        onFocus={(e) => {
          setFocused(true);
          onFocus?.(e);
        }}
        onBlur={(e) => {
          setFocused(false);
          onBlur?.(e);
        }}
        style={[
          styles.input,
          {
            borderColor: error ? colors.state.danger : focused ? colors.focus : colors.border.default,
            borderWidth: focused || error ? borders.focus : borders.hairline,
          },
        ]}
        {...props}
      />
      {(error || helper) && (
        <Text variant="caption" tone={error ? "danger" : "secondary"} style={styles.note}>
          {error ?? helper}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    marginBottom: space.xs,
  },
  input: {
    minHeight: touch.min,
    paddingHorizontal: space.md,
    borderRadius: radii.md,
    backgroundColor: colors.bg.surface,
    color: colors.text.primary,
    fontFamily: fonts.ui,
    fontSize: type.body.size,
  },
  note: {
    marginTop: space.xs,
  },
});
