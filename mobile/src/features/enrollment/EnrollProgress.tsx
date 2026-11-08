import { View } from "react-native";
import { Text } from "@/components/ui";
import { useTheme } from "@/theme/ThemeProvider";
import { radii, space } from "@/theme/tokens";

export interface EnrollProgressProps {
  // Which passage this is, counting from 1.
  step: number;
  total: number;
  title: string;
}

const RULE_HEIGHT = space.xs;

// "Passage 2 of 3" with a rule split into one segment per passage.
export function EnrollProgress({ step, total, title }: EnrollProgressProps) {
  const { colors } = useTheme();

  return (
    <View
      accessible
      accessibilityLabel={`Passage ${step} of ${total}, ${title}`}
      style={{ gap: space.sm }}
    >
      <Text variant="label" tone="secondary">
        Passage {step} of {total} · {title}
      </Text>

      <View style={{ flexDirection: "row", gap: space.xs }}>
        {Array.from({ length: total }, (_, index) => (
          <View
            key={index}
            style={{
              flex: 1,
              height: RULE_HEIGHT,
              borderRadius: radii.pill,
              backgroundColor: index < step ? colors.ink : colors.border,
            }}
          />
        ))}
      </View>
    </View>
  );
}
