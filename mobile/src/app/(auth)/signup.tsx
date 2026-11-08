import { useRouter } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";
import { BottomDock, Button, Input, Screen, Text, useDockClearance } from "@/components/ui";
import { AuthHero } from "@/features/auth/AuthHero";
import { useValidatedField, validators } from "@/hooks/useValidatedField";
import { useSignup } from "@/api/auth";
import { signupErrorMessage } from "@/api/authErrors";
import { layout, sizes, space } from "@/theme/tokens";

export default function SignupScreen() {
  const router = useRouter();
  const displayName = useValidatedField(validators.displayName);
  const email = useValidatedField(validators.email);
  const password = useValidatedField(validators.password);
  const signup = useSignup();
  const dockClearance = useDockClearance(false);

  const isValid =
    !displayName.error && !email.error && !password.error && displayName.value.length > 0 && email.value.length > 0 && password.value.length > 0;

  const onSubmit = () => {
    signup.mutate({ display_name: displayName.value, email: email.value, password: password.value });
  };

  return (
    <Screen clearTopInset>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space["3xl"], paddingBottom: dockClearance, gap: layout.sectionGap }}
      >
        <AuthHero
          eyebrow="Create your account"
          headline="Start with your"
          accent="voice."
          subtitle="An account takes a minute. Your voiceprint comes after, and you choose when."
        />

        <View style={{ gap: space.md }}>
          <Input label="Name" value={displayName.value} onChangeText={displayName.setValue} onBlur={displayName.onBlur} error={displayName.error} />
          <Input
            label="Email"
            value={email.value}
            onChangeText={email.setValue}
            onBlur={email.onBlur}
            error={email.error}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Input
            label="Password"
            value={password.value}
            onChangeText={password.setValue}
            onBlur={password.onBlur}
            error={password.error}
            helper={password.error ? undefined : "At least 8 characters"}
            secure
          />

          {signup.isError && (
            <Text variant="callout" tone="danger">
              {signupErrorMessage(signup.error)}
            </Text>
          )}
        </View>

        <View style={{ alignItems: "center" }}>
          <Pressable
            onPress={() => router.push("/(auth)/login")}
            hitSlop={space.md}
            accessibilityRole="link"
            style={{ minHeight: sizes.hitMin, justifyContent: "center" }}
          >
            <Text variant="callout" tone="secondary">
              Already have an account? <Text variant="bodyStrong">Sign in</Text>
            </Text>
          </Pressable>
        </View>
      </ScrollView>

      <BottomDock aboveTabBar={false}>
        <Button label="Create account" size="dock" onPress={onSubmit} disabled={!isValid} loading={signup.isPending} />
      </BottomDock>
    </Screen>
  );
}
