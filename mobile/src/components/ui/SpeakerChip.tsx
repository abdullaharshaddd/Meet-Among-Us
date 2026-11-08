import { Pressable, View } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { speakerHue } from "@/theme/speakerHues";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Badge } from "./Badge";
import { Text } from "./Text";

export interface SpeakerChipProps {
  // Same id, same color, in every meeting.
  speakerId: string;
  name: string;
  // A Guest is a named outsider with no account. Never use this for an unmatched voice.
  isGuest?: boolean;
  onPress?: () => void;
}

export function SpeakerChip({ speakerId, name, isGuest = false, onPress }: SpeakerChipProps) {
  const { colors } = useTheme();
  const hue = speakerHue(speakerId);
  const extraHit = (sizes.hitMin - sizes.chipHeight) / 2;

  const chip = (
    <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: sizes.chipHeight }}>
      <View
        style={{
          width: sizes.speakerDot,
          height: sizes.speakerDot,
          borderRadius: radii.pill,
          backgroundColor: isGuest ? "transparent" : hue,
          borderWidth: isGuest ? borders.focus : 0,
          borderColor: hue,
        }}
      />
      <Text variant="subhead" style={{ flexShrink: 1 }} numberOfLines={1}>
        {name}
      </Text>
      {isGuest && <Badge label="Guest" />}
    </View>
  );

  if (!onPress) {
    return <View accessible accessibilityLabel={isGuest ? `${name}, guest` : name}>{chip}</View>;
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={isGuest ? `${name}, guest` : name}
      hitSlop={{ top: extraHit, bottom: extraHit }}
      onPress={onPress}
      style={{ alignSelf: "flex-start" }}
    >
      {chip}
    </Pressable>
  );
}
