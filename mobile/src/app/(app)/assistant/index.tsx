import { View } from "react-native";
import { Header, EmptyState, LargeTitle, Screen } from "@/components/ui";
import { layout, space } from "@/theme/tokens";

// The assistant needs searching across meetings, which comes after summaries. Nothing here is pretend.
export default function AssistantScreen() {
  return (
    <Screen>
      <Header title="Assistant" />

      <View style={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, gap: layout.sectionGap }}>
        <LargeTitle>Assistant</LargeTitle>
        <EmptyState
          title="Coming soon"
          description="Soon you will be able to ask questions across all your meetings and get answers that point to the exact moment. For now, open a meeting to read its summary and transcript."
        />
      </View>
    </Screen>
  );
}
