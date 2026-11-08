import { View } from "react-native";
import { space } from "@/theme/tokens";
import { BilingualText } from "./BilingualText";
import { Button } from "./Button";
import { MeterStrip } from "./MeterStrip";
import { Text } from "./Text";

export interface EmptyStateProps {
  title: string;
  description?: string;
  action?: { label: string; onPress: () => void };
  secondaryAction?: { label: string; onPress: () => void };
}

export function EmptyState({ title, description, action, secondaryAction }: EmptyStateProps) {
  return (
    <View style={{ gap: space.lg, paddingVertical: space["3xl"] }}>
      <MeterStrip />

      <View style={{ gap: space.sm }}>
        <BilingualText variant="displayMd">{title}</BilingualText>
        {description && (
          <Text variant="callout" tone="secondary">
            {description}
          </Text>
        )}
      </View>

      {(action || secondaryAction) && (
        <View style={{ gap: space.sm }}>
          {action && <Button label={action.label} onPress={action.onPress} />}
          {secondaryAction && <Button label={secondaryAction.label} variant="secondary" onPress={secondaryAction.onPress} />}
        </View>
      )}
    </View>
  );
}
