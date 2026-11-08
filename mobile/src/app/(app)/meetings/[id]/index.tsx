import { useRef, useState } from "react";
import { LayoutChangeEvent, Pressable, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import Animated, { runOnJS, useAnimatedReaction } from "react-native-reanimated";
import {
  AvatarStack,
  Badge,
  BilingualText,
  BottomDock,
  Button,
  Card,
  CitationChip,
  EmptyState,
  Header,
  Icon,
  Screen,
  SegmentedTabs,
  Skeleton,
  TaskRow,
  Text,
  TranscriptRow,
  useDockClearance,
  useScrollState,
  useToast,
} from "@/components/ui";
import { MeetingMenuSheets, type MenuSheet } from "@/features/meetings/MeetingMenuSheets";
import { RenameSpeakerSheet, type RenameChoice } from "@/features/meetings/RenameSpeakerSheet";
import { formatDuration, formatWhen } from "@/lib/format";
import { findMeeting, meetingProjectName } from "@/mocks/meetings";
import { findPerson, guests as initialGuests, type MockPerson } from "@/mocks/people";
import { actionItems, decisions, formatClock, segments as initialSegments, summary } from "@/mocks/transcript";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, radii, sizes, space } from "@/theme/tokens";

type TabKey = "summary" | "transcript" | "decisions" | "actions";

const TABS: { key: TabKey; label: string }[] = [
  { key: "summary", label: "Summary" },
  { key: "transcript", label: "Transcript" },
  { key: "decisions", label: "Decisions" },
  { key: "actions", label: "Action items" },
];

// How far a citation jump lands below the top, so the line isn't hidden under the sticky tabs.
const JUMP_MARGIN = sizes.pillHeight + space.xl;

