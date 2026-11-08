import { useState } from "react";
import { View } from "react-native";
import Animated from "react-native-reanimated";
import {
  BottomDock,
  BottomSheet,
  Button,
  EmptyState,
  FilterChip,
  Header,
  Input,
  LargeTitle,
  Screen,
  TaskRow,
  Text,
  WorkspaceSwitcher,
  useDockClearance,
  useScrollState,
  useToast,
} from "@/components/ui";
import { formatDue } from "@/lib/format";
import { initialTasks, type MockTask } from "@/mocks/tasks";
import { layout, space } from "@/theme/tokens";

type Filter = "mine" | "all" | "overdue" | "done";

// The signed-in person in the mock data.
const ME = "user-ayesha";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "mine", label: "Mine" },
  { key: "all", label: "All" },
  { key: "overdue", label: "Overdue" },
  { key: "done", label: "Done" },
];

const EMPTY_COPY: Record<Filter, { title: string; description: string }> = {
  mine: { title: "Nothing on your plate", description: "Tasks assigned to you from meetings show up here." },
  all: { title: "No tasks yet", description: "Confirm an action item from a meeting or ask the assistant to add one." },
  overdue: { title: "Nothing is late", description: "Tasks past their due date collect here." },
  done: { title: "Nothing finished yet", description: "Completed tasks stay here for reference." },
};

function groupOf(task: MockTask): string {
  if (task.isDone) return "Completed";
  if (task.dueInDays < 0) return "Overdue";
  if (task.dueInDays === 0) return "Today";
  if (task.dueInDays <= 7) return "This week";

  return "Later";
}

const GROUP_ORDER = ["Overdue", "Today", "This week", "Later", "Completed"];

export default function TasksScreen() {
  const toast = useToast();
  const { scrollY, onScroll } = useScrollState();
  const dockClearance = useDockClearance(true);

  const [tasks, setTasks] = useState(initialTasks);
  const [filter, setFilter] = useState<Filter>("mine");
  const [isAdding, setIsAdding] = useState(false);
  const [draft, setDraft] = useState("");

  const visible = tasks.filter((task) => {
    if (filter === "done") return task.isDone;
    if (task.isDone) return false;
    if (filter === "mine") return task.assigneeId === ME;
    if (filter === "overdue") return task.dueInDays < 0;

    return true;
  });

  const overdueCount = tasks.filter((task) => !task.isDone && task.dueInDays < 0).length;

  const update = (id: string, changes: Partial<MockTask>) =>
    setTasks((current) => current.map((task) => (task.id === id ? { ...task, ...changes } : task)));

  const addTask = () => {
    const title = draft.trim();
    if (!title) return;

    setTasks((current) => [
      { id: `t${current.length + 1}`, title, source: "Added by you", dueInDays: 0, assigneeId: ME, assigneeName: "Ayesha Siddiqui", isDone: false },
      ...current,
    ]);

    setDraft("");
    setIsAdding(false);
    toast.show("Task added");
  };

  return (
    <Screen>
      <Header title="Tasks" scrollY={scrollY} leading={<WorkspaceSwitcher />} />

      <Animated.ScrollView
        onScroll={onScroll}
        scrollEventThrottle={16}
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: dockClearance, gap: layout.sectionGap }}
      >
        <LargeTitle>Tasks</LargeTitle>

        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
          {FILTERS.map((item) => (
            <FilterChip
              key={item.key}
              label={item.label}
              selected={filter === item.key}
              count={item.key === "overdue" ? overdueCount : undefined}
              onPress={() => setFilter(item.key)}
            />
          ))}
        </View>

        {visible.length === 0 ? (
          <EmptyState title={EMPTY_COPY[filter].title} description={EMPTY_COPY[filter].description} />
        ) : (
          GROUP_ORDER.map((group) => {
            const rows = visible.filter((task) => groupOf(task) === group).sort((a, b) => a.dueInDays - b.dueInDays);
            if (rows.length === 0) return null;

            return (
              <View key={group}>
                <Text variant="label" tone={group === "Overdue" ? "danger" : "secondary"} style={{ marginBottom: space.xs }}>
                  {group} · {rows.length}
                </Text>

                {rows.map((task) => (
                  <TaskRow
                    key={task.id}
                    title={task.title}
                    source={task.source}
                    dueLabel={formatDue(task.dueInDays)}
                    isOverdue={task.dueInDays < 0}
                    isDone={task.isDone}
                    assignee={{ id: task.assigneeId, name: task.assigneeName }}
                    onToggle={(done) => {
                      update(task.id, { isDone: done });
                      toast.show(done ? "Marked done" : "Reopened");
                    }}
                    onReschedule={() => {
                      update(task.id, { dueInDays: 1 });
                      toast.show("Moved to tomorrow");
                    }}
                  />
                ))}
              </View>
            );
          })
        )}
      </Animated.ScrollView>

      <BottomDock>
        <View style={{ alignItems: "flex-end" }}>
          <Button label="New task" icon="add" size="dock" fullWidth={false} onPress={() => setIsAdding(true)} />
        </View>
      </BottomDock>

      <BottomSheet visible={isAdding} onClose={() => setIsAdding(false)} title="New task">
        <Input label="What needs doing?" value={draft} onChangeText={setDraft} autoFocus />
        <Button label="Add task" disabled={draft.trim().length === 0} onPress={addTask} />
      </BottomSheet>
    </Screen>
  );
}
