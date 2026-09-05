import { useRouter } from "expo-router";
import { Pressable, View } from "react-native";
import { Screen, Text, TextField, Button } from "@/components";
import { useValidatedField, validators } from "@/hooks/useValidatedField";
import { useSignup } from "@/api/auth";
import { signupErrorMessage } from "@/api/authErrors";
import { space } from "@/theme/tokens";

export default function SignupScreen() {
  const router = useRouter();
  const displayName = useValidatedField(validators.displayName);
  const email = useValidatedField(validators.email);
  const password = useValidatedField(validators.password);
  const signup = useSignup();

  const isValid =
    !displayName.error && !email.error && !password.error && displayName.value.length > 0 && email.value.length > 0 && password.value.length > 0;

  const onSubmit = () => {
    signup.mutate({ display_name: displayName.value, email: email.value, password: password.value });
  };

  return (
    <Screen style={{ justifyContent: "center", gap: space.lg }}>
      <View style={{ gap: space.xs }}>
        <Text variant="title">Create account</Text>
        <Text variant="body" tone="secondary">
          Bilingual meeting intelligence, set up in a minute.
        </Text>
      </View>

      <View style={{ gap: space.md }}>
        <TextField label="Name" value={displayName.value} onChangeText={displayName.setValue} onBlur={displayName.onBlur} error={displayName.error} />
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
        <TextField
          label="Password"
          value={password.value}
          onChangeText={password.setValue}
          onBlur={password.onBlur}
          error={password.error}
          helper={password.error ? undefined : "At least 8 characters"}
          secure
        />
      </View>

      {signup.isError && (
        <Text variant="body" tone="danger">
          {signupErrorMessage(signup.error)}
        </Text>
      )}

      <Button label="Create account" onPress={onSubmit} disabled={!isValid} loading={signup.isPending} />

      <Pressable
        onPress={() => router.push("/(auth)/login")}
        hitSlop={12}
        style={{ alignSelf: "center", minHeight: 44, justifyContent: "center" }}
      >
        <Text variant="body" tone="secondary">
          Already have an account? <Text variant="bodyStrong" tone="accent">Sign in</Text>
        </Text>
      </Pressable>
    </Screen>
  );
}
