import { Pressable, View } from "react-native";
import { speakerHue } from "@/theme/speakerHues";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, space } from "@/theme/tokens";
import { BilingualText } from "./BilingualText";
import { SpeakerChip } from "./SpeakerChip";
import { Text } from "./Text";
import { UnknownSpeakerChip } from "./UnknownSpeakerChip";

// Who said a line. A Guest is a named outsider; an Unknown Speaker is a voice that matched nobody.
export type TranscriptSpeaker =
  | { kind: "member"; id: string; name: string }
  | { kind: "guest"; id: string; name: string }
  | { kind: "unknown"; id: string; number: number };

export type SegmentLanguage = "en" | "ur" | "mixed";

export interface TranscriptRowProps {
  timeLabel: string;
  speaker: TranscriptSpeaker;
  text: string;
  language: SegmentLanguage;
  // Only the first line of a run by the same speaker shows the chip.
  showSpeaker?: boolean;
  highlighted?: boolean;
  onTimePress?: () => void;
  // Opens the rename sheet for an Unknown Speaker.
  onRenamePress?: () => void;
}

const TIME_WIDTH = 52;

export function TranscriptRow({
  timeLabel,
  speaker,
  text,
  language,
  showSpeaker = true,
  highlighted = false,
  onTimePress,
  onRenamePress,
}: TranscriptRowProps) {
  const { colors } = useTheme();

  // The segment's language sets the base direction. Mixed lines let the text decide.
  const direction = language === "ur" ? "rtl" : language === "en" ? "ltr" : "auto";
  const barColor = speaker.kind === "unknown" ? colors.borderStrong : speakerHue(speaker.id);

  return (
    <View
      style={{
        flexDirection: "row",
        gap: space.md,
        paddingVertical: space.sm,
        paddingHorizontal: space.sm,
        borderRadius: radii.md,
        backgroundColor: highlighted ? colors.sunken : "transparent",
        borderWidth: borders.hairline,
        borderColor: highlighted ? colors.borderStrong : "transparent",
      }}
    >
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Jump to ${timeLabel}`}
        disabled={!onTimePress}
        onPress={onTimePress}
        hitSlop={space.sm}
        style={{ width: TIME_WIDTH, paddingTop: space.xxs }}
      >
        <Text variant="mono" tone="secondary">
          {timeLabel}
        </Text>
      </Pressable>

      <View style={{ width: borders.focus, borderRadius: radii.pill, backgroundColor: barColor }} />

      <View style={{ flex: 1, gap: space.xs }}>
        {showSpeaker &&
          (speaker.kind === "unknown" ? (
            <UnknownSpeakerChip number={speaker.number} onPress={onRenamePress ?? (() => {})} />
          ) : (
            <SpeakerChip speakerId={speaker.id} name={speaker.name} isGuest={speaker.kind === "guest"} />
          ))}

        <BilingualText direction={direction}>{text}</BilingualText>
      </View>
    </View>
  );
}
