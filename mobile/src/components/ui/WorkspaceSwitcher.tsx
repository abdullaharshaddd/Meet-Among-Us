import { useState } from "react";
import { Pressable, View } from "react-native";
import { useRouter } from "expo-router";
import { useActiveWorkspace } from "@/api/workspaces";
import { playHaptic } from "@/lib/haptics";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Badge } from "./Badge";
import { BottomSheet } from "./BottomSheet";
import { Button } from "./Button";
import { Icon } from "./Icon";
import { Text } from "./Text";

// The workspace name in the header, and the sheet that opens from it.
export function WorkspaceSwitcher() {
  const router = useRouter();
  const { colors } = useTheme();
  const { workspace, workspaces } = useActiveWorkspace();
  const setActiveWorkspaceId = useWorkspaceStore((state) => state.setActiveWorkspaceId);
  const [isOpen, setIsOpen] = useState(false);

  const goTo = (path: "/(app)/workspaces/create" | "/(app)/workspaces/join" | "/(app)/workspaces/members") => {
    setIsOpen(false);
    router.push(path);
  };

  const choose = (id: string) => {
    playHaptic("selection");
    setActiveWorkspaceId(id);
    setIsOpen(false);
  };

  return (
    <>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Workspace ${workspace?.name ?? "none"}. Tap to switch.`}
        onPress={() => setIsOpen(true)}
        style={{ flexDirection: "row", alignItems: "center", gap: space.xs, minHeight: sizes.hitMin, flexShrink: 1 }}
      >
        <Text variant="headline" numberOfLines={1} style={{ flexShrink: 1 }}>
          {workspace?.name ?? "No workspace"}
        </Text>
        <Icon name="chevronDown" size="sm" color={colors.textSecondary} />
      </Pressable>

      <BottomSheet visible={isOpen} onClose={() => setIsOpen(false)} title="Workspaces">
        <View style={{ gap: space.xs }}>
          {workspaces.map((item) => {
            const isActive = item.id === workspace?.id;

            return (
              <Pressable
                key={item.id}
                accessibilityRole="button"
                accessibilityState={{ selected: isActive }}
                onPress={() => choose(item.id)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: space.md,
                  minHeight: sizes.dockHeight,
                  paddingHorizontal: space.lg,
                  borderRadius: radii.md,
                  borderWidth: borders.hairline,
                  borderColor: isActive ? colors.borderControl : colors.border,
                  backgroundColor: isActive ? colors.sunken : "transparent",
                }}
              >
                <View style={{ flexShrink: 1, gap: space.xxs }}>
                  <Text variant="bodyStrong" numberOfLines={1}>
                    {item.name}
                  </Text>
                  <Badge label={item.my_role} />
                </View>
                {isActive && <Icon name="check" size="md" />}
              </Pressable>
            );
          })}
        </View>

        <View style={{ gap: space.sm }}>
          <Button label="Members" variant="secondary" onPress={() => goTo("/(app)/workspaces/members")} />
          <Button label="Create a workspace" variant="secondary" onPress={() => goTo("/(app)/workspaces/create")} />
          <Button label="Join with a code" variant="ghost" onPress={() => goTo("/(app)/workspaces/join")} />
        </View>
      </BottomSheet>
    </>
  );
}
