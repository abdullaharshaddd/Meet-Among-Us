import type { ReactNode } from "react";
import { View } from "react-native";
import { space } from "@/theme/tokens";
import { Text } from "./Text";

export function Section({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <View style={{ gap: space.md }}>
      <View style={{ gap: space.xs }}>
        <Text variant="label" tone="secondary">
          {title}
        </Text>
        {note && (
          <Text variant="caption" tone="secondary">
            {note}
          </Text>
        )}
      </View>
      {children}
    </View>
  );
}
