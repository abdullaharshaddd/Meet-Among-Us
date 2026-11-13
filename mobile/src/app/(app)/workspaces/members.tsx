import { useState } from "react";
import { ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import {
  useActiveWorkspace,
  useChangeRole,
  useInvites,
  useMembers,
  useRemoveMember,
  useResendInvite,
  useRevokeInvite,
  useTransferOwnership,
  type WorkspaceMember,
} from "@/api/workspaces";
import { BottomSheet, Badge, Button, Card, EmptyState, Header, LargeTitle, Screen, Skeleton, Text, useToast } from "@/components/ui";
import { layout, space } from "@/theme/tokens";

type Pending = { kind: "remove" | "leave" | "transfer"; member: WorkspaceMember } | null;

// Everyone in the workspace. The owner changes roles and hands the workspace over, an admin removes plain members,
// and anyone but the owner can leave.
export default function MembersScreen() {
  const router = useRouter();
  const toast = useToast();
  const { workspace } = useActiveWorkspace();
  const { data: members, isLoading } = useMembers(workspace?.id);
  const isOwner = workspace?.my_role === "owner";
  const isAdmin = workspace?.my_role === "owner" || workspace?.my_role === "admin";
  const { data: invites } = useInvites(workspace?.id, isAdmin);
  const changeRole = useChangeRole(workspace?.id);
  const removeMember = useRemoveMember(workspace?.id);
  const transfer = useTransferOwnership(workspace?.id);
  const revoke = useRevokeInvite(workspace?.id);
  const resend = useResendInvite(workspace?.id);
  const [pending, setPending] = useState<Pending>(null);

  const fail = (error: Error) => toast.show(error.message);
  const canRemove = (member: WorkspaceMember) => !member.is_me && member.role !== "owner" && (isOwner || (isAdmin && member.role === "member"));

  const confirm = () => {
    if (!pending) return;

    const done = () => setPending(null);

    if (pending.kind === "transfer") transfer.mutate(pending.member.user_id, { onSuccess: done, onError: fail });
    else removeMember.mutate(pending.member.user_id, { onSuccess: () => { done(); if (pending.kind === "leave") router.replace("/(app)/meetings"); }, onError: fail });
  };

  return (
    <Screen>
      <Header title="Members" onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space["5xl"], gap: layout.sectionGap }}>
        <LargeTitle>{workspace?.name ?? "Members"}</LargeTitle>

        {isAdmin && <Button label="Invite someone" onPress={() => router.push("/(app)/workspaces/invite")} />}

        {isLoading && <Skeleton height={space["4xl"]} />}

        <View style={{ gap: layout.cardGap }}>
          {(members ?? []).map((member) => (
            <Card key={member.user_id} style={{ gap: space.sm }}>
              <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.md }}>
                <View style={{ flexShrink: 1 }}>
                  <Text variant="bodyStrong">
                    {member.display_name}
                    {member.is_me ? " (you)" : ""}
                  </Text>
                  {member.email && (
                    <Text variant="caption" tone="secondary">
                      {member.email}
                    </Text>
                  )}
                </View>
                <Badge label={member.role === "owner" ? "Owner" : member.role === "admin" ? "Admin" : "Member"} variant={member.role === "member" ? "outline" : "success"} />
              </View>

              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
                {isOwner && !member.is_me && member.role !== "owner" && (
                  <Button
                    label={member.role === "admin" ? "Make member" : "Make admin"}
                    variant="secondary"
                    size="sm"
                    fullWidth={false}
                    onPress={() => changeRole.mutate({ userId: member.user_id, role: member.role === "admin" ? "member" : "admin" }, { onError: fail })}
                  />
                )}
                {isOwner && !member.is_me && <Button label="Make owner" variant="secondary" size="sm" fullWidth={false} onPress={() => setPending({ kind: "transfer", member })} />}
                {canRemove(member) && <Button label="Remove" variant="dangerText" size="sm" fullWidth={false} onPress={() => setPending({ kind: "remove", member })} />}
                {member.is_me && member.role !== "owner" && <Button label="Leave workspace" variant="dangerText" size="sm" fullWidth={false} onPress={() => setPending({ kind: "leave", member })} />}
              </View>
            </Card>
          ))}
        </View>

        {isAdmin && (
          <View style={{ gap: layout.cardGap }}>
            <Text variant="label" tone="secondary">
              Pending invites
            </Text>
            {(invites ?? []).length === 0 && <EmptyState title="No pending invites" />}
            {(invites ?? []).map((invite) => (
              <Card key={invite.id} style={{ gap: space.sm }}>
                <Text variant="bodyStrong">{invite.email}</Text>
                <Text variant="caption" tone={invite.email_status === "failed" ? "danger" : "secondary"}>
                  {invite.email_status === "sent" ? "Email sent" : invite.email_status === "sending" ? "Sending…" : `Email not sent: ${invite.email_error ?? "unknown reason"}`}
                </Text>
                <View style={{ flexDirection: "row", gap: space.sm }}>
                  <Button label="Resend" variant="secondary" size="sm" fullWidth={false} onPress={() => resend.mutate(invite.id, { onSuccess: () => toast.show("Sending again"), onError: fail })} />
                  <Button label="Revoke" variant="dangerText" size="sm" fullWidth={false} onPress={() => revoke.mutate(invite.id, { onError: fail })} />
                </View>
              </Card>
            ))}
          </View>
        )}
      </ScrollView>

      <BottomSheet
        visible={pending !== null}
        onClose={() => setPending(null)}
        title={pending?.kind === "transfer" ? `Make ${pending.member.display_name} the owner?` : pending?.kind === "leave" ? "Leave this workspace?" : `Remove ${pending?.member.display_name}?`}
      >
        <Text variant="callout" tone="secondary">
          {pending?.kind === "transfer"
            ? "They become the only owner and you become an admin. Only they can undo it."
            : pending?.kind === "leave"
              ? "You lose access to this workspace and its meetings. You can rejoin with a code or an invite."
              : "They lose access to this workspace and its meetings."}
        </Text>
        <Button label="Confirm" variant={pending?.kind === "transfer" ? "primary" : "dangerText"} loading={removeMember.isPending || transfer.isPending} onPress={confirm} />
        <Button label="Cancel" variant="secondary" onPress={() => setPending(null)} />
      </BottomSheet>
    </Screen>
  );
}
