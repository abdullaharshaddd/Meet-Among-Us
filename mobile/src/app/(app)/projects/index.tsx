import { Screen, EmptyState } from "@/components";

export default function ProjectsListStub() {
  return (
    <Screen style={{ justifyContent: "center" }}>
      <EmptyState glyph="▤" title="Projects" description="Create or join a project once workspaces land in Phase 5." />
    </Screen>
  );
}
