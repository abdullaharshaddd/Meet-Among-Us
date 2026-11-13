import { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import Animated from "react-native-reanimated";
import { useEnrollmentStatus } from "@/api/enrollment";
import { useMeetings, type MeetingListItem, type MeetingStatus } from "@/api/meetings";
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
  type MeetingCardStatus,
} from "@/components/ui";
import { MeetingsDock } from "@/features/meetings/MeetingsDock";
import { useEnrollmentGate } from "@/hooks/useEnrollmentGate";
import { formatWhen } from "@/lib/format";
import { passages } from "@/lib/enrollmentPassages";
import { layout, radii, sizes, space } from "@/theme/tokens";

const CARD_STATUS: Record<MeetingStatus, MeetingCardStatus> = {
  waiting_for_audio: "upcoming",
  processing: "processing",
  done: "ready",
  failed: "failed",
};

export default function MeetingsScreen() {
  const router = useRouter();
  const { workspace, isLoading: workspacesLoading } = useActiveWorkspace();
  const { data: meetingList, isLoading: meetingsLoading, isError, refetch } = useMeetings(workspace?.id);
  const { isEnrolled } = useEnrollmentGate();
  const { data: enrollment } = useEnrollmentStatus();
  const { scrollY, isScrollingDown, onScroll } = useScrollState();
  const dockClearance = useDockClearance(true);

  const [isSearching, setIsSearching] = useState(false);
  const [query, setQuery] = useState("");

  const allMeetings = meetingList ?? [];
  const meetings = allMeetings.filter((meeting) => meeting.title.toLowerCase().includes(query.trim().toLowerCase()));
  const acceptedCount = enrollment?.passages.filter((passage) => passage.state === "accepted").length ?? 0;
  const needsEnrollment = enrollment !== undefined && !isEnrolled;

  const renderCard = (meeting: MeetingListItem) => (
    <MeetingCard
      key={meeting.id}
      title={meeting.title}
      whenLabel={formatWhen(new Date(meeting.created_at))}
      subtitle={`Hosted by ${meeting.host_name} · ${meeting.attendee_count} ${meeting.attendee_count === 1 ? "person" : "people"}`}
      people={[]}
      status={CARD_STATUS[meeting.status]}
      onPress={() => router.push({ pathname: "/(app)/meetings/[id]", params: { id: meeting.id } })}
    />
  );

  const body = () => {
    if (workspacesLoading || (workspace && meetingsLoading)) {
      return (
        <View style={{ gap: layout.cardGap }}>
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

    if (isError) {
      return <EmptyState title="Couldn't load meetings" description="Check the connection and try again." action={{ label: "Try again", onPress: () => void refetch() }} />;
    }

    if (allMeetings.length === 0) {
      return (
        <EmptyState
          title="No meetings yet"
          description="Create a meeting, choose who is in it, and get everyone's agreement. The recording becomes a transcript, a summary and a list of decisions."
          action={{ label: "New meeting", onPress: () => router.push("/(app)/meetings/new") }}
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

    return <View style={{ gap: layout.cardGap }}>{meetings.map(renderCard)}</View>;
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
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: dockClearance, gap: layout.sectionGap }}
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

      {workspace && (
        <MeetingsDock
          isEnrolled={isEnrolled}
          isScrollingDown={isScrollingDown}
          onStart={() => router.push("/(app)/meetings/new")}
          onEnroll={() => router.push("/(app)/enroll")}
        />
      )}
    </Screen>
  );
}
