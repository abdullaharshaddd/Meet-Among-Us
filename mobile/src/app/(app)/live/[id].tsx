import { useEffect, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  AudioLevelMeter,
  AvatarStack,
  BilingualText,
  BottomDock,
  Button,
  Icon,
  Screen,
  SpeakerChip,
  StopButton,
  Text,
  useToast,
  type IconName,
} from "@/components/ui";
import { formatTimer } from "@/lib/format";
import { playHaptic } from "@/lib/haptics";
import { findMeeting } from "@/mocks/meetings";
import { liveParticipants, useMockLevel } from "@/mocks/live";
import { projectName } from "@/mocks/projects";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, motion, opacity, radii, sizes, space } from "@/theme/tokens";

// The shell starts mid-meeting so the timer and chunk counter have something to show.
const SHELL_START_SECONDS = 24 * 60 + 8;
const CHUNK_SECONDS = 30;
// Centres the small round buttons on the stop button, whose ring makes it taller.
const DECK_BUTTON_OFFSET = (sizes.stopButton + sizes.progressRingGap * 2 - sizes.dockSecondary) / 2;
const DECK_HEIGHT = sizes.stopButton + sizes.progressRingGap * 2 + space["3xl"];

function RecDot({ isPaused }: { isPaused: boolean }) {
  const { colors } = useTheme();
  const reducedMotion = useReducedMotion();
  const pulse = useSharedValue(1);

  useEffect(() => {
    if (isPaused || reducedMotion) {
      pulse.value = 1;
      return;
    }

    pulse.value = withRepeat(
      withSequence(
        withTiming(opacity.dim, { duration: motion.duration.slow * 2, easing: motion.easing.standard }),
        withTiming(1, { duration: motion.duration.slow * 2, easing: motion.easing.standard }),
      ),
      -1,
    );

    return () => cancelAnimation(pulse);
  }, [isPaused, reducedMotion, pulse]);

  const style = useAnimatedStyle(() => ({ opacity: pulse.value }));

  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
      <Animated.View
        style={[{ width: space.md, height: space.md, borderRadius: radii.pill, backgroundColor: isPaused ? colors.textSecondary : colors.signal }, style]}
      />
      <Text variant="label" tone={isPaused ? "secondary" : "signal"}>
        {isPaused ? "Paused" : "Rec"}
      </Text>
    </View>
  );
}

function DeckButton({ icon, label, onPress }: { icon: IconName; label: string; onPress: () => void }) {
  const { colors } = useTheme();

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={{ alignItems: "center", gap: space.sm, width: sizes.stopButton, marginTop: DECK_BUTTON_OFFSET }}
    >
      <View
        style={{
          width: sizes.dockSecondary,
          height: sizes.dockSecondary,
          borderRadius: radii.pill,
          alignItems: "center",
          justifyContent: "center",
          borderWidth: borders.thin,
          borderColor: colors.borderControl,
        }}
      >
        <Icon name={icon} size="lg" />
      </View>
      <Text variant="label" tone="secondary">
        {label}
      </Text>
    </Pressable>
  );
}

export default function LiveRecordingScreen() {
  const { id, project } = useLocalSearchParams<{ id: string; project?: string }>();
  const router = useRouter();
  const toast = useToast();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const meeting = findMeeting(id);
  const title = meeting?.title ?? "New meeting";
  const subtitle = meeting ? projectName(meeting.projectId) : project ? projectName(project) : "No project";

  const [elapsed, setElapsed] = useState(meeting ? SHELL_START_SECONDS : 0);
  const [isPaused, setIsPaused] = useState(false);
  const level = useMockLevel(!isPaused);

  useEffect(() => {
    if (isPaused) return;

    const timer = setInterval(() => setElapsed((seconds) => seconds + 1), 1000);

    return () => clearInterval(timer);
  }, [isPaused]);

  const chunk = Math.floor(elapsed / CHUNK_SECONDS) + 1;

  const togglePause = () => {
    playHaptic("pauseResume");
    setIsPaused(!isPaused);
  };

  const markMoment = () => {
    playHaptic("confirm");
    toast.show(`Moment marked at ${formatTimer(elapsed)}`);
  };

  const endMeeting = () => {
    toast.show("Meeting ended. Processing the recording.");
    router.replace({ pathname: "/(app)/meetings/[id]", params: { id: "meeting-hiring" } });
  };

  return (
    <Screen clearTopInset>
      <View
        style={{
          height: sizes.headerBar,
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          gap: space.md,
          paddingHorizontal: layout.screenGutter,
        }}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Minimise"
          onPress={() => router.back()}
          hitSlop={space.sm}
          style={{ width: sizes.hitMin, height: sizes.hitMin, justifyContent: "center" }}
        >
          <Icon name="minimise" size="lg" />
        </Pressable>

        <View style={{ flex: 1, alignItems: "center" }}>
          <BilingualText variant="headline" numberOfLines={1}>
            {title}
          </BilingualText>
        </View>

        <View style={{ minWidth: sizes.hitMin, alignItems: "flex-end" }}>
          <RecDot isPaused={isPaused} />
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingTop: space["2xl"],
          paddingBottom: DECK_HEIGHT + insets.bottom + space["3xl"],
          gap: layout.sectionGap,
        }}
      >
        <View style={{ alignItems: "center", gap: space.sm, paddingHorizontal: layout.screenGutter }}>
          <Text variant="timer" accessibilityLabel={`Elapsed ${formatTimer(elapsed)}`}>
            {formatTimer(elapsed)}
          </Text>
          <Text variant="mono" tone="secondary">
            Chunk {chunk} · {chunk - 1} uploaded · 0 queued
          </Text>
          <Text variant="caption" tone="secondary">
            {subtitle}
          </Text>
        </View>

        <AudioLevelMeter level={level} state={isPaused ? "paused" : "capturing"} height={sizes.meterHeightLive} />

        <View style={{ paddingHorizontal: layout.screenGutter, gap: layout.sectionGap }}>
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
              gap: space.md,
              paddingLeft: space.lg,
              paddingRight: space.sm,
              borderRadius: radii.md,
              borderWidth: borders.hairline,
              borderColor: colors.border,
              backgroundColor: colors.surface,
            }}
          >
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm, flexShrink: 1 }}>
              <Icon name="sync" size="md" color={colors.success} />
              <Text variant="mono" tone="secondary" numberOfLines={1}>
                Synced · ±12 ms
              </Text>
            </View>
            <Button label="Re-sync" size="sm" variant="ghost" onPress={() => toast.show("Re-synced the room clock")} />
          </View>

          <View style={{ gap: space.md }}>
            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <Text variant="label" tone="secondary">
                Participants · {liveParticipants.length}
              </Text>
              <AvatarStack people={liveParticipants} />
            </View>

            <View style={{ flexDirection: "row", flexWrap: "wrap", columnGap: space.lg }}>
              {liveParticipants.map((person) => (
                <SpeakerChip key={person.id} speakerId={person.id} name={person.name} isGuest={person.isGuest} />
              ))}
            </View>
          </View>
        </View>
      </ScrollView>

      <BottomDock aboveTabBar={false}>
        <View style={{ flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between" }}>
          <DeckButton icon={isPaused ? "play" : "pause"} label={isPaused ? "Resume" : "Pause"} onPress={togglePause} />
          <StopButton onComplete={endMeeting} />
          <DeckButton icon="bookmark" label="Mark" onPress={markMoment} />
        </View>
      </BottomDock>
    </Screen>
  );
}
