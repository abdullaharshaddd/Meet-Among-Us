import { Screen, EmptyState } from "@/components";

export default function MeetingsListStub() {
  return (
    <Screen style={{ justifyContent: "center" }}>
      <EmptyState glyph="◷" title="Meetings" description="Scheduled and past meetings will show up here once projects land in Phase 5–6." />
    </Screen>
  );
}