export default function MeetingDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const toast = useToast();
  const { colors, shadow } = useTheme();
  const meeting = findMeeting(id);
  const { scrollY, onScroll } = useScrollState();
  const dockClearance = useDockClearance(true);
  const scroller = useRef<Animated.ScrollView>(null);

  const [tab, setTab] = useState<TabKey>("summary");
  const [title, setTitle] = useState(meeting?.title ?? "");
  const [menu, setMenu] = useState<MenuSheet>("none");
  const [segments, setSegments] = useState(initialSegments);
  const [guests, setGuests] = useState<MockPerson[]>(initialGuests);
  const [renameSegmentId, setRenameSegmentId] = useState<string | null>(null);
  const [doneItems, setDoneItems] = useState<string[]>([]);

  // Where each transcript row sits, measured as the rows lay out, so a citation can scroll to it.
  const contentTop = useRef(0);
  const rowTops = useRef<Record<string, number>>({});
  const [jumpedTo, setJumpedTo] = useState<{ id: string; label: string; top: number } | null>(null);
  const [pillDirection, setPillDirection] = useState<"up" | "down" | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);

  const jumpTarget = jumpedTo?.top ?? null;

  // The "Back to" pill appears once the reader has moved a screen away from the line they jumped to.
  useAnimatedReaction(
    () => {
      if (jumpTarget === null) return 0;
      const away = scrollY.value - jumpTarget;

      return away > 400 ? 1 : away < -400 ? -1 : 0;
    },
    (state, previous) => {
      if (state !== previous) runOnJS(setPillDirection)(state === 1 ? "up" : state === -1 ? "down" : null);
    },
    [jumpTarget],
  );

  if (!meeting) {
    return (
      <Screen>
        <Header onBack={() => router.back()} />
        <View style={{ paddingHorizontal: layout.screenGutter }}>
          <EmptyState title="Meeting not found" description="It may have been deleted." action={{ label: "Back to meetings", onPress: () => router.back() }} />
        </View>
      </Screen>
    );
  }

  const people = meeting.participantIds.map((personId) => {
    const person = findPerson(personId);

    return { id: personId, name: person?.name ?? "Unknown", isGuest: person?.isGuest ?? false };
  });

  const renameSegment = segments.find((segment) => segment.id === renameSegmentId);
  const renameSpeaker = renameSegment?.speaker.kind === "unknown" ? renameSegment.speaker : null;
  const renameCount = renameSpeaker ? segments.filter((segment) => segment.speaker.id === renameSpeaker.id).length : 0;

  const saveRename = (choice: RenameChoice, applyToAll: boolean) => {
    if (!renameSpeaker || !renameSegmentId) return;

    if (choice.kind === "guest" && !guests.some((guest) => guest.id === choice.id)) {
      setGuests([...guests, { id: choice.id, name: choice.name, isGuest: true }]);
    }

    setSegments(
      segments.map((segment) => {
        const isTarget = applyToAll ? segment.speaker.id === renameSpeaker.id : segment.id === renameSegmentId;

        return isTarget ? { ...segment, speaker: { kind: choice.kind, id: choice.id, name: choice.name } } : segment;
      }),
    );

    setRenameSegmentId(null);
    toast.show(`Named ${choice.name}${applyToAll ? ` on ${renameCount} lines` : ""}`);
  };

  const jumpToMoment = (seconds: number, label: string) => {
    const target = segments.reduce((closest, segment) =>
      Math.abs(segment.startSeconds - seconds) < Math.abs(closest.startSeconds - seconds) ? segment : closest,
    );

    setTab("transcript");
    setHighlightedId(target.id);

    // The transcript has to mount before its rows can be measured.
    setTimeout(() => {
      const top = Math.max(0, contentTop.current + (rowTops.current[target.id] ?? 0) - JUMP_MARGIN);

      scroller.current?.scrollTo({ y: top, animated: true });
      setJumpedTo({ id: target.id, label, top });
    }, 80);
  };

  const backToJump = () => {
    if (jumpedTo) scroller.current?.scrollTo({ y: jumpedTo.top, animated: true });
  };

  const sourceLabel = (seconds: number) => `${title} · ${formatClock(seconds)}`;

  const renderBody = () => {
    if (meeting.status === "processing") {
      return (
        <View style={{ gap: space.lg }}>
          <Card style={{ gap: space.md }}>
            <Badge label="Processing" variant="warning" />
            <Text variant="callout" tone="secondary">
              The recording is being transcribed. This takes a few minutes, and you will get a notification when it is ready.
            </Text>
          </Card>
          <View style={{ gap: space.sm }}>
            <Skeleton height={space.xl} width="55%" />
            <Skeleton height={space.lg} />
            <Skeleton height={space.lg} />
            <Skeleton height={space.lg} width="70%" />
          </View>
        </View>
      );
    }

    if (meeting.status === "failed") {
      return (
        <Card style={{ gap: space.md }}>
          <Badge label="Failed" variant="danger" />
          <Text variant="callout" tone="secondary">
            We couldn't process this recording. The audio is safe, and you can try again.
          </Text>
          <Button label="Try again" variant="secondary" onPress={() => toast.show("Queued for another try")} />
        </Card>
      );
    }

    if (tab === "summary") {
      return (
        <View style={{ gap: layout.sectionGap }}>
          <BilingualText variant="body">{summary.overview}</BilingualText>

          <View style={{ gap: space.md }}>
            <Text variant="label" tone="secondary">
              Key points
            </Text>
            {summary.points.map((point) => (
              <View key={point} style={{ flexDirection: "row", gap: space.md }}>
                <View style={{ width: space.sm, height: space.sm, marginTop: space.sm, borderRadius: radii.pill, backgroundColor: colors.ink }} />
                <BilingualText style={{ flex: 1 }}>{point}</BilingualText>
              </View>
            ))}
          </View>

          <View style={{ gap: space.sm }}>
            <Text variant="label" tone="secondary">
              Sources
            </Text>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
              {decisions.map((decision) => (
                <CitationChip key={decision.id} label={sourceLabel(decision.atSeconds)} onPress={() => jumpToMoment(decision.atSeconds, formatClock(decision.atSeconds))} />
              ))}
            </View>
          </View>
        </View>
      );
    }

    if (tab === "transcript") {
      return (
        <View style={{ gap: space.xs }}>
          {segments.map((segment, index) => (
            <View
              key={segment.id}
              onLayout={(event: LayoutChangeEvent) => {
                rowTops.current[segment.id] = event.nativeEvent.layout.y;
              }}
            >
              <TranscriptRow
                timeLabel={formatClock(segment.startSeconds)}
                speaker={segment.speaker}
                text={segment.text}
                language={segment.language}
                showSpeaker={index === 0 || segments[index - 1].speaker.id !== segment.speaker.id}
                highlighted={segment.id === highlightedId}
                onRenamePress={() => setRenameSegmentId(segment.id)}
              />
            </View>
          ))}
        </View>
      );
    }

    if (tab === "decisions") {
      return (
        <View style={{ gap: layout.cardGap }}>
          {decisions.map((decision) => (
            <Card key={decision.id} style={{ gap: space.md }}>
              <BilingualText variant="bodyStrong">{decision.text}</BilingualText>
              <CitationChip label={sourceLabel(decision.atSeconds)} onPress={() => jumpToMoment(decision.atSeconds, formatClock(decision.atSeconds))} />
            </Card>
          ))}
        </View>
      );
    }

    return (
      <View>
        {actionItems.map((item) => (
          <TaskRow
            key={item.id}
            title={item.title}
            source={`${item.ownerName} · ${title}`}
            dueLabel={item.dueLabel}
            isDone={doneItems.includes(item.id)}
            assignee={{ id: item.ownerId, name: item.ownerName }}
            onToggle={(done) => setDoneItems(done ? [...doneItems, item.id] : doneItems.filter((value) => value !== item.id))}
            swipeEnabled={false}
          />
        ))}
      </View>
    );
  };

  const summaryText = `${title}\n\n${summary.overview}\n\n${summary.points.map((point) => `• ${point}`).join("\n")}`;

  return (
    <Screen>
      <Header
        title={title}
        scrollY={scrollY}
        onBack={() => router.back()}
        action={{ icon: "more", label: "Meeting options", onPress: () => setMenu("menu") }}
      />

      <Animated.ScrollView
        ref={scroller}
        onScroll={onScroll}
        scrollEventThrottle={16}
        stickyHeaderIndices={[1]}
        contentContainerStyle={{ paddingBottom: dockClearance }}
      >
        <View style={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space.lg, gap: space.md }}>
          <BilingualText variant="displayLg">{title}</BilingualText>

          <Text variant="mono" tone="secondary">
            {formatWhen(meeting.startsAt)}
            {meeting.durationMinutes ? ` · ${formatDuration(meeting.durationMinutes)}` : ""}
          </Text>

          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.md }}>
            <Text variant="callout" tone="secondary" numberOfLines={1} style={{ flexShrink: 1 }}>
              {meetingProjectName(meeting)}
            </Text>
            <AvatarStack people={people} />
          </View>
        </View>

        <View style={{ backgroundColor: colors.canvas, paddingHorizontal: layout.screenGutter, paddingVertical: space.sm }}>
          <SegmentedTabs options={TABS} value={tab} onChange={setTab} />
        </View>

        <View
          onLayout={(event) => {
            contentTop.current = event.nativeEvent.layout.y;
          }}
          style={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg }}
        >
          {renderBody()}
        </View>
      </Animated.ScrollView>

      {pillDirection && jumpedTo && tab === "transcript" && (
        <View pointerEvents="box-none" style={{ position: "absolute", left: 0, right: 0, bottom: dockClearance, alignItems: "center" }}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Back to ${jumpedTo.label}`}
            onPress={backToJump}
            style={[
              {
                flexDirection: "row",
                alignItems: "center",
                gap: space.sm,
                minHeight: sizes.hitMin,
                paddingHorizontal: space.lg,
                borderRadius: radii.pill,
                backgroundColor: colors.ink,
              },
              shadow,
            ]}
          >
            <Icon name={pillDirection === "up" ? "arrowUp" : "arrowDown"} size="sm" color={colors.onInk} />
            <Text variant="subhead" color={colors.onInk}>
              Back to {jumpedTo.label}
            </Text>
          </Pressable>
        </View>
      )}

      <BottomDock>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Ask about this meeting"
          onPress={() => router.push({ pathname: "/(app)/assistant/index", params: { scope: meeting.id } })}
          style={{
            height: sizes.dockHeight,
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            paddingLeft: space.lg,
            paddingRight: space.sm,
            borderRadius: radii.lg,
            borderWidth: borders.thin,
            borderColor: colors.borderControl,
            backgroundColor: colors.surface,
          }}
        >
          <Text variant="body" tone="secondary">
            Ask about this meeting…
          </Text>
          <View
            style={{
              width: sizes.buttonSm,
              height: sizes.buttonSm,
              borderRadius: radii.pill,
              backgroundColor: colors.ink,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon name="send" size="md" color={colors.onInk} />
          </View>
        </Pressable>
      </BottomDock>

      <MeetingMenuSheets
        sheet={menu}
        onChange={setMenu}
        title={title}
        onRename={setTitle}
        onDelete={() => {
          toast.show("Meeting deleted");
          router.back();
        }}
        summaryText={summaryText}
      />

      <RenameSpeakerSheet
        visible={renameSpeaker !== null}
        onClose={() => setRenameSegmentId(null)}
        unknownNumber={renameSpeaker?.number ?? 0}
        segmentCount={renameCount}
        guests={guests}
        onSave={saveRename}
      />
    </Screen>
  );
}
