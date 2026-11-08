import { useEffect, useState } from "react";
import { Pressable, Switch, View } from "react-native";
import { Avatar, BottomSheet, Button, Icon, Input, Text } from "@/components/ui";
import { members, type MockPerson } from "@/mocks/people";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";

export interface RenameChoice {
  kind: "member" | "guest";
  id: string;
  name: string;
}

export interface RenameSpeakerSheetProps {
  visible: boolean;
  onClose: () => void;
  // The Unknown Speaker being named, and how many lines they have in this meeting.
  unknownNumber: number;
  segmentCount: number;
  guests: MockPerson[];
  // Called with the person chosen and whether every one of the speaker's lines should change.
  onSave: (choice: RenameChoice, applyToAll: boolean) => void;
}

// "Who is this?" lists the team, the Guests already in this meeting, and a way to add a new
// Guest by name. Adding a Guest makes them a named attendee with no voiceprint.
export function RenameSpeakerSheet({ visible, onClose, unknownNumber, segmentCount, guests, onSave }: RenameSpeakerSheetProps) {
  const { colors } = useTheme();
  const [choice, setChoice] = useState<RenameChoice | null>(null);
  const [isAddingGuest, setIsAddingGuest] = useState(false);
  const [guestName, setGuestName] = useState("");
  const [applyToAll, setApplyToAll] = useState(true);

  // Every time the sheet opens it starts clean, with "apply to all" on.
  useEffect(() => {
    if (!visible) return;

    setChoice(null);
    setIsAddingGuest(false);
    setGuestName("");
    setApplyToAll(true);
  }, [visible]);

  const addGuest = () => {
    const name = guestName.trim();
    if (!name) return;

    setChoice({ kind: "guest", id: `guest-${name.toLowerCase().replace(/\s+/g, "-")}`, name });
    setIsAddingGuest(false);
  };

  const renderRow = (person: { id: string; name: string }, kind: "member" | "guest") => {
    const isSelected = choice?.id === person.id;

    return (
      <Pressable
        key={person.id}
        accessibilityRole="radio"
        accessibilityState={{ selected: isSelected }}
        onPress={() => setChoice({ kind, id: person.id, name: person.name })}
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: space.md,
          minHeight: sizes.dockHeight,
          paddingHorizontal: space.md,
          borderRadius: radii.md,
          borderWidth: isSelected ? borders.thin : borders.hairline,
          borderColor: isSelected ? colors.ink : colors.border,
          backgroundColor: isSelected ? colors.sunken : "transparent",
        }}
      >
        <Avatar personId={person.id} name={person.name} isGuest={kind === "guest"} />
        <Text variant="bodyStrong" style={{ flex: 1 }} numberOfLines={1}>
          {person.name}
        </Text>
        {kind === "guest" && <Text variant="label" tone="secondary">Guest</Text>}
        {isSelected && <Icon name="check" size="md" />}
      </Pressable>
    );
  };

  // A Guest typed in just now is not in the meeting's list yet, so it gets its own row.
  const typedGuest = choice && choice.kind === "guest" && !guests.some((guest) => guest.id === choice.id) ? choice : null;

  return (
    <BottomSheet visible={visible} onClose={onClose} title="Who is this?">
      <Text variant="callout" tone="secondary">
        Unknown Speaker {unknownNumber} has {segmentCount} {segmentCount === 1 ? "line" : "lines"} in this meeting.
      </Text>

      <View style={{ gap: space.xs }}>
        <Text variant="label" tone="secondary">
          Team
        </Text>
        {members.map((person) => renderRow(person, "member"))}
      </View>

      <View style={{ gap: space.xs }}>
        <Text variant="label" tone="secondary">
          Guests in this meeting
        </Text>
        {guests.map((person) => renderRow(person, "guest"))}
        {typedGuest && renderRow(typedGuest, "guest")}

        {isAddingGuest ? (
          <View style={{ gap: space.sm }}>
            <Input label="Guest's name" value={guestName} onChangeText={setGuestName} autoFocus />
            <Button label="Add guest" size="sm" fullWidth={false} disabled={guestName.trim().length === 0} onPress={addGuest} />
          </View>
        ) : (
          <Button label="Add as guest…" variant="secondary" icon="add" onPress={() => setIsAddingGuest(true)} />
        )}
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          gap: space.md,
          minHeight: sizes.hitMin,
        }}
      >
        <Text variant="bodyStrong" style={{ flexShrink: 1 }}>
          Apply to all {segmentCount} segments
        </Text>
        <Switch
          value={applyToAll}
          onValueChange={setApplyToAll}
          accessibilityLabel={`Apply to all ${segmentCount} segments`}
          trackColor={{ false: colors.sunken, true: colors.ink }}
          thumbColor={colors.raised}
          ios_backgroundColor={colors.sunken}
        />
      </View>

      <Button label="Save" disabled={!choice} onPress={() => choice && onSave(choice, applyToAll)} />
    </BottomSheet>
  );
}
