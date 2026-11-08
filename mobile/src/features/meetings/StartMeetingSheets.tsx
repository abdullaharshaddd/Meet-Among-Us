import { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import { useRouter } from "expo-router";
import { BottomSheet, BilingualText, Button, Checkbox, Icon, Input, Text } from "@/components/ui";
import { projectsFor } from "@/mocks/projects";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";

export type MeetingSheet = "none" | "project" | "consent" | "join";

export interface StartMeetingSheetsProps {
  sheet: MeetingSheet;
  onChange: (sheet: MeetingSheet) => void;
  workspaceIndex: number;
}

// Start meeting opens the project picker, then the consent sheet, then the live screen.
// Join asks for a code. All three are sheets so the Meetings list stays visible behind them.
export function StartMeetingSheets({ sheet, onChange, workspaceIndex }: StartMeetingSheetsProps) {
  const router = useRouter();
  const { colors } = useTheme();
  const projects = projectsFor(workspaceIndex);

  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [toldEveryone, setToldEveryone] = useState(false);
  const [code, setCode] = useState("");

  // Each new start begins with the consent box empty.
  useEffect(() => {
    if (sheet === "project") setToldEveryone(false);
  }, [sheet]);

  const close = () => onChange("none");

  const beginRecording = () => {
    close();
    router.push({ pathname: "/(app)/live/[id]", params: { id: "new", project: projectId } });
  };

  const join = () => {
    close();
    router.push({ pathname: "/(app)/live/[id]", params: { id: "meeting-design-review" } });
  };

  return (
    <>
      <BottomSheet visible={sheet === "project"} onClose={close} title="Which project is this for?">
        {projects.length === 0 && (
          <Text variant="callout" tone="secondary">
            This workspace has no projects yet. The meeting will be saved without one.
          </Text>
        )}

        <View style={{ gap: space.xs }}>
          {projects.map((project) => {
            const isSelected = project.id === projectId;

            return (
              <Pressable
                key={project.id}
                accessibilityRole="radio"
                accessibilityState={{ selected: isSelected }}
                onPress={() => setProjectId(project.id)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  minHeight: sizes.dockHeight,
                  paddingHorizontal: space.lg,
                  borderRadius: radii.md,
                  borderWidth: isSelected ? borders.thin : borders.hairline,
                  borderColor: isSelected ? colors.ink : colors.border,
                  backgroundColor: isSelected ? colors.sunken : "transparent",
                }}
              >
                <Text variant="bodyStrong">{project.name}</Text>
                {isSelected && <Icon name="check" size="md" />}
              </Pressable>
            );
          })}
        </View>

        <Button label="Continue" onPress={() => onChange("consent")} />
      </BottomSheet>

      <BottomSheet visible={sheet === "consent"} onClose={close} title="Before you record">
        <BilingualText tone="secondary">
          Everyone in the room will be recorded and transcribed. Tell them before you start, in whichever language you speak.
        </BilingualText>

        <View style={{ gap: space.sm }}>
          <Text variant="callout" tone="secondary">
            Team members with a voiceprint are labelled by name. A person you add as a Guest is labelled as a Guest. Any other voice shows up as an Unknown Speaker until you name it.
          </Text>
        </View>

        <Pressable
          accessibilityRole="checkbox"
          accessibilityState={{ checked: toldEveryone }}
          onPress={() => setToldEveryone(!toldEveryone)}
          style={{ flexDirection: "row", alignItems: "center", gap: space.md, minHeight: sizes.hitMin }}
        >
          <Checkbox checked={toldEveryone} onChange={setToldEveryone} label="I have told everyone in the room" />
          <Text variant="bodyStrong" style={{ flexShrink: 1 }}>
            I have told everyone in the room
          </Text>
        </Pressable>

        <Button label="Start recording" variant="signal" disabled={!toldEveryone} onPress={beginRecording} />
        <Button label="Cancel" variant="ghost" onPress={close} />
      </BottomSheet>

      <BottomSheet visible={sheet === "join"} onClose={close} title="Join a meeting">
        <Input
          label="Meeting code"
          value={code}
          onChangeText={setCode}
          autoCapitalize="characters"
          autoCorrect={false}
          placeholder="K7QM-2XPD"
          helper="Ask the host to read out the code on their screen."
        />
        <Button label="Join" disabled={code.trim().length < 4} onPress={join} />
      </BottomSheet>
    </>
  );
}
