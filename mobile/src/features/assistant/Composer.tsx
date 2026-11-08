import { useState } from "react";
import { Pressable, TextInput, View } from "react-native";
import { BottomDock, Icon } from "@/components/ui";
import { guessDirection } from "@/lib/scriptRuns";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space, type } from "@/theme/tokens";

export interface ComposerProps {
  onSend: (text: string) => void;
  placeholder: string;
}

// The message box. Its direction follows whichever script has more words, so Urdu and
// code-switched messages line up the way they read.
export function Composer({ onSend, placeholder }: ComposerProps) {
  const { colors } = useTheme();
  const [text, setText] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  const trimmed = text.trim();
  const isRtl = trimmed.length > 0 && guessDirection(trimmed) === "rtl";

  const send = () => {
    if (!trimmed) return;

    onSend(trimmed);
    setText("");
  };

  return (
    <BottomDock>
      <View
        style={{
          flexDirection: "row",
          alignItems: "flex-end",
          gap: space.sm,
          minHeight: sizes.dockHeight,
          paddingLeft: space.lg,
          paddingRight: space.sm,
          paddingVertical: space.sm,
          borderRadius: radii.lg,
          backgroundColor: colors.surface,
          borderWidth: isFocused ? borders.focus : borders.thin,
          borderColor: isFocused ? colors.focusRing : colors.borderControl,
        }}
      >
        <TextInput
          accessibilityLabel="Message"
          value={text}
          onChangeText={setText}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          placeholderTextColor={colors.textSecondary}
          selectionColor={colors.ink}
          multiline
          style={[
            isRtl ? type.urduBody : type.body,
            {
              flex: 1,
              maxHeight: sizes.composerMax,
              paddingVertical: space.sm,
              color: colors.textPrimary,
              textAlign: isRtl ? "right" : "left",
              writingDirection: isRtl ? "rtl" : "ltr",
            },
          ]}
        />

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Send"
          accessibilityState={{ disabled: !trimmed }}
          disabled={!trimmed}
          onPress={send}
          hitSlop={space.xs}
          style={{
            width: sizes.buttonSm,
            height: sizes.buttonSm,
            borderRadius: radii.pill,
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: trimmed ? colors.ink : colors.sunken,
          }}
        >
          <Icon name="send" size="md" color={trimmed ? colors.onInk : colors.textSecondary} />
        </Pressable>
      </View>
    </BottomDock>
  );
}
