import { Screen, EmptyState } from "@/components";

export default function MeetingLobbyStub() {
  return (
    <Screen style={{ justifyContent: "center" }}>
      <EmptyState glyph="●" title="Meeting lobby" description="Consent, attendee list, and Start Recording — coming in Phase 6." />
    </Screen>
  );
}
