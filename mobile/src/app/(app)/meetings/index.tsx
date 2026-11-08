import { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import Animated from "react-native-reanimated";
import { useEnrollmentStatus } from "@/api/enrollment";
import { useActiveWorkspace } from "@/api/workspaces";
import {
  Button,
  Card,
  EmptyState,
  Header,
  Input,
  LargeTitle,
  MeetingCard,
  Screen,
  Skeleton,
  Text,
  WorkspaceSwitcher,
  useDockClearance,
  useScrollState,
} from "@/components/ui";
import { MeetingsDock } from "@/features/meetings/MeetingsDock";
import { StartMeetingSheets, type MeetingSheet } from "@/features/meetings/StartMeetingSheets";
import { useEnrollmentGate } from "@/hooks/useEnrollmentGate";
import { formatDuration, formatTimer, formatWhen } from "@/lib/format";
import { passages } from "@/lib/enrollmentPassages";
import { findPerson } from "@/mocks/people";
import { listMeetings, meetingProjectName, type MockMeeting } from "@/mocks/meetings";
import { layout, radii, sizes, space } from "@/theme/tokens";

function peopleFor(meeting: MockMeeting) {
  return meeting.participantIds.map((id) => {
    const person = findPerson(id);

    return { id, name: person?.name ?? "Unknown", isGuest: person?.isGuest ?? false };
  });
}

export default function MeetingsScreen() {
  const router = useRouter();
  const { workspace, workspaceIndex, isLoading: workspacesLoading } = useActiveWorkspace();
  const { isEnrolled } = useEnrollmentGate();
  const { data: enrollment } = useEnrollmentStatus();
  const { scrollY, isScrollingDown, onScroll } = useScrollState();
  const dockClearance = useDockClearance(true);

  const [sheet, setSheet] = useState<MeetingSheet>("none");
  const [isSearching, setIsSearching] = useState(false);
  const [query, setQuery] = useState("");

  const allMeetings = workspace ? listMeetings(workspaceIndex) : [];
  const meetings = allMeetings.filter((meeting) => meeting.title.toLowerCase().includes(query.trim().toLowerCase()));

  const liveMeeting = meetings.find((meeting) => meeting.status === "live");
  const upcoming = meetings.filter((meeting) => meeting.status === "upcoming").sort((a, b) => a.startsAt.getTime() - b.startsAt.getTime());
  const past = meetings
    .filter((meeting) => meeting.status !== "upcoming" && meeting.status !== "live")
    .sort((a, b) => b.startsAt.getTime() - a.startsAt.getTime());

  const acceptedCount = enrollment?.passages.filter((passage) => passage.state === "accepted").length ?? 0;
  const needsEnrollment = enrollment !== undefined && !isEnrolled;

  const openMeeting = (meeting: MockMeeting) => {
    if (meeting.status === "live") {
      router.push({ pathname: "/(app)/live/[id]", params: { id: meeting.id } });
      return;
    }

    router.push({ pathname: "/(app)/meetings/[id]", params: { id: meeting.id } });
  };

  const renderCard = (meeting: MockMeeting) => {
    const minutesLive = Math.max(1, Math.round((Date.now() - meeting.startsAt.getTime()) / 60000));

    return (
      <MeetingCard
        key={meeting.id}
        title={meeting.title}
        whenLabel={formatWhen(meeting.startsAt)}
        durationLabel={meeting.status === "live" ? formatTimer(minutesLive * 60) : meeting.durationMinutes ? formatDuration(meeting.durationMinutes) : undefined}
        projectName={meetingProjectName(meeting)}
        people={peopleFor(meeting)}
        status={meeting.status}
        onPress={() => openMeeting(meeting)}
      />
    );
  };

  const body = () => {
    if (workspacesLoading) {
      return (
        <View style={{ gap: layout.cardGap }}>
          <Skeleton height={sizes.skeletonCard} radius={radii.md} />
          <Skeleton height={sizes.skeletonCard} radius={radii.md} />
          <Skeleton height={sizes.skeletonCard} radius={radii.md} />
        </View>
      );
    }

    if (!workspace) {
      return (
        <EmptyState
          title="Start with a workspace"
          description="A workspace is where your team's meetings, tasks and people live. Create one, or join with a code from a teammate."
          action={{ label: "Create a workspace", onPress: () => router.push("/(app)/workspaces/create") }}
          secondaryAction={{ label: "Join with a code", onPress: () => router.push("/(app)/workspaces/join") }}
        />
      );
    }

    if (allMeetings.length === 0) {
      return (
        <EmptyState
          title="No meetings yet"
          description="Start one when everyone is in the room. The recording becomes a transcript, a summary and a list of decisions."
        />
      );
    }

    if (meetings.length === 0) {
      return (
        <Text variant="callout" tone="secondary">
          No meeting matches "{query}".
        </Text>
      );
    }

    return (
      <>
        {liveMeeting && renderCard(liveMeeting)}

        {upcoming.length > 0 && (
          <View style={{ gap: layout.cardGap }}>
            <Text variant="label" tone="secondary">
              Upcoming · {upcoming.length}
            </Text>
            {upcoming.map(renderCard)}
          </View>
        )}

        {past.length > 0 && (
          <View style={{ gap: layout.cardGap }}>
            <Text variant="label" tone="secondary">
              Past
            </Text>
            {past.map(renderCard)}
          </View>
        )}
      </>
    );
  };

  return (
    <Screen>
      <Header
        title="Meetings"
        scrollY={scrollY}
        leading={<WorkspaceSwitcher />}
        action={{ icon: "search", label: "Search meetings", onPress: () => setIsSearching(!isSearching) }}
      />

      <Animated.ScrollView
        onScroll={onScroll}
        scrollEventThrottle={16}
        contentContainerStyle={{
          paddingHorizontal: layout.screenGutter,
          paddingTop: space.lg,
          paddingBottom: dockClearance,
          gap: layout.sectionGap,
        }}
      >
        <LargeTitle>Meetings</LargeTitle>

        {isSearching && <Input label="Search" value={query} onChangeText={setQuery} placeholder="Meeting title" autoFocus />}

        {needsEnrollment && (
          <Card style={{ gap: space.md }}>
            <View style={{ gap: space.xs }}>
              <Text variant="label" tone="secondary">
                Voice enrollment · {acceptedCount} of {passages.length}
              </Text>
              <Text variant="headline">Set up your voice</Text>
              <Text variant="callout" tone="secondary">
                Meetings label who spoke by matching voices. Read three short passages once and your name appears next to your words.
              </Text>
            </View>
            <Button label={acceptedCount > 0 ? "Continue enrollment" : "Start enrollment"} onPress={() => router.push("/(app)/enroll")} />
          </Card>
        )}

        <View style={{ gap: layout.sectionGap }}>{body()}</View>
      </Animated.ScrollView>

      <MeetingsDock
        isEnrolled={isEnrolled}
        isScrollingDown={isScrollingDown}
        onStart={() => setSheet("project")}
        onJoin={() => setSheet("join")}
        onEnroll={() => router.push("/(app)/enroll")}
      />

      <StartMeetingSheets sheet={sheet} onChange={setSheet} workspaceIndex={workspaceIndex} />
    </Screen>
  );
}
