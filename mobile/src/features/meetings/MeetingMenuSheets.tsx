import { useEffect, useState } from "react";
import { View } from "react-native";
import * as Clipboard from "expo-clipboard";
import { BottomSheet, Button, Input, Text, useToast } from "@/components/ui";
import { space } from "@/theme/tokens";

export type MenuSheet = "none" | "menu" | "rename" | "delete";

export interface MeetingMenuSheetsProps {
  sheet: MenuSheet;
  onChange: (sheet: MenuSheet) => void;
  title: string;
  onRename: (title: string) => void;
  onDelete: () => void;
  summaryText: string;
}

// The overflow menu from the meeting header: rename, share the summary, delete.
export function MeetingMenuSheets({ sheet, onChange, title, onRename, onDelete, summaryText }: MeetingMenuSheetsProps) {
  const toast = useToast();
  const [draft, setDraft] = useState(title);

  useEffect(() => {
    if (sheet === "rename") setDraft(title);
  }, [sheet, title]);

  const close = () => onChange("none");

  const share = async () => {
    close();

    try {
      await Clipboard.setStringAsync(summaryText);
      toast.show("Summary copied");
    } catch {
      toast.show("Couldn't copy the summary");
    }
  };

  return (
    <>
      <BottomSheet visible={sheet === "menu"} onClose={close}>
        <Button label="Rename" variant="secondary" onPress={() => onChange("rename")} />
        <Button label="Share summary" variant="secondary" onPress={share} />
        <Button label="Delete meeting" variant="dangerText" haptic="destructive" onPress={() => onChange("delete")} />
      </BottomSheet>

      <BottomSheet visible={sheet === "rename"} onClose={close} title="Rename meeting">
        <Input label="Title" value={draft} onChangeText={setDraft} autoFocus />
        <Button
          label="Save"
          disabled={draft.trim().length === 0}
          onPress={() => {
            onRename(draft.trim());
            close();
          }}
        />
      </BottomSheet>

      <BottomSheet visible={sheet === "delete"} onClose={close} title="Delete this meeting?">
        <View style={{ gap: space.xs }}>
          <Text variant="callout" tone="secondary">
            The recording, transcript, summary and decisions are removed for everyone in the workspace. This can't be undone.
          </Text>
        </View>
        <Button
          label="Delete meeting"
          variant="dangerText"
          haptic="destructive"
          onPress={() => {
            close();
            onDelete();
          }}
        />
        <Button label="Keep it" variant="secondary" onPress={close} />
      </BottomSheet>
    </>
  );
}
