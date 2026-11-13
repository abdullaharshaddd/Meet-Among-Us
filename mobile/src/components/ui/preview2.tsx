// Second half of the dev preview: navigation, recording and row components.
import { useEffect, useState } from "react";
import { View } from "react-native";
import { layout, space } from "@/theme/tokens";
import { AudioLevelMeter } from "./AudioLevelMeter";
import { ActionConfirmCard } from "./ActionConfirmCard";
import { BottomSheet } from "./BottomSheet";
import { Button } from "./Button";
import { Card } from "./Card";
import { CitationChip } from "./CitationChip";
import { EmptyState } from "./EmptyState";
import { FilterChip } from "./FilterChip";
import { MeetingCard } from "./MeetingCard";
import { Section } from "./PreviewSection";
import { RecordButton } from "./RecordButton";
import { SegmentedTabs } from "./SegmentedTabs";
import { Skeleton } from "./Skeleton";
import { StopButton } from "./StopButton";
import { TaskRow } from "./TaskRow";
import { Text } from "./Text";
import { useToast } from "./Toast";
import { TranscriptRow } from "./TranscriptRow";

function ControlsPreview() {
  const [tab, setTab] = useState("summary");
  const [filter, setFilter] = useState("mine");
  const [sheetOpen, setSheetOpen] = useState(false);
  const toast = useToast();

  return (
    <Section title="Tabs, chips, sheet, toast">
      <SegmentedTabs
        value={tab}
        onChange={setTab}
        options={[
          { key: "summary", label: "Summary" },
          { key: "transcript", label: "Transcript" },
          { key: "decisions", label: "Decisions" },
          { key: "actions", label: "Action items" },
        ]}
      />

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
        {["Mine", "All", "Overdue", "Done"].map((label) => (
          <FilterChip key={label} label={label} selected={filter === label.toLowerCase()} onPress={() => setFilter(label.toLowerCase())} />
        ))}
        <FilterChip label="Overdue" count={3} selected={false} onPress={() => {}} />
      </View>

      <CitationChip label="Sprint sync · 12:04" onPress={() => toast.show("Jumped to 12:04")} />

      <View style={{ flexDirection: "row", gap: space.sm }}>
        <Button label="Open sheet" size="sm" variant="secondary" onPress={() => setSheetOpen(true)} />
        <Button label="Show toast" size="sm" variant="secondary" onPress={() => toast.show("Moment marked at 00:12:04")} />
      </View>

      <BottomSheet visible={sheetOpen} onClose={() => setSheetOpen(false)} title="A sheet">
        <Text variant="callout" tone="secondary">
          Drag the handle down or tap the dimmed area to close.
        </Text>
        <Button label="Done" onPress={() => setSheetOpen(false)} />
      </BottomSheet>

      <Text variant="caption" tone="secondary">
        Skeleton
      </Text>
      <View style={{ gap: space.sm }}>
        <Skeleton height={20} width="60%" />
        <Skeleton height={14} />
        <Skeleton height={14} width="80%" />
      </View>
    </Section>
  );
}

function RecordingPreview() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [ended, setEnded] = useState(0);
  const level = useDemoLevel(isRecording && !isPaused);

  return (
    <Section title="Recording" note="Meter, record button, and the hold-to-end stop button. Hold the stop button for 600 ms.">
      <Card style={{ gap: space.lg }}>
        <AudioLevelMeter level={level} state={isRecording ? (isPaused ? "paused" : "capturing") : "idle"} />

        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-around" }}>
          <RecordButton isRecording={isRecording} onPress={() => setIsRecording(!isRecording)} />
          <StopButton onComplete={() => setEnded(ended + 1)} />
        </View>

        <Button label={isPaused ? "Resume meter" : "Pause meter"} size="sm" variant="secondary" onPress={() => setIsPaused(!isPaused)} />
        <Text variant="caption" tone="secondary">
          Meetings ended by holding: {ended}
        </Text>
      </Card>
    </Section>
  );
}

function RowsPreview() {
  const [done, setDone] = useState(false);

  return (
    <Section title="Rows and cards">
      <MeetingCard
        title="Sprint sync"
        whenLabel="Tue 4 Nov · 14:00"
        durationLabel="48 min"
        subtitle="Spring launch"
        people={[
          { id: "user-ayesha", name: "Ayesha Siddiqui" },
          { id: "user-bilal", name: "Bilal Hussain" },
          { id: "guest-omar", name: "Omar Farooq", isGuest: true },
        ]}
        status="processing"
        onPress={() => {}}
      />

      <Card padded={false} style={{ paddingHorizontal: layout.screenGutter }}>
        <TaskRow
          title="Send final artwork to the vendor"
          source="Sprint sync"
          dueLabel="Mon 3 Nov"
          isOverdue
          isDone={done}
          assignee={{ id: "user-bilal", name: "Bilal Hussain" }}
          onToggle={setDone}
          onReschedule={() => {}}
        />
        <TaskRow
          title="Draft the Urdu welcome copy — اردو متن"
          source="Vendor call"
          dueLabel="Today"
          isDone={false}
          onToggle={() => {}}
          swipeEnabled={false}
        />
      </Card>

      <Card style={{ gap: space.xs }}>
        {segments.slice(0, 6).map((segment, index) => (
          <TranscriptRow
            key={segment.id}
            timeLabel={`${String(Math.floor(segment.startSeconds / 60)).padStart(2, "0")}:${String(segment.startSeconds % 60).padStart(2, "0")}`}
            speaker={segment.speaker}
            text={segment.text}
            language={segment.language}
            showSpeaker={index === 0 || segments[index - 1].speaker.id !== segment.speaker.id}
            highlighted={index === 2}
            onRenamePress={() => {}}
          />
        ))}
      </Card>

      <ActionConfirmCard
        action="Create task"
        title="Send final artwork to the vendor"
        fields={[
          { label: "Owner", value: "Bilal Hussain" },
          { label: "Due", value: "Monday" },
        ]}
        onConfirm={() => {}}
        onEdit={() => {}}
        onCancel={() => {}}
      />

      <Card>
        <EmptyState title="No tasks here" description="Tasks from your meetings land here once they are confirmed." />
      </Card>
    </Section>
  );
}

export function MorePreviews() {
  return (
    <>
      <ControlsPreview />
      <RecordingPreview />
      <RowsPreview />
    </>
  );
}

// Sample lines and a wobbling level, only for this developer-only component gallery. Nothing here reaches a user.
const segments = [
  { id: "d1", startSeconds: 4, speaker: { kind: "member" as const, id: "demo-a", name: "Sample speaker A" }, text: "A sample line in English.", language: "en" as const },
  { id: "d2", startSeconds: 12, speaker: { kind: "member" as const, id: "demo-b", name: "Sample speaker B" }, text: "اردو میں ایک نمونہ جملہ۔", language: "ur" as const },
  { id: "d3", startSeconds: 20, speaker: { kind: "unknown" as const, id: "demo-u", number: 1 }, text: "Aik sample line, mixed with English.", language: "mixed" as const },
  { id: "d4", startSeconds: 31, speaker: { kind: "guest" as const, id: "demo-g", name: "Sample guest" }, text: "Another sample line.", language: "en" as const },
];

function useDemoLevel(isRunning: boolean): number {
  const [level, setLevel] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      setLevel(0);

      return;
    }

    let tick = 0;
    const timer = setInterval(() => {
      tick += 1;
      setLevel(Math.min(1, Math.max(0, (Math.sin(tick / 9) + 1) / 2)));
    }, 80);

    return () => clearInterval(timer);
  }, [isRunning]);

  return level;
}
