import { useEffect, useState } from "react";
import { Pressable, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import * as Clipboard from "expo-clipboard";
import { BilingualText, BottomDock, Button, Header, Screen, Text } from "@/components/ui";
import { ApiError } from "@/api/client";
import { useJoinWorkspace } from "@/api/workspaces";
import { cleanJoinCode, formatJoinCode, isCompleteJoinCode } from "@/lib/joinCode";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, radii, sizes, space, type } from "@/theme/tokens";

function joinErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "We couldn't find a workspace with that code. Check it and try again.";
    if (error.status === 403) return "That workspace has turned off joining by code. Ask an admin to add you.";
  }

  return "We couldn't join. Check your connection and try again.";
}

export default function JoinWorkspaceScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const joinWorkspace = useJoinWorkspace();
  const [code, setCode] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [offeredCode, setOfferedCode] = useState<string | null>(null);

  // If the clipboard already holds a join code, offer it with one tap.
  useEffect(() => {
    Clipboard.getStringAsync()
      .then((text) => {
        const clean = cleanJoinCode(text.trim());

        if (isCompleteJoinCode(clean) && text.trim().length <= 9) setOfferedCode(clean);
      })
      .catch(() => {});
  }, []);

  const join = async () => {
    try {
      await joinWorkspace.mutateAsync(cleanJoinCode(code));

      playHaptic("confirm");
      router.replace("/(app)/meetings");
    } catch {
      // The message under the code explains what happened.
    }
  };

  return (
    <Screen>
      <Header onBack={() => router.back()} />

      <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.xl }}>
        <View style={{ gap: space.sm }}>
          <BilingualText variant="displayLg">Join with a code</BilingualText>
          <Text variant="body" tone="secondary">
            Ask a teammate for the eight-character code. It looks like K7QM-2XPD.
          </Text>
        </View>

        <View style={{ gap: space.sm }}>
          <Text variant="label" tone="secondary">
            Join code
          </Text>

          <TextInput
            accessibilityLabel="Join code"
            value={formatJoinCode(code)}
            onChangeText={(text) => setCode(cleanJoinCode(text))}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="XXXX-XXXX"
            placeholderTextColor={colors.textSecondary}
            selectionColor={colors.ink}
            autoCapitalize="characters"
            autoCorrect={false}
            autoFocus
            maxLength={9}
            style={[
              type.codeInput,
              {
                height: sizes.inputHeight + space.lg,
                paddingHorizontal: space.lg,
                color: colors.textPrimary,
                backgroundColor: colors.sunken,
                borderRadius: radii.md,
                borderWidth: isFocused ? borders.focus : borders.thin,
                borderColor: joinWorkspace.isError ? colors.danger : isFocused ? colors.focusRing : colors.borderControl,
              },
            ]}
          />

          {joinWorkspace.isError && (
            <Text variant="caption" tone="danger" accessibilityLiveRegion="polite">
              {joinErrorMessage(joinWorkspace.error)}
            </Text>
          )}

          {offeredCode && code.length === 0 && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Paste ${formatJoinCode(offeredCode)} from the clipboard`}
              onPress={() => setCode(offeredCode)}
              style={{
                alignSelf: "flex-start",
                minHeight: sizes.hitMin,
                justifyContent: "center",
                paddingHorizontal: space.md,
                borderRadius: radii.sm,
                borderWidth: borders.thin,
                borderColor: colors.borderControl,
              }}
            >
              <Text variant="mono">Paste {formatJoinCode(offeredCode)}</Text>
            </Pressable>
          )}
        </View>
      </View>

      <BottomDock aboveTabBar={false}>
        <Button
          label="Join workspace"
          size="dock"
          disabled={!isCompleteJoinCode(code)}
          loading={joinWorkspace.isPending}
          onPress={join}
        />
      </BottomDock>
    </Screen>
  );
}
