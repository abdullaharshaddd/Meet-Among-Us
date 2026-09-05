import { Screen, EmptyState } from "@/components";

export default function EnrollStub() {
  return (
    <Screen style={{ justifyContent: "center" }}>
      <EmptyState
        glyph="◉"
        title="Voice enrollment"
        description="Record three short passages — English, Urdu, and code-switched — to build your voiceprint. Coming in Phase 4."
      />
    </Screen>
  );
}
