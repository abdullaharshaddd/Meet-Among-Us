import { useState } from "react";
import { ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { useDeleteAccount, useDeletionPreview } from "@/api/account";
import { Badge, Button, Card, Header, Input, LargeTitle, Screen, Skeleton, Text } from "@/components/ui";
import { GoogleReauthButton } from "@/features/account/GoogleReauthButton";
import { useAuthStore } from "@/store/authStore";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { layout, space } from "@/theme/tokens";

// Permanent. The screen says exactly what goes, what stays without the person's name, and what blocks it, then
// asks for the password (or a fresh Google sign-in) before it does anything.
export default function DeleteAccountScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const clearTokens = useAuthStore((state) => state.clearTokens);
  const setActiveWorkspaceId = useWorkspaceStore((state) => state.setActiveWorkspaceId);
  const { data: preview, isLoading } = useDeletionPreview();
  const deleteAccount = useDeleteAccount();
  const [password, setPassword] = useState("");

  const blocked = preview !== undefined && !preview.can_delete;

  const finish = () => {
    // Every session is already gone on the server. This clears the phone's copy and returns to login.
    clearTokens();
    queryClient.clear();
    router.replace("/(auth)/login");
  };

  const submit = (proof: { password?: string; google_id_token?: string }) => deleteAccount.mutate(proof, { onSuccess: finish });

  return (
    <Screen>
      <Header title="Delete account" onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space["5xl"], gap: layout.sectionGap }} keyboardShouldPersistTaps="handled">
        <LargeTitle>Delete your account</LargeTitle>
        <Text variant="callout" tone="danger">
          This is permanent. It cannot be undone, and we cannot recover anything afterwards.
        </Text>

        {isLoading && <Skeleton height={space["4xl"]} />}

        <Card style={{ gap: space.md }}>
          <Text variant="label" tone="secondary">
            What gets deleted
          </Text>
          <Text variant="callout">• Your account, your email and your sign-in on every device.</Text>
          <Text variant="callout">• Your voiceprint and your voice enrollment recordings.</Text>
          <Text variant="callout">• Your membership of every workspace, and the invites you sent.</Text>
          {(preview?.workspaces_deleted ?? []).map((workspace) => (
            <Text key={workspace.id} variant="callout">
              • The workspace "{workspace.name}", because nobody else is in it, with all its meetings, recordings and results.
            </Text>
          ))}
        </Card>

        <Card style={{ gap: space.sm }}>
          <Text variant="label" tone="secondary">
            What stays
          </Text>
          <Text variant="callout">
            Meetings in workspaces that continue ({preview?.meetings_kept ?? 0} for you) stay for the other people in them. Your name is replaced by
            "Former member" in their transcripts, attendee lists and task owners. Your words stay, without your name, and your consent answers stay
            with each meeting.
          </Text>
        </Card>

        {blocked && (
          <Card style={{ gap: space.md }}>
            <Badge label="Can't delete yet" variant="danger" />
            <Text variant="callout">
              You own {preview.workspaces_blocking.map((workspace) => `"${workspace.name}"`).join(", ")}, and other people are in it. Hand it to someone else
              first: open Members and choose "Make owner" on another person.
            </Text>
            {preview.workspaces_blocking.map((workspace) => (
              <Button
                key={workspace.id}
                label={`Open members of ${workspace.name}`}
                variant="secondary"
                onPress={() => {
                  setActiveWorkspaceId(workspace.id);
                  router.push("/(app)/workspaces/members");
                }}
              />
            ))}
          </Card>
        )}

        {preview && !blocked && (
          <View style={{ gap: space.md }}>
            <Text variant="label" tone="secondary">
              Confirm it is you
            </Text>
            <Input label="Password" value={password} onChangeText={setPassword} secure autoCapitalize="none" />
            <Text variant="caption" tone="secondary">
              Signed up with Google? Confirm with Google instead.
            </Text>

            {deleteAccount.isError && (
              <Text variant="callout" tone="danger">
                {deleteAccount.error instanceof Error ? deleteAccount.error.message : "Couldn't delete the account."}
              </Text>
            )}

            <Button label="Delete my account permanently" variant="dangerText" haptic="destructive" disabled={password.length === 0} loading={deleteAccount.isPending} onPress={() => submit({ password })} />
            <GoogleReauthButton disabled={deleteAccount.isPending} onToken={(token) => submit({ google_id_token: token })} />
          </View>
        )}
      </ScrollView>
    </Screen>
  );
}
