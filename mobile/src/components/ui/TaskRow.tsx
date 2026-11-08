import { View } from "react-native";
import { Swipeable } from "./TaskSwipe";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, space } from "@/theme/tokens";
import { Avatar } from "./Avatar";
import { BilingualText } from "./BilingualText";
import { Checkbox } from "./Checkbox";
import { Text } from "./Text";

export interface TaskRowProps {
  title: string;
  // Where the task came from, like "Sprint sync".
  source: string;
  dueLabel: string;
  isOverdue?: boolean;
  isDone: boolean;
  assignee?: { id: string; name: string };
  onToggle: (done: boolean) => void;
  onReschedule?: () => void;
  // Off for rows inside a meeting summary, where swiping would be a surprise.
  swipeEnabled?: boolean;
}

export function TaskRow({
  title,
  source,
  dueLabel,
  isOverdue = false,
  isDone,
  assignee,
  onToggle,
  onReschedule,
  swipeEnabled = true,
}: TaskRowProps) {
  const { colors } = useTheme();

  const row = (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        gap: space.md,
        paddingVertical: space.md,
        backgroundColor: colors.canvas,
        borderBottomWidth: borders.hairline,
        borderBottomColor: colors.border,
      }}
    >
      <Checkbox checked={isDone} onChange={onToggle} label={isDone ? `Mark ${title} not done` : `Mark ${title} done`} />

      <View style={{ flex: 1, gap: space.xxs, opacity: isDone ? 0.6 : 1 }}>
        <BilingualText variant="bodyStrong" style={isDone ? { textDecorationLine: "line-through" } : undefined}>
          {title}
        </BilingualText>

        <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
          <Text variant="mono" tone={isOverdue && !isDone ? "danger" : "secondary"}>
            {dueLabel}
          </Text>
          <Text variant="caption" tone="secondary" numberOfLines={1} style={{ flexShrink: 1 }}>
            {source}
          </Text>
        </View>
      </View>

      {assignee && <Avatar personId={assignee.id} name={assignee.name} size="sm" />}
    </View>
  );

  if (!swipeEnabled) return row;

  return (
    <Swipeable
      onComplete={() => onToggle(!isDone)}
      onReschedule={onReschedule}
      completeLabel={isDone ? "Reopen" : "Done"}
    >
      {row}
    </Swipeable>
  );
}
