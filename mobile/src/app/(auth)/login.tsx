import { useRouter } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";
import { BottomDock, Button, GoogleSignInButton, Input, Screen, Text, useDockClearance } from "@/components/ui";
import { AuthHero } from "@/features/auth/AuthHero";
import { useValidatedField, validators } from "@/hooks/useValidatedField";
import { useLogin } from "@/api/auth";
import { loginErrorMessage } from "@/api/authErrors";
import { layout, sizes, space } from "@/theme/tokens";

export default function LoginScreen() {
  const router = useRouter();
  const email = useValidatedField(validators.email);
  const password = useValidatedField(validators.password);
  const login = useLogin();
  // Two stacked buttons in the dock, so the list needs room for a second one.
  const dockClearance = useDockClearance(false) + sizes.dockHeight + space.sm;

  const isValid = !email.error && !password.error && email.value.length > 0 && password.value.length > 0;

  const onSubmit = () => {
    login.mutate({ email: email.value, password: password.value });
  };

  return (
    <Screen clearTopInset>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space["3xl"], paddingBottom: dockClearance, gap: layout.sectionGap }}
      >
        <AuthHero
          eyebrow="MeetAmongUs"
          headline="Every word,"
          accent="remembered."
          subtitle="Record the room in English and Urdu. Get back who said what, and what was decided."
        />

        <View style={{ gap: space.md }}>
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
          <Input label="Password" value={password.value} onChangeText={password.setValue} onBlur={password.onBlur} error={password.error} secure />

          {login.isError && (
            <Text variant="callout" tone="danger">
              {loginErrorMessage(login.error)}
            </Text>
          )}
        </View>

        <View style={{ gap: space.xs, alignItems: "center" }}>
          <Pressable
            onPress={() => router.push("/(auth)/signup")}
            hitSlop={space.md}
            accessibilityRole="link"
            style={{ minHeight: sizes.hitMin, justifyContent: "center" }}
          >
            <Text variant="callout" tone="secondary">
              Don't have an account? <Text variant="bodyStrong">Create one</Text>
            </Text>
          </Pressable>

          {__DEV__ && <Button label="Design system (dev only)" variant="ghost" size="sm" onPress={() => router.push("/design-system")} />}
        </View>
      </ScrollView>

      <BottomDock aboveTabBar={false}>
        <View style={{ gap: space.sm }}>
          <GoogleSignInButton />
          <Button label="Sign in with email" size="dock" variant="secondary" onPress={onSubmit} disabled={!isValid} loading={login.isPending} />
        </View>
      </BottomDock>
    </Screen>
  );
}
