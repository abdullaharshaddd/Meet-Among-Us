import { useRef, useState } from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Clipboard from "expo-clipboard";
import {
  useAddAttendee,
  useMeeting,
  useRemoveAttendee,
  useRenameSpeaker,
  useRetryMeeting,
  useSetTaskDone,
  STATUS_LABEL,
  type Citation,
  type MeetingDetail,
  type Segment,
} from "@/api/meetings";
import { useMembers } from "@/api/workspaces";
import {
  Badge,
  BilingualText,
  Button,
  Card,
  CitationChip,
  EmptyState,
  Header,
  Input,
  Screen,
  SegmentedTabs,
  Skeleton,
  TaskRow,
  Text,
  TranscriptRow,
  useToast,
  type TranscriptSpeaker,
} from "@/components/ui";
import { RenameSpeakerSheet, type RenameChoice } from "@/features/meetings/RenameSpeakerSheet";
import { formatWhen } from "@/lib/format";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, radii, space } from "@/theme/tokens";

type TabKey = "summary" | "transcript" | "decisions" | "actions";

const TABS: { key: TabKey; label: string }[] = [
  { key: "summary", label: "Summary" },
  { key: "transcript", label: "Transcript" },
  { key: "decisions", label: "Decisions" },
  { key: "actions", label: "Action items" },
];

const clock = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;

function speakerFor(segment: Segment): TranscriptSpeaker {
  const { speaker } = segment;

  if (speaker.kind === "unclear") return { kind: "unclear" };
  if (speaker.kind === "unknown") return { kind: "unknown", id: `unknown-${speaker.unknown_number}`, number: speaker.unknown_number ?? 0 };
  if (speaker.kind === "guest") return { kind: "guest", id: speaker.attendee_id ?? speaker.name, name: speaker.name };

  return { kind: "member", id: speaker.user_id ?? speaker.attendee_id ?? "former", name: speaker.name };
}

function summaryAsText(meeting: MeetingDetail): string {
  const summary = meeting.summary;

  if (!summary) return meeting.title;

  const lines = [meeting.title, "", ...summary.sentences.map((s) => s.text), "", "Key points", ...summary.key_points.map((p) => `• ${p.text}`)];

  if (summary.decisions.length) lines.push("", "Decisions", ...summary.decisions.map((d) => `• ${d.decision} (${d.decided_by})`));
  if (summary.action_items.length) lines.push("", "Action items", ...summary.action_items.map((a) => `• ${a.task} (${a.owner}${a.deadline_text ? `, ${a.deadline_text}` : ""})`));

  return lines.join("\n");
}

