import { useRef, type ReactNode } from "react";
import { View } from "react-native";
import ReanimatedSwipeable, { type SwipeableMethods } from "react-native-gesture-handler/ReanimatedSwipeable";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { sizes } from "@/theme/tokens";
import { Icon } from "./Icon";
import { Text } from "./Text";

export interface SwipeableProps {
  children: ReactNode;
  onComplete: () => void;
  onReschedule?: () => void;
  completeLabel: string;
}

// Swipe right to finish a task, swipe left to push it to another day. Either way the row
// springs back, because the list decides what the task looks like afterwards.
export function Swipeable({ children, onComplete, onReschedule, completeLabel }: SwipeableProps) {
  const { colors } = useTheme();
  const swipeable = useRef<SwipeableMethods>(null);

  const handleOpen = (direction: "left" | "right") => {
    playHaptic("confirm");

    // Opening to the right means the person dragged the row to the right.
    if (direction === "right") onComplete();
    else onReschedule?.();

    swipeable.current?.close();
  };

  return (
    <ReanimatedSwipeable
      ref={swipeable}
      friction={2}
      overshootLeft={false}
      overshootRight={false}
      leftThreshold={sizes.swipeAction / 2}
      rightThreshold={sizes.swipeAction / 2}
      onSwipeableOpen={handleOpen}
      renderLeftActions={() => (
        <View style={{ width: sizes.swipeAction, alignItems: "center", justifyContent: "center", backgroundColor: colors.success }}>
          <Icon name="check" size="md" color={colors.canvas} />
          <Text variant="label" color={colors.canvas}>
            {completeLabel}
          </Text>
        </View>
      )}
      renderRightActions={() =>
        onReschedule ? (
          <View style={{ width: sizes.swipeAction, alignItems: "center", justifyContent: "center", backgroundColor: colors.warning }}>
            <Icon name="sync" size="md" color={colors.canvas} />
            <Text variant="label" color={colors.canvas}>
              Tomorrow
            </Text>
          </View>
        ) : null
      }
    >
      {children}
    </ReanimatedSwipeable>
  );
}
