import { useState } from "react";
import { View } from "react-native";
import Animated, { LinearTransition } from "react-native-reanimated";
import { playHaptic } from "@/lib/haptics";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, motion, radii, space } from "@/theme/tokens";
import { Button } from "./Button";
import { Icon } from "./Icon";
import { Text } from "./Text";

export interface ActionField {
  label: string;
  value: string;
}

export interface ActionConfirmCardProps {
  // What the assistant wants to do, like "Create task".
  action: string;
  title: string;
  fields: ActionField[];
  onConfirm: () => void;
  onEdit: () => void;
  onCancel: () => void;
}

type Outcome = "pending" | "confirmed" | "cancelled";

// The assistant never acts on its own. It proposes, and nothing happens until Confirm.
export function ActionConfirmCard({ action, title, fields, onConfirm, onEdit, onCancel }: ActionConfirmCardProps) {
  const { colors } = useTheme();
  const [outcome, setOutcome] = useState<Outcome>("pending");

  const confirm = () => {
    playHaptic("confirm");
    setOutcome("confirmed");
    onConfirm();
  };

  const cancel = () => {
    setOutcome("cancelled");
    onCancel();
  };

  if (outcome !== "pending") {
    const isConfirmed = outcome === "confirmed";

    return (
      <Animated.View
        layout={LinearTransition.duration(motion.duration.base)}
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: space.md,
          padding: space.lg,
          borderRadius: radii.md,
          borderWidth: borders.hairline,
          borderColor: colors.border,
          backgroundColor: colors.surface,
        }}
      >
        {isConfirmed && <Icon name="check" size="md" color={colors.success} />}
        <Text variant="subhead" tone={isConfirmed ? "success" : "secondary"} style={{ flexShrink: 1 }}>
          {isConfirmed ? `${action} done · ${title}` : `${action} cancelled`}
        </Text>
      </Animated.View>
    );
  }

  return (
    <Animated.View
      layout={LinearTransition.duration(motion.duration.base)}
      style={{
        gap: space.lg,
        padding: space.lg,
        borderRadius: radii.md,
        borderWidth: borders.thin,
        borderColor: colors.borderControl,
        backgroundColor: colors.surface,
      }}
    >
      <View style={{ gap: space.xs }}>
        <Text variant="label" tone="secondary">
          {action}
        </Text>
        <Text variant="headline">{title}</Text>
      </View>

      <View style={{ gap: space.sm }}>
        {fields.map((field) => (
          <View key={field.label} style={{ flexDirection: "row", justifyContent: "space-between", gap: space.lg }}>
            <Text variant="callout" tone="secondary">
              {field.label}
            </Text>
            <Text variant="callout" style={{ flexShrink: 1, textAlign: "right" }}>
              {field.value}
            </Text>
          </View>
        ))}
      </View>

      <View style={{ gap: space.sm }}>
        <Button label="Edit" variant="secondary" onPress={onEdit} />
        <Button label="Confirm" onPress={confirm} />
        <Button label="Cancel" variant="ghost" onPress={cancel} />
      </View>
    </Animated.View>
  );
}