export default function MeetingDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const toast = useToast();
  const { colors } = useTheme();
  const { data: meeting, isLoading, isError } = useMeeting(id);
  const { data: workspaceMembers } = useMembers(meeting?.workspace_id);
  const addAttendee = useAddAttendee(id);
  const removeAttendee = useRemoveAttendee(id);
  const retry = useRetryMeeting(id);
  const renameSpeaker = useRenameSpeaker(id);
  const setTaskDone = useSetTaskDone();

  const scroller = useRef<ScrollView>(null);
  const contentTop = useRef(0);
  const rowTops = useRef<Record<number, number>>({});
  const [tab, setTab] = useState<TabKey>("summary");
  const [highlighted, setHighlighted] = useState<number | null>(null);
  const [guestDraft, setGuestDraft] = useState("");
  const [renameNumber, setRenameNumber] = useState<number | null>(null);

  if (isLoading) {
    return (
      <Screen>
        <Header onBack={() => router.back()} />
        <View style={{ paddingHorizontal: layout.screenGutter, gap: space.md }}>
          <Skeleton height={space.xl} width="60%" />
          <Skeleton height={space["4xl"]} />
        </View>
      </Screen>
    );
  }

  if (!meeting || isError) {
    return (
      <Screen>
        <Header onBack={() => router.back()} />
        <View style={{ paddingHorizontal: layout.screenGutter }}>
          <EmptyState title="Meeting not found" description="It may not exist, or you may not be in it." action={{ label: "Back to meetings", onPress: () => router.replace("/(app)/meetings") }} />
        </View>
      </Screen>
    );
  }

  const editable = meeting.is_host && (meeting.status === "waiting_for_audio" || meeting.status === "failed");
  const mine = meeting.attendees.find((attendee) => attendee.is_me);
  const iStillNeedToAnswer = mine !== undefined && !mine.consent?.granted;
  const guestsNeedingMe = meeting.is_host && meeting.attendees.some((attendee) => attendee.kind === "guest" && !attendee.consent?.granted);
  const inMeeting = new Set(meeting.attendees.map((attendee) => attendee.user_id).filter(Boolean));
  const canAdd = (workspaceMembers ?? []).filter((member) => !inMeeting.has(member.user_id));

  const addGuest = () => {
    const name = guestDraft.trim();

    if (name) addAttendee.mutate({ guest_name: name }, { onError: (error) => toast.show(error.message) });

    setGuestDraft("");
  };

  const jumpToTurn = (turn: number) => {
    setTab("transcript");
    setHighlighted(turn);
    // The transcript has to mount before its rows can be measured.
    setTimeout(() => scroller.current?.scrollTo({ y: Math.max(0, contentTop.current + (rowTops.current[turn] ?? 0) - space["4xl"]), animated: true }), 80);
  };

  const citationChips = (citations: Citation[]) => (
    <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
      {citations.map((citation) => (
        <CitationChip key={citation.turn_number} label={`${clock(citation.start)} · ${citation.speaker_name}`} onPress={() => jumpToTurn(citation.turn_number)} />
      ))}
    </View>
  );

  const saveRename = (choice: RenameChoice) => {
    if (renameNumber === null) return;

    renameSpeaker.mutate(
      { unknownNumber: renameNumber, attendeeId: "attendeeId" in choice ? choice.attendeeId : undefined, guestName: "guestName" in choice ? choice.guestName : undefined },
      {
        onSuccess: () => {
          setRenameNumber(null);
          toast.show("Renamed everywhere in this meeting");
        },
        onError: (error) => toast.show(error.message),
      },
    );
  };

  const people = (
    <Card style={{ gap: space.md }}>
      <Text variant="label" tone="secondary">
        People · {meeting.attendees.length}
      </Text>

      {meeting.attendees.map((attendee) => (
        <View key={attendee.id} style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.md }}>
          <View style={{ flexShrink: 1, gap: space.xxs }}>
            <Text variant="bodyStrong">
              {attendee.name}
              {attendee.is_me ? " (you)" : ""}
            </Text>
            <Text variant="caption" tone="secondary">
              {[
                attendee.is_host ? "Host" : attendee.kind === "guest" ? "Guest" : null,
                attendee.consent?.granted ? "Agreed" : attendee.consent ? "Declined" : meeting.status === "waiting_for_audio" ? "Hasn't answered" : null,
              ]
                .filter(Boolean)
                .join(" · ")}
            </Text>
          </View>
          {editable && !attendee.is_host && (
            <Button label="Remove" variant="ghost" size="sm" fullWidth={false} loading={removeAttendee.isPending && removeAttendee.variables === attendee.id} onPress={() => removeAttendee.mutate(attendee.id, { onError: (error) => toast.show(error.message) })} />
          )}
        </View>
      ))}

      {meeting.warnings.map((warning) => (
        <View key={warning} style={{ flexDirection: "row", gap: space.sm, alignItems: "flex-start" }}>
          <Badge label="Heads up" variant="warning" />
          <Text variant="callout" tone="secondary" style={{ flex: 1 }}>
            {warning}
          </Text>
        </View>
      ))}

      {editable && (
        <View style={{ gap: space.md }}>
          {canAdd.length > 0 && (
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
              {canAdd.map((member) => (
                <Button key={member.user_id} label={`+ ${member.display_name}`} variant="secondary" size="sm" fullWidth={false} onPress={() => addAttendee.mutate({ user_id: member.user_id }, { onError: (error) => toast.show(error.message) })} />
              ))}
            </View>
          )}
          <View style={{ flexDirection: "row", alignItems: "flex-end", gap: space.sm }}>
            <View style={{ flex: 1 }}>
              <Input label="Add a guest" value={guestDraft} onChangeText={setGuestDraft} onSubmitEditing={addGuest} returnKeyType="done" />
            </View>
            <Button label="Add" variant="secondary" fullWidth={false} disabled={guestDraft.trim().length === 0} onPress={addGuest} />
          </View>
        </View>
      )}
    </Card>
  );

  const stateCard = () => {
    if (meeting.status === "processing") {
      return (
        <Card style={{ gap: space.md }}>
          <Badge label="Processing" variant="warning" />
          <Text variant="callout" tone="secondary">
            The recording is being turned into a transcript and summary. This page updates by itself, so you can leave and come back.
          </Text>
          <View style={{ gap: space.sm }}>
            <Skeleton height={space.lg} width="70%" />
            <Skeleton height={space.lg} />
          </View>
        </Card>
      );
    }

    if (meeting.status === "failed") {
      return (
        <Card style={{ gap: space.md }}>
          <Badge label="Failed" variant="danger" />
          <Text variant="callout">{meeting.failure_reason ?? "Something went wrong."}</Text>
          <Text variant="caption" tone="secondary">
            What already worked is saved. Retrying only redoes the {meeting.failed_step ?? "failed"} step.
          </Text>
          {meeting.is_host && <Button label="Retry" variant="secondary" loading={retry.isPending} onPress={() => retry.mutate(undefined, { onError: (error) => toast.show(error.message) })} />}
        </Card>
      );
    }

    if (meeting.status === "waiting_for_audio") {
      return (
        <Card style={{ gap: space.md }}>
          <Badge label="Waiting for audio" variant="outline" />
          {meeting.consent_ready ? (
            <Text variant="callout" tone="secondary">
              Everyone has agreed.{meeting.is_host ? " Record the meeting when you are ready." : " The host records the meeting."}
            </Text>
          ) : (
            <Text variant="callout" tone="secondary">
              Recording can't be processed until everyone agrees. Waiting for: {meeting.waiting_for_consent.join(", ")}.
            </Text>
          )}
          {(iStillNeedToAnswer || guestsNeedingMe) && (
            <Button label="Review and agree" onPress={() => router.push({ pathname: "/(app)/meetings/[id]/consent", params: { id } })} />
          )}
          {meeting.is_host && (
            <Button label="Record the meeting" variant="signal" disabled={!meeting.consent_ready} onPress={() => router.push({ pathname: "/(app)/live/[id]", params: { id } })} />
          )}
        </Card>
      );
    }

    return null;
  };

  const renderResult = () => {
    const summary = meeting.summary;

    if (!summary) return null;

    if (tab === "summary") {
      return (
        <View style={{ gap: layout.sectionGap }}>
          <View style={{ gap: space.md }}>
            {summary.sentences.map((sentence) => (
              <View key={sentence.text} style={{ gap: space.sm }}>
                <BilingualText>{sentence.text}</BilingualText>
                {citationChips(sentence.citations)}
              </View>
            ))}
          </View>

          <View style={{ gap: space.md }}>
            <Text variant="label" tone="secondary">
              Key points
            </Text>
            {summary.key_points.map((point) => (
              <View key={point.text} style={{ flexDirection: "row", gap: space.md }}>
                <View style={{ width: space.sm, height: space.sm, marginTop: space.sm, borderRadius: radii.pill, backgroundColor: colors.ink }} />
                <BilingualText style={{ flex: 1 }}>{point.text}</BilingualText>
              </View>
            ))}
          </View>

          <Button
            label="Copy summary"
            variant="secondary"
            onPress={async () => {
              await Clipboard.setStringAsync(summaryAsText(meeting));
              toast.show("Summary copied");
            }}
          />
        </View>
      );
    }

    if (tab === "transcript") {
      return (
        <View style={{ gap: space.xs }}>
          {meeting.transcript.map((segment, index) => (
            <View key={segment.position} onLayout={(event) => (rowTops.current[segment.position] = event.nativeEvent.layout.y)}>
              <TranscriptRow
                timeLabel={clock(segment.start)}
                speaker={speakerFor(segment)}
                text={segment.text}
                language={segment.language === "unknown" ? "mixed" : segment.language}
                showSpeaker={index === 0 || speakerFor(meeting.transcript[index - 1]).kind !== speakerFor(segment).kind || segment.speaker.name !== meeting.transcript[index - 1].speaker.name}
                highlighted={segment.position === highlighted}
                onRenamePress={() => setRenameNumber(segment.speaker.unknown_number ?? null)}
              />
            </View>
          ))}
        </View>
      );
    }

    if (tab === "decisions") {
      if (summary.decisions.length === 0) return <Text variant="callout" tone="secondary">No decisions were stated in this meeting.</Text>;

      return (
        <View style={{ gap: layout.cardGap }}>
          {summary.decisions.map((decision) => (
            <Card key={decision.id} style={{ gap: space.md }}>
              <BilingualText variant="bodyStrong">{decision.decision}</BilingualText>
              <Text variant="caption" tone="secondary">
                {decision.decided_by}
              </Text>
              {citationChips(decision.citations)}
            </Card>
          ))}
        </View>
      );
    }

    if (summary.action_items.length === 0) return <Text variant="callout" tone="secondary">No action items were stated in this meeting.</Text>;

    return (
      <View>
        {summary.action_items.map((item) => (
          <View key={item.id}>
            <TaskRow
              title={item.task}
              source={`${item.owner} · ${meeting.title}`}
              dueLabel={item.deadline_text ?? "No deadline"}
              isDone={item.done}
              onToggle={(done) => setTaskDone.mutate({ id: item.id, done })}
              swipeEnabled={false}
            />
            {citationChips(item.citations)}
          </View>
        ))}
      </View>
    );
  };

  return (
    <Screen>
      <Header title={meeting.title} onBack={() => router.back()} />

      <ScrollView ref={scroller} contentContainerStyle={{ paddingBottom: space["5xl"] }}>
        <View style={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: space.md }}>
          <BilingualText variant="displayLg">{meeting.title}</BilingualText>
          <Text variant="mono" tone="secondary">
            {formatWhen(new Date(meeting.created_at))} · Hosted by {meeting.host_name} · {STATUS_LABEL[meeting.status]}
          </Text>
          {stateCard()}
          {people}
        </View>

        {meeting.status === "done" && meeting.summary && (
          <>
            <View style={{ paddingHorizontal: layout.screenGutter, paddingTop: space.xl }}>
              <SegmentedTabs options={TABS} value={tab} onChange={setTab} />
            </View>
            <View onLayout={(event) => (contentTop.current = event.nativeEvent.layout.y)} style={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg }}>
              {renderResult()}
            </View>
          </>
        )}
      </ScrollView>

      <RenameSpeakerSheet
        visible={renameNumber !== null}
        onClose={() => setRenameNumber(null)}
        unknownNumber={renameNumber ?? 0}
        attendees={meeting.attendees}
        saving={renameSpeaker.isPending}
        onSave={saveRename}
      />
    </Screen>
  );
}
