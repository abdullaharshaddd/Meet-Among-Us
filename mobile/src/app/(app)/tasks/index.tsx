import { View } from "react-native";
import { useRouter } from "expo-router";
import Animated from "react-native-reanimated";
import { useSetTaskDone, useTasks, type Task } from "@/api/meetings";
import { Button, EmptyState, Header, LargeTitle, Screen, Skeleton, TaskRow, Text, useDockClearance, useScrollState } from "@/components/ui";
import { layout, space } from "@/theme/tokens";

// Action items from every meeting you host or attend, with who owns them. Ticking one is shared: it shows as done
// for everyone in that meeting.
export default function TasksScreen() {
  const router = useRouter();
  const { data: tasks, isLoading, isError, refetch } = useTasks();
  const setDone = useSetTaskDone();
  const { scrollY, onScroll } = useScrollState();
  const clearance = useDockClearance(false);

  const open = (tasks ?? []).filter((task) => !task.done);
  const done = (tasks ?? []).filter((task) => task.done);

  const renderTask = (task: Task) => (
    <View key={task.id}>
      <TaskRow
        title={task.task}
        source={`${task.owner} · ${task.meeting_title}`}
        dueLabel={task.deadline_text ?? "No deadline"}
        isDone={task.done}
        onToggle={(isDone) => setDone.mutate({ id: task.id, done: isDone })}
        swipeEnabled={false}
      />
      <Button label={`Open ${task.meeting_title}`} variant="ghost" size="sm" fullWidth={false} onPress={() => router.push({ pathname: "/(app)/meetings/[id]", params: { id: task.meeting_id } })} />
    </View>
  );

  const body = () => {
    if (isLoading) return <Skeleton height={space["4xl"]} />;
    if (isError) return <EmptyState title="Couldn't load tasks" action={{ label: "Try again", onPress: () => void refetch() }} />;

    if ((tasks ?? []).length === 0) {
      return <EmptyState title="No tasks yet" description="When a meeting you were in finishes processing, the action items said in it appear here." />;
    }

    return (
      <>
        <View style={{ gap: space.xs }}>
          <Text variant="label" tone="secondary">
            Open · {open.length}
          </Text>
          {open.map(renderTask)}
        </View>

        {done.length > 0 && (
          <View style={{ gap: space.xs }}>
            <Text variant="label" tone="secondary">
              Done · {done.length}
            </Text>
            {done.map(renderTask)}
          </View>
        )}
      </>
    );
  };

  return (
    <Screen>
      <Header title="Tasks" scrollY={scrollY} />

      <Animated.ScrollView
        onScroll={onScroll}
        scrollEventThrottle={16}
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: clearance, gap: layout.sectionGap }}
      >
        <LargeTitle>Tasks</LargeTitle>
        {body()}
      </Animated.ScrollView>
    </Screen>
  );
}
