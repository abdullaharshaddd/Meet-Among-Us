import { View } from "react-native";
import { useRouter } from "expo-router";
import { BilingualText, BottomDock, Button, Header, Input, Screen, Text, useToast } from "@/components/ui";
import { useActiveWorkspace, useInviteMember } from "@/api/workspaces";
import { useValidatedField, validators } from "@/hooks/useValidatedField";
import { playHaptic } from "@/lib/haptics";
import { layout, space } from "@/theme/tokens";

export default function InviteMemberScreen() {
  const router = useRouter();
  const toast = useToast();
  const { workspace } = useActiveWorkspace();
  const inviteMember = useInviteMember(workspace?.id);
  const email = useValidatedField(validators.email);

  const isValid = email.value.length > 0 && validators.email(email.value) === undefined;

  const send = async () => {
    await inviteMember.mutateAsync(email.value.trim());

    playHaptic("confirm");
    toast.show(`Invite sent to ${email.value.trim()}`);
    router.back();
  };

  return (
    <Screen>
      <Header onBack={() => router.back()} />

      <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.xl }}>
        <View style={{ gap: space.sm }}>
          <BilingualText variant="displayLg">Invite a teammate</BilingualText>
          <Text variant="body" tone="secondary">
            They get an email with a link to join {workspace?.name ?? "this workspace"}.
          </Text>
        </View>

        <Input
          label="Email"
          value={email.value}
          onChangeText={email.setValue}
          onBlur={email.onBlur}
          error={email.error}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          autoFocus
        />
      </View>

      <BottomDock aboveTabBar={false}>
        <Button label="Send invite" size="dock" disabled={!isValid} loading={inviteMember.isPending} onPress={send} />
      </BottomDock>
    </Screen>
  );
}
