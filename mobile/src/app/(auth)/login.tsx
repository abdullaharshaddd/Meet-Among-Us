import { useRouter } from "expo-router";
import { Pressable, View } from "react-native";
import { Screen, Text, TextField, Button, GoogleSignInButton } from "@/components";
import { useValidatedField, validators } from "@/hooks/useValidatedField";
import { useLogin } from "@/api/auth";
import { loginErrorMessage } from "@/api/authErrors";
import { colors, space } from "@/theme/tokens";

export default function LoginScreen() {
  const router = useRouter();
  const email = useValidatedField(validators.email);
  const password = useValidatedField(validators.password);
  const login = useLogin();

  const isValid = !email.error && !password.error && email.value.length > 0 && password.value.length > 0;

  const onSubmit = () => {
    login.mutate({ email: email.value, password: password.value });
  };

  return (
    <Screen style={{ justifyContent: "center", gap: space.lg }}>
      <View style={{ gap: space.xs }}>
        <Text variant="title">Sign in</Text>
        <Text variant="body" tone="secondary">
          Welcome back.
        </Text>
      </View>

      <View style={{ gap: space.md }}>
        <TextField
          label="Email"
          value={email.value}
          onChangeText={email.setValue}
          onBlur={email.onBlur}
          error={email.error}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <TextField label="Password" value={password.value} onChangeText={password.setValue} onBlur={password.onBlur} error={password.error} secure />
      </View>

      {login.isError && (
        <Text variant="body" tone="danger">
          {loginErrorMessage(login.error)}
        </Text>
      )}

      <Button label="Sign in" onPress={onSubmit} disabled={!isValid} loading={login.isPending} />

      <View style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
        <View style={{ flex: 1, height: 1, backgroundColor: colors.border.default }} />
        <Text variant="caption" tone="tertiary">
          or
        </Text>
        <View style={{ flex: 1, height: 1, backgroundColor: colors.border.default }} />
      </View>

      <GoogleSignInButton />

      <Pressable
        onPress={() => router.push("/(auth)/signup")}
        hitSlop={12}
        style={{ alignSelf: "center", minHeight: 44, justifyContent: "center" }}
      >
        <Text variant="body" tone="secondary">
          Don't have an account? <Text variant="bodyStrong" tone="accent">Create one</Text>
        </Text>
      </Pressable>
    </Screen>
  );
}
