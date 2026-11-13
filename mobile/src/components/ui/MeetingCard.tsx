import { View } from "react-native";
import { space } from "@/theme/tokens";
import { AvatarStack, type StackPerson } from "./AvatarStack";
import { Badge } from "./Badge";
import { BilingualText } from "./BilingualText";
import { Card } from "./Card";
import { Text } from "./Text";

export type MeetingCardStatus = "upcoming" | "live" | "processing" | "ready" | "failed";

export interface MeetingCardProps {
  title: string;
  // Already formatted, like "Tue 4 Nov · 14:00".
  whenLabel: string;
  // Duration for a past meeting, or the running time for a live one.
  durationLabel?: string;
  // A line under the title, like "Hosted by Sara · 3 people".
  subtitle: string;
  people: StackPerson[];
  status: MeetingCardStatus;
  onPress: () => void;
}

export function MeetingCard({ title, whenLabel, durationLabel, subtitle, people, status, onPress }: MeetingCardProps) {
  const isLive = status === "live";

  return (
    <Card
      variant={isLive ? "live" : "default"}
      onPress={onPress}
      accessibilityLabel={`${title}, ${whenLabel}, ${subtitle}`}
      style={{ gap: space.md }}
    >
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.md }}>
        <Text variant="label" tone={isLive ? "signal" : "secondary"} numberOfLines={1} style={{ flexShrink: 1 }}>
          {isLive ? durationLabel : whenLabel}
        </Text>

        {isLive && <Badge label="Live" variant="live" />}
        {status === "upcoming" && <Badge label="Waiting for audio" variant="outline" />}
        {status === "processing" && <Badge label="Processing" variant="warning" />}
        {status === "failed" && <Badge label="Failed" variant="danger" />}
      </View>

      <BilingualText variant="headline">{title}</BilingualText>

      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.md }}>
        <View style={{ flexShrink: 1, gap: space.xxs }}>
          <Text variant="callout" tone="secondary" numberOfLines={1}>
            {subtitle}
          </Text>
          {!isLive && durationLabel && (
            <Text variant="mono" tone="secondary">
              {durationLabel}
            </Text>
          )}
        </View>

        <AvatarStack people={people} />
      </View>
    </Card>
  );
}
