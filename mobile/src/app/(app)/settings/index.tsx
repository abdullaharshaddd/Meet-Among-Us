import { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import Constants from "expo-constants";
import Animated from "react-native-reanimated";
import {
  Avatar,
  Badge,
  BilingualText,
  BottomSheet,
  Button,
  Header,
  LargeTitle,
  Screen,
  SegmentedTabs,
  Text,
  useScrollState,
} from "@/components/ui";
import { useLogout } from "@/api/auth";
import { useEnrollmentStatus, useResetEnrollment } from "@/api/enrollment";
import { useActiveWorkspace } from "@/api/workspaces";
import { SettingsGroup, SettingsRow } from "@/features/settings/SettingsList";
import { playHaptic } from "@/lib/haptics";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/theme/themeStore";
import { layout, space } from "@/theme/tokens";

type ThemeChoice = "system" | "light" | "dark";

const THEME_OPTIONS: { key: ThemeChoice; label: string }[] = [
  { key: "system", label: "System" },
  { key: "light", label: "Paper" },
  { key: "dark", label: "Studio" },
];

type Sheet = "none" | "reenroll" | "signout";

export default function SettingsScreen() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { data: enrollment } = useEnrollmentStatus();
  const resetEnrollment = useResetEnrollment();
  const { workspace } = useActiveWorkspace();
  const { scrollY, onScroll } = useScrollState();
  const themeOverride = useThemeStore((state) => state.override);
  const setThemeOverride = useThemeStore((state) => state.setOverride);

  const [sheet, setSheet] = useState<Sheet>("none");
  const [resetFailed, setResetFailed] = useState(false);

  const hasVoiceprint = enrollment !== undefined && enrollment.enrollment_status !== "not_started";
  const isEnrolled = enrollment?.enrollment_status === "complete";

  const reEnroll = async () => {
    setResetFailed(false);

    try {
      await resetEnrollment.mutateAsync();
    } catch {
      setResetFailed(true);
      return;
    }

    setSheet("none");
    router.push("/(app)/enroll");
  };

  const signOut = () => {
    playHaptic("destructive");
    setSheet("none");
    logout();
  };

  return (
    <Screen>
      <Header title="Settings" scrollY={scrollY} />

      <Animated.ScrollView
        onScroll={onScroll}
        scrollEventThrottle={16}
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space["5xl"], gap: layout.sectionGap }}
      >
        <LargeTitle>Settings</LargeTitle>

        <SettingsGroup title="Account">
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.lg }}>
            <Avatar personId={user?.id ?? "me"} name={user?.display_name ?? "?"} imageUrl={user?.avatar_url} />
            <View style={{ flex: 1, gap: space.xxs }}>
              <BilingualText variant="headline" numberOfLines={1}>
                {user?.display_name ?? "Signed in"}
              </BilingualText>
              <Text variant="callout" tone="secondary" numberOfLines={1}>
                {user?.email ?? ""}
              </Text>
            </View>
          </View>
        </SettingsGroup>

        <SettingsGroup title="Voice">
          <SettingsRow
            label="Voice enrollment"
            trailing={<Badge label={isEnrolled ? "Enrolled" : "Not enrolled"} variant={isEnrolled ? "success" : "warning"} />}
            onPress={() => router.push("/(app)/enroll")}
            isLast={!hasVoiceprint}
          />
          {hasVoiceprint && <SettingsRow label="Delete voiceprint and re-enroll" tone="danger" onPress={() => setSheet("reenroll")} isLast />}
        </SettingsGroup>

        <SettingsGroup title="Workspace">
          <SettingsRow label="Current workspace" value={workspace?.name ?? "None"} />
          <SettingsRow label="Members" onPress={() => router.push("/(app)/workspaces/members")} />
          <SettingsRow label="Create a workspace" onPress={() => router.push("/(app)/workspaces/create")} />
          <SettingsRow label="Join with a code" onPress={() => router.push("/(app)/workspaces/join")} isLast />
        </SettingsGroup>

        <View style={{ gap: space.sm }}>
          <Text variant="label" tone="secondary">
            Appearance
          </Text>
          <SegmentedTabs
            options={THEME_OPTIONS}
            value={themeOverride ?? "system"}
            onChange={(choice) => setThemeOverride(choice === "system" ? null : choice)}
          />
        </View>

        <SettingsGroup title="Integrations">
          <SettingsRow label="Google Calendar" value="Coming soon" isLast />
        </SettingsGroup>

        <SettingsGroup title="About">
          <SettingsRow label="Version" value={Constants.expoConfig?.version ?? "1.0.0"} isLast />
        </SettingsGroup>

        {__DEV__ && (
          <SettingsGroup title="Developer">
            <SettingsRow label="Design system" onPress={() => router.push("/design-system")} isLast />
          </SettingsGroup>
        )}

        <Button label="Sign out" variant="dangerText" onPress={() => setSheet("signout")} />
      </Animated.ScrollView>

      <BottomSheet visible={sheet === "reenroll"} onClose={() => setSheet("none")} title="Delete your voiceprint?">
        <Text variant="callout" tone="secondary">
          This deletes your current voiceprint and recordings. You will need to record all three passages again before joining meetings.
        </Text>
        {resetFailed && (
          <Text variant="callout" tone="danger">
            We couldn't delete it. Check your connection and try again.
          </Text>
        )}
        <Button label="Delete and re-enroll" variant="dangerText" haptic="destructive" loading={resetEnrollment.isPending} onPress={reEnroll} />
        <Button label="Cancel" variant="secondary" onPress={() => setSheet("none")} />
      </BottomSheet>

      <BottomSheet visible={sheet === "signout"} onClose={() => setSheet("none")} title="Sign out?">
        <Text variant="callout" tone="secondary">
          You will need to sign in again to see your meetings.
        </Text>
        <Button label="Sign out" variant="dangerText" onPress={signOut} />
        <Button label="Stay signed in" variant="secondary" onPress={() => setSheet("none")} />
      </BottomSheet>
    </Screen>
  );
}
