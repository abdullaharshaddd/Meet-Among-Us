import { View } from "react-native";
import { useRouter } from "expo-router";
import * as Clipboard from "expo-clipboard";
import Animated from "react-native-reanimated";
import {
  Avatar,
  Badge,
  BottomDock,
  Button,
  Card,
  EmptyState,
  Header,
  LargeTitle,
  Screen,
  Skeleton,
  Text,
  useDockClearance,
  useScrollState,
  useToast,
} from "@/components/ui";
import { useActiveWorkspace, useMembers } from "@/api/workspaces";
import { formatJoinCode } from "@/lib/joinCode";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, space, type } from "@/theme/tokens";

export default function MembersScreen() {
  const router = useRouter();
  const toast = useToast();
  const { colors } = useTheme();
  const { workspace } = useActiveWorkspace();
  const { data: members, isLoading } = useMembers(workspace?.id);
  const { scrollY, onScroll } = useScrollState();
  const dockClearance = useDockClearance(false);

  const canInvite = workspace?.my_role === "owner" || workspace?.my_role === "admin";

  const copyCode = async (code: string) => {
    await Clipboard.setStringAsync(code);
    toast.show("Join code copied");
  };

  return (
    <Screen>
      <Header title="Members" scrollY={scrollY} onBack={() => router.back()} />

      <Animated.ScrollView
        onScroll={onScroll}
        scrollEventThrottle={16}
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: dockClearance, gap: layout.sectionGap }}
      >
        <LargeTitle subtitle={workspace?.name}>Members</LargeTitle>

        {/* Members never get a code from the server, so a missing code simply shows nothing. */}
        {workspace?.join_code && (
          <Card style={{ gap: space.md }}>
            <Text variant="label" tone="secondary">
              Join code
            </Text>
            <Text style={type.codeInput} accessibilityLabel={`Join code ${workspace.join_code.split("").join(" ")}`}>
              {formatJoinCode(workspace.join_code)}
            </Text>
            <Button label="Copy code" icon="copy" variant="secondary" onPress={() => copyCode(workspace.join_code ?? "")} />
          </Card>
        )}

        {isLoading && (
          <View style={{ gap: space.md }}>
            <Skeleton height={space["4xl"]} />
            <Skeleton height={space["4xl"]} />
            <Skeleton height={space["4xl"]} />
          </View>
        )}

        {members && members.length === 0 && <EmptyState title="Just you so far" description="Invite teammates by email or share the join code." />}

        {members && members.length > 0 && (
          <View>
            {members.map((member) => (
              <View
                key={member.userId}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  gap: space.md,
                  paddingVertical: space.md,
                  borderBottomWidth: borders.hairline,
                  borderBottomColor: colors.border,
                }}
              >
                <Avatar personId={member.userId} name={member.name} />

                <View style={{ flex: 1, gap: space.xxs }}>
                  <Text variant="bodyStrong" numberOfLines={1}>
                    {member.name}
                  </Text>
                  <Text variant="caption" tone="secondary" numberOfLines={1}>
                    {member.email}
                  </Text>
                </View>

                <View style={{ alignItems: "flex-end", gap: space.xs }}>
                  <Badge label={member.role} />
                  {!member.isEnrolled && <Badge label="Not enrolled" variant="warning" />}
                </View>
              </View>
            ))}
          </View>
        )}
      </Animated.ScrollView>

      {canInvite && (
        <BottomDock aboveTabBar={false}>
          <Button label="Invite by email" size="dock" icon="add" onPress={() => router.push("/(app)/workspaces/invite")} />
        </BottomDock>
      )}
    </Screen>
  );
}
