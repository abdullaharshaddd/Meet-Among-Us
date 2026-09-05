import { Screen, EmptyState } from "@/components";

export default function MeetingDetailStub() {
  return (
    <Screen style={{ justifyContent: "center" }}>
      <EmptyState glyph="◷" title="Meeting details" description="Transcript, summary, and recordings — coming in Phase 6." />
    </Screen>
  );
}
