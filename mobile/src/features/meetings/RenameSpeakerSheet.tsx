import { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import type { Attendee } from "@/api/meetings";
import { BottomSheet, Button, Input, Text } from "@/components/ui";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";

export type RenameChoice = { attendeeId: string } | { guestName: string };

export interface RenameSpeakerSheetProps {
  visible: boolean;
  onClose: () => void;
  unknownNumber: number;
  // The people in this meeting, members and guests. A former member cannot be picked.
  attendees: Attendee[];
  saving: boolean;
  onSave: (choice: RenameChoice) => void;
}

// Names an Unknown Speaker for the whole meeting: pick someone who is in it, or type an outside guest's name.
// Nothing here changes anyone's voiceprint.
export function RenameSpeakerSheet({ visible, onClose, unknownNumber, attendees, saving, onSave }: RenameSpeakerSheetProps) {
  const { colors } = useTheme();
  const [guestName, setGuestName] = useState("");

  useEffect(() => {
    if (visible) setGuestName("");
  }, [visible]);

  const choices = attendees.filter((attendee) => attendee.kind !== "former_member");

  return (
    <BottomSheet visible={visible} onClose={onClose} title={`Who is Unknown Speaker ${unknownNumber}?`}>
      <Text variant="callout" tone="secondary">
        The name replaces "Unknown Speaker {unknownNumber}" everywhere in this meeting. It does not change anyone's voiceprint.
      </Text>

      <View style={{ gap: space.xs }}>
        {choices.map((attendee) => (
          <Pressable
            key={attendee.id}
            accessibilityRole="button"
            disabled={saving}
            onPress={() => onSave({ attendeeId: attendee.id })}
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
              minHeight: sizes.hitMin,
              paddingHorizontal: space.lg,
              borderRadius: radii.md,
              borderWidth: borders.hairline,
              borderColor: colors.border,
            }}
          >
            <Text variant="bodyStrong">{attendee.name}</Text>
            {attendee.kind === "guest" && (
              <Text variant="caption" tone="secondary">
                Guest
              </Text>
            )}
          </Pressable>
        ))}
      </View>

      <Input label="Or name a guest" value={guestName} onChangeText={setGuestName} placeholder="Name of someone from outside" />
      <Button label="Save" loading={saving} disabled={guestName.trim().length === 0} onPress={() => onSave({ guestName: guestName.trim() })} />
    </BottomSheet>
  );
}
