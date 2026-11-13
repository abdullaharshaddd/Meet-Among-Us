import { useState } from "react";
import { ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useCreateMeeting } from "@/api/meetings";
import { useActiveWorkspace, useMembers } from "@/api/workspaces";
import { Badge, Button, Card, Checkbox, Header, Input, LargeTitle, Screen, Text } from "@/components/ui";
import { useAuthStore } from "@/store/authStore";
import { layout, space } from "@/theme/tokens";

// Create a meeting: a title, who is in it from the workspace, and any named guests. Then it opens, where everyone
// agrees to be recorded.
export default function NewMeetingScreen() {
  const router = useRouter();
  const { workspace } = useActiveWorkspace();
  const { data: members, isLoading } = useMembers(workspace?.id);
  const me = useAuthStore((state) => state.user);
  const create = useCreateMeeting(workspace?.id);

  const [title, setTitle] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const [guestDraft, setGuestDraft] = useState("");
  const [guests, setGuests] = useState<string[]>([]);

  const others = (members ?? []).filter((member) => member.user_id !== me?.id);
  const canCreate = title.trim().length > 0 && !create.isPending;

  const addGuest = () => {
    const name = guestDraft.trim();

    if (name && !guests.some((existing) => existing.toLowerCase() === name.toLowerCase())) setGuests([...guests, name]);

    setGuestDraft("");
  };

  const submit = () => {
    create.mutate(
      { title: title.trim(), attendee_user_ids: picked, guest_names: guests },
      { onSuccess: (meeting) => router.replace({ pathname: "/(app)/meetings/[id]", params: { id: meeting.id } }) },
    );
  };

  return (
    <Screen>
      <Header title="New meeting" onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space["5xl"], gap: layout.sectionGap }} keyboardShouldPersistTaps="handled">
        <LargeTitle>New meeting</LargeTitle>

        <Input label="Title" value={title} onChangeText={setTitle} placeholder="Weekly sync" autoFocus />

        <View style={{ gap: space.sm }}>
          <Text variant="label" tone="secondary">
            Who is in the room
          </Text>
          <Card style={{ gap: space.xs }}>
            <Text variant="bodyStrong">You (host)</Text>
          </Card>
          {isLoading && <Text variant="callout" tone="secondary">Loading your team…</Text>}
          {others.map((member) => (
            <Checkbox
              key={member.user_id}
              label={member.display_name}
              checked={picked.includes(member.user_id)}
              onChange={(checked) => setPicked(checked ? [...picked, member.user_id] : picked.filter((id) => id !== member.user_id))}
            />
          ))}
          {!isLoading && others.length === 0 && (
            <Text variant="callout" tone="secondary">
              Nobody else is in this workspace yet. You can invite people from Settings, or add a guest below.
            </Text>
          )}
        </View>

        <View style={{ gap: space.sm }}>
          <Text variant="label" tone="secondary">
            Guests
          </Text>
          <Text variant="callout" tone="secondary">
            A guest is a named person from outside the workspace. They have no account, so you agree to the recording for them.
          </Text>
          <View style={{ flexDirection: "row", alignItems: "flex-end", gap: space.sm }}>
            <View style={{ flex: 1 }}>
              <Input label="Guest name" value={guestDraft} onChangeText={setGuestDraft} onSubmitEditing={addGuest} returnKeyType="done" />
            </View>
            <Button label="Add" variant="secondary" fullWidth={false} disabled={guestDraft.trim().length === 0} onPress={addGuest} />
          </View>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
            {guests.map((name) => (
              <Button key={name} label={`${name}  ✕`} variant="ghost" size="sm" fullWidth={false} onPress={() => setGuests(guests.filter((g) => g !== name))} />
            ))}
          </View>
          {guests.length > 0 && <Badge label={`${guests.length} guest${guests.length === 1 ? "" : "s"}`} variant="outline" />}
        </View>

        {create.isError && (
          <Text variant="callout" tone="danger">
            {create.error instanceof Error ? create.error.message : "Couldn't create the meeting."}
          </Text>
        )}

        <Button label="Create meeting" loading={create.isPending} disabled={!canCreate} onPress={submit} />
      </ScrollView>
    </Screen>
  );
}
