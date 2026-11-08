import { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import * as Clipboard from "expo-clipboard";
import { BilingualText, BottomDock, Button, Card, Header, Input, Screen, Text, useToast } from "@/components/ui";
import { ApiError } from "@/api/client";
import { useCreateWorkspace, type Workspace } from "@/api/workspaces";
import { formatJoinCode } from "@/lib/joinCode";
import { playHaptic } from "@/lib/haptics";
import { layout, space, type } from "@/theme/tokens";

const NAME_MIN = 2;

export default function CreateWorkspaceScreen() {
  const router = useRouter();
  const toast = useToast();
  const createWorkspace = useCreateWorkspace();
  const [name, setName] = useState("");
  const [created, setCreated] = useState<Workspace | null>(null);

  const trimmed = name.trim();

  const create = async () => {
    try {
      const workspace = await createWorkspace.mutateAsync(trimmed);

      playHaptic("confirm");
      setCreated(workspace);
    } catch {
      // The message under the field explains what happened.
    }
  };

  const copyCode = async (code: string) => {
    await Clipboard.setStringAsync(code);
    toast.show("Join code copied");
  };

  const errorMessage = createWorkspace.isError
    ? createWorkspace.error instanceof ApiError && createWorkspace.error.status === 422
      ? "Enter a name between 2 and 80 characters."
      : "We couldn't create the workspace. Check your connection and try again."
    : undefined;

  if (created) {
    return (
      <Screen>
        <Header />
        <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.xl }}>
          <View style={{ gap: space.sm }}>
            <Text variant="label" tone="success">
              Workspace created
            </Text>
            <BilingualText variant="displayLg">{created.name}</BilingualText>
          </View>

          {created.join_code && (
            <Card style={{ gap: space.md }}>
              <Text variant="label" tone="secondary">
                Join code
              </Text>
              <Text style={type.codeInput} accessibilityLabel={`Join code ${created.join_code.split("").join(" ")}`}>
                {formatJoinCode(created.join_code)}
              </Text>
              <Text variant="callout" tone="secondary">
                Share it out loud or by message. Anyone with the code can join, until you turn code joining off.
              </Text>
              <Button label="Copy code" icon="copy" variant="secondary" onPress={() => copyCode(created.join_code ?? "")} />
            </Card>
          )}
        </View>

        <BottomDock aboveTabBar={false}>
          <Button label="Go to meetings" size="dock" onPress={() => router.replace("/(app)/meetings")} />
        </BottomDock>
      </Screen>
    );
  }

  return (
    <Screen>
      <Header onBack={() => router.back()} />

      <View style={{ flex: 1, paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.xl }}>
        <View style={{ gap: space.sm }}>
          <BilingualText variant="displayLg">Create a workspace</BilingualText>
          <Text variant="body" tone="secondary">
            One workspace per team. Meetings, tasks and people live inside it.
          </Text>
        </View>

        <Input
          label="Workspace name"
          value={name}
          onChangeText={setName}
          error={errorMessage}
          placeholder="Orbit Labs"
          autoFocus
          returnKeyType="done"
        />
      </View>

      <BottomDock aboveTabBar={false}>
        <Button
          label="Create workspace"
          size="dock"
          disabled={trimmed.length < NAME_MIN}
          loading={createWorkspace.isPending}
          onPress={create}
        />
      </BottomDock>
    </Screen>
  );
}
