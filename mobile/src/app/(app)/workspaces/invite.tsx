import { useState } from "react";
import { ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useActiveWorkspace, useInviteMember } from "@/api/workspaces";
import { Button, Card, Header, Input, LargeTitle, Screen, Text, useToast } from "@/components/ui";
import { layout, space } from "@/theme/tokens";

// Two ways in: the workspace's join code (share it anywhere), or an email invite that also carries a personal code.
export default function InviteScreen() {
  const router = useRouter();
  const toast = useToast();
  const { workspace } = useActiveWorkspace();
  const invite = useInviteMember(workspace?.id);
  const [email, setEmail] = useState("");

  const send = () => {
    invite.mutate(email.trim(), {
      onSuccess: () => {
        toast.show(`Invite created for ${email.trim()}. The email is sending.`);
        setEmail("");
        router.back();
      },
    });
  };

  return (
    <Screen>
      <Header title="Invite" onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space["5xl"], gap: layout.sectionGap }} keyboardShouldPersistTaps="handled">
        <LargeTitle>{`Invite to ${workspace?.name ?? "workspace"}`}</LargeTitle>

        {workspace?.join_code && workspace.code_joining_enabled && (
          <Card style={{ gap: space.sm }}>
            <Text variant="label" tone="secondary">
              Join code
            </Text>
            <Text variant="displayLg" selectable>
              {workspace.join_code}
            </Text>
            <Text variant="callout" tone="secondary">
              Anyone with this code can join. They open Settings, choose "Join with a code", and type it.
            </Text>
          </Card>
        )}

        <View style={{ gap: space.md }}>
          <Text variant="label" tone="secondary">
            Or send an email invite
          </Text>
          <Input label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" autoCorrect={false} placeholder="name@example.com" />
          {invite.isError && (
            <Text variant="callout" tone="danger">
              {invite.error instanceof Error ? invite.error.message : "Couldn't create the invite."}
            </Text>
          )}
          <Button label="Send invite" loading={invite.isPending} disabled={!email.includes("@")} onPress={send} />
        </View>
      </ScrollView>
    </Screen>
  );
}
